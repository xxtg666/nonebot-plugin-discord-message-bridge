import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import nonebot


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

TEST_DATA = tempfile.TemporaryDirectory()
TEST_DATA_PATH = Path(TEST_DATA.name)
nonebot.init(
    dmb_http_proxy="",
    dmb_qq_bind_file=str(TEST_DATA_PATH / "bind.json"),
    dmb_forwards_config_file=str(TEST_DATA_PATH / "forwards.yaml"),
)

from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.exception import FinishedException

from nonebot_plugin_discord_message_bridge import global_vars as gv
from nonebot_plugin_discord_message_bridge import forward_qq_group_file_to_discord
from nonebot_plugin_discord_message_bridge.bots import discordbot
from nonebot_plugin_discord_message_bridge.config import qq_bind_file
from nonebot_plugin_discord_message_bridge.utils import local as uLocal
from nonebot_plugin_discord_message_bridge.utils import send as uSend


def tearDownModule():
    TEST_DATA.cleanup()


class FakeQQBot:
    def __init__(self):
        self.messages = []
        self.api_calls = []

    async def send_group_msg(self, **kwargs):
        self.messages.append(kwargs)
        return {"message_id": 1000 + len(self.messages)}

    async def call_api(self, api, **kwargs):
        self.api_calls.append((api, kwargs))
        return {}


class FakeAttachment:
    def __init__(
        self,
        filename="clip.mp4",
        url="https://cdn.discord.test/clip.mp4",
        content_type="video/mp4",
        size=1024,
    ):
        self.filename = filename
        self.url = url
        self.content_type = content_type
        self.size = size


class FakeDiscordMessage:
    def __init__(self, content, attachments, message_id=88):
        self.author = SimpleNamespace(name="discord-user")
        self.content = content
        self.attachments = attachments
        self.reference = None
        self.id = message_id


class LocalRenderingTests(unittest.TestCase):
    def setUp(self):
        with open(qq_bind_file, "w", encoding="utf-8") as file:
            json.dump({"42": "10001"}, file)

    def test_qq_message_only_inlines_images(self):
        message = Message(
            [
                MessageSegment.text("before"),
                MessageSegment.image("https://qq.test/image.png"),
                MessageSegment.text("middle"),
                MessageSegment("video", {"file": "https://qq.test/video.mp4"}),
                MessageSegment("file", {"file": "https://qq.test/archive.zip"}),
                MessageSegment.text("after"),
            ]
        )

        text, attachments = uLocal.render_message_for_discord(message)

        self.assertEqual(text, "before [图片] middleafter")
        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments[0]["type"], "image")

    def test_media_detection_checks_url_when_filename_has_no_extension(self):
        self.assertTrue(
            uLocal.is_video_file("opaque-id", "https://cdn.test/movie.MP4?token=1")
        )
        self.assertTrue(
            uLocal.is_image_file("opaque-id", "https://cdn.test/photo.WEBP?token=1")
        )

    def test_discord_text_is_structured_and_cq_code_stays_text(self):
        message = uLocal.render_discord_text_for_qq(
            "hello [CQ:at,qq=all] <@42> <@999>"
        )

        segment_types = [segment.type for segment in message]
        self.assertEqual(segment_types.count("at"), 1)
        self.assertTrue(all(segment_type in {"text", "at"} for segment_type in segment_types))
        self.assertIn("[CQ:at,qq=all]", message[0].data["text"])
        self.assertEqual(message[1].data["qq"], "10001")
        self.assertIn(
            "<@999>",
            "".join(
                segment.data["text"]
                for segment in message
                if segment.type == "text"
            ),
        )

class DiscordToQQTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        gv.message_id_records.clear()
        self.bot = FakeQQBot()
        gv.qq_bot = self.bot
        self.fwd = {"qq-group": 1, "discord-prefix": "[Discord] "}

    async def test_video_sends_text_first_then_local_video(self):
        attachment = FakeAttachment()
        message = FakeDiscordMessage(
            "caption [CQ:at,qq=all]",
            [attachment],
        )

        with patch.object(
            uSend,
            "download_file_to_cache",
            AsyncMock(return_value=r"C:\cache\clip.mp4"),
        ) as download:
            with patch.object(uSend, "remove_cached_file") as remove:
                message_id = await discordbot.forward_discord_message_to_qq(
                    message, self.fwd
                )

        self.assertEqual(message_id, 1001)
        self.assertEqual(len(self.bot.messages), 2)
        main_message = self.bot.messages[0]["message"]
        video_message = self.bot.messages[1]["message"]
        self.assertIsInstance(main_message, Message)
        self.assertIsInstance(video_message, Message)
        self.assertIn("caption [CQ:at,qq=all]", main_message.extract_plain_text())
        self.assertIn("[视频]", main_message.extract_plain_text())
        self.assertNotIn("video", [segment.type for segment in main_message])
        self.assertEqual([segment.type for segment in video_message], ["video"])
        self.assertEqual(video_message[0].data["file"], r"C:\cache\clip.mp4")
        download.assert_awaited_once_with(
            attachment.url,
            attachment.filename,
        )
        remove.assert_called_once_with(r"C:\cache\clip.mp4")
        self.assertEqual(gv.message_id_records, [("1001", "88")])

    async def test_video_failure_does_not_lose_main_text(self):
        attachment = FakeAttachment()
        message = FakeDiscordMessage("important caption", [attachment])

        with patch.object(
            uSend,
            "download_file_to_cache",
            AsyncMock(side_effect=RuntimeError("download failed")),
        ):
            await discordbot.forward_discord_message_to_qq(message, self.fwd)

        self.assertEqual(len(self.bot.messages), 2)
        self.assertIn(
            "important caption",
            self.bot.messages[0]["message"].extract_plain_text(),
        )
        self.assertIn(
            "[视频转发失败] clip.mp4",
            self.bot.messages[1]["message"].extract_plain_text(),
        )
        self.assertEqual(gv.message_id_records, [("1001", "88")])

    async def test_file_fallback_never_asks_qq_to_download_discord_url(self):
        bot = FakeQQBot()
        gv.qq_bot = bot
        discord_url = "https://cdn.discord.test/secret.bin"

        with patch.object(
            uSend,
            "download_file_to_cache",
            AsyncMock(side_effect=RuntimeError("unreachable")),
        ):
            sent = await discordbot._send_discord_attachment_to_qq(
                123456,
                FakeAttachment(
                    filename="secret.bin",
                    url=discord_url,
                    content_type="application/octet-stream",
                ),
                False,
            )

        self.assertFalse(sent)
        self.assertEqual(bot.api_calls, [])
        self.assertEqual(len(bot.messages), 1)
        fallback = bot.messages[0]["message"]
        self.assertIsInstance(fallback, Message)
        self.assertIn("[文件转发失败] secret.bin", fallback.extract_plain_text())
        self.assertNotIn(discord_url, fallback.extract_plain_text())

    async def test_deferred_attachments_keep_discord_order(self):
        attachments = [
            FakeAttachment(filename="one.mp4"),
            FakeAttachment(
                filename="archive.zip",
                content_type="application/zip",
                url="https://cdn.discord.test/archive.zip",
            ),
            FakeAttachment(filename="two.mp4"),
        ]
        message = FakeDiscordMessage("mixed", attachments)
        actions = []

        async def send_attachment(group_id, attachment, is_video):
            actions.append(("video" if is_video else "file", attachment.filename))
            return True

        with patch.object(
            discordbot,
            "_send_discord_attachment_to_qq",
            side_effect=send_attachment,
        ):
            await discordbot.forward_discord_message_to_qq(message, self.fwd)

        main_text = self.bot.messages[0]["message"].extract_plain_text()
        self.assertEqual(main_text.count("[视频]"), 2)
        self.assertIn("[文件: archive.zip]", main_text)
        self.assertEqual(
            actions,
            [
                ("video", "one.mp4"),
                ("file", "archive.zip"),
                ("video", "two.mp4"),
            ],
        )

class QQMetadataTests(unittest.IsolatedAsyncioTestCase):
    async def test_group_upload_prefers_existing_nickname(self):
        bot = SimpleNamespace(
            call_api=AsyncMock(
                return_value={"card": "group-card", "nickname": "nickname"}
            )
        )

        name = await uLocal.get_group_member_name(bot, 123456, 10001)

        self.assertEqual(name, "nickname")
        bot.call_api.assert_awaited_once_with(
            "get_group_member_info",
            group_id=123456,
            user_id=10001,
            no_cache=False,
        )

    async def test_group_upload_falls_back_to_qq_id(self):
        bot = SimpleNamespace(call_api=AsyncMock(side_effect=RuntimeError("failed")))

        name = await uLocal.get_group_member_name(bot, 123456, 10001)

        self.assertEqual(name, "10001")

    async def test_group_upload_forwards_video_with_member_name(self):
        event = SimpleNamespace(
            group_id=123456,
            user_id=10001,
            file=SimpleNamespace(
                id="file-id",
                busid=102,
                name="video.mp4",
                size=1024,
            ),
        )
        bot = SimpleNamespace(self_id=99999)

        async def call_api(api, **kwargs):
            if api == "get_group_file_url":
                return {"url": "https://qq-cdn.test/video.mp4"}
            if api == "get_group_member_info":
                return {"card": "group-card", "nickname": "nickname"}
            raise AssertionError(f"Unexpected API: {api}")

        bot.call_api = AsyncMock(side_effect=call_api)
        forwards = [{"discord-channel": 1}]
        webhook = AsyncMock(return_value="message-id")

        with patch.object(uLocal, "get_forwards", return_value=forwards):
            with patch.object(uSend, "webhook_send_message", webhook):
                await forward_qq_group_file_to_discord(bot, event)

        self.assertEqual(webhook.await_count, 1)
        for call in webhook.await_args_list:
            args = call.args
            self.assertEqual(args[0], "nickname [QQ]")
            self.assertEqual(args[2], " [视频] ")
            self.assertEqual(args[4][0]["type"], "video")
            self.assertEqual(args[4][0]["filename"], "video.mp4")

    async def test_group_upload_does_not_treat_finished_as_an_error(self):
        event = SimpleNamespace(
            group_id=123456,
            user_id=10001,
            file=SimpleNamespace(
                id="file-id",
                busid=102,
                name="video.mp4",
                size=1024,
            ),
        )

        async def call_api(api, **kwargs):
            if api == "get_group_file_url":
                return {"url": "https://qq-cdn.test/video.mp4"}
            return {"card": "group-card", "nickname": "nickname"}

        bot = SimpleNamespace(
            self_id=99999,
            call_api=AsyncMock(side_effect=call_api),
        )

        with patch.object(
            uLocal,
            "get_forwards",
            return_value=[{"discord-channel": 1}],
        ):
            with patch.object(
                uSend,
                "webhook_send_message",
                AsyncMock(side_effect=FinishedException()),
            ):
                with self.assertRaises(FinishedException):
                    await forward_qq_group_file_to_discord(bot, event)


class WebhookTests(unittest.IsolatedAsyncioTestCase):
    async def test_attachment_download_failure_keeps_text(self):
        posted_payloads = []

        def handler(request):
            if request.url.host == "qq-cdn.test":
                return httpx.Response(404, content=b"missing")
            posted_payloads.append(json.loads(request.content))
            return httpx.Response(200, json={"id": "discord-message-id"})

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        channel = {"webhook-url": "https://discord.test/api/webhooks/1/secret"}

        with patch.object(uSend.httpx, "AsyncClient", return_value=client):
            with patch.object(uLocal, "get_discord_channel", return_value=channel):
                await uSend.webhook_send_message(
                    "qq-user",
                    "https://avatar.test/user.png",
                    "important text",
                    {"discord-channel": 1},
                    [
                        {
                            "url": "https://qq-cdn.test/missing.mp4",
                            "filename": "missing.mp4",
                        }
                    ],
                )

        self.assertEqual(len(posted_payloads), 1)
        self.assertIn("important text", posted_payloads[0]["content"])
        self.assertIn("[附件下载失败]", posted_payloads[0]["content"])
