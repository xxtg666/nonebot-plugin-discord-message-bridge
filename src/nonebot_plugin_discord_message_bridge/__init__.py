import nonebot
from nonebot import logger
from nonebot.exception import FinishedException
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.adapters.onebot.v11.event import GroupRecallNoticeEvent, GroupUploadNoticeEvent
import threading
import httpx
import copy
import json
import os

from . import global_vars as gv
from .config import *
from .utils import forward as uForward
from .utils import local as uLocal
from .utils import send as uSend
from .utils import download as uDownload
from .utils import yamlloader as uYaml
from .bots import discordbot as bDiscord


os.environ["HTTP_PROXY"] = HTTP_PROXY
os.environ["HTTPS_PROXY"] = HTTP_PROXY
if not os.path.exists(qq_bind_file):
    with uLocal.safe_open(qq_bind_file, "w", encoding="utf-8") as file:
        json.dump({}, file)
if not os.path.exists(forwards_config_file):
    uYaml.dump(uYaml.default_config_data, forwards_config_file)
    logger.warning(f"转发配置文件已生成于 ( {os.path.abspath(forwards_config_file)} ) , 请配置后重启插件.")
    logger.warning("参考配置文件: https://github.com/xxtg666/nonebot-plugin-discord-message-bridge/blob/main/docs/dmb-config-example.yaml")
gv.forward_config = uYaml.load(forwards_config_file)
uLocal.load_forward_config()

if FORWARD_MSG_SERVER:
    enable_forward_msg_parse = True
else:
    enable_forward_msg_parse = False
    logger.warning(
        "未配置转发消息上传服务器, 将无法解析转发消息, 请在配置文件中设置 `dmb_forward_msg_server`"
    )


def set_qq_bind(discord_id, qq_id):
    with open(qq_bind_file, "r", encoding="utf-8") as file:
        qq_bind = json.load(file)
    qq_bind[str(discord_id)] = str(qq_id)
    with open(qq_bind_file, "w", encoding="utf-8") as file:
        json.dump(qq_bind, file)


@nonebot.on_message().handle()
async def _(matcher: Matcher, bot: Bot, event: GroupMessageEvent):
    try:
        group_id = event.group_id
    except Exception:
        return
    for fwd in uLocal.get_forwards(event.group_id, "qq-groups"):
        message_types = [segment.type for segment in event.get_message()]
        logger.debug(
            f"Received message from QQ: PlainText={event.get_plaintext()} SegmentTypes={message_types} UserID={event.get_user_id()} GroupID={event.group_id} MessageID={event.message_id} "
            f"ReplyMessageID={event.reply.message_id if event.reply else None} SenderNickname={event.sender.nickname}"
        )
        if event.get_plaintext().startswith(QQ_COMMAND_PREFIX + QQ_COMMAND_NAME) and not fwd["silent"]:
            args = event.get_plaintext().strip().split(" ")[1:]
            if args:
                if args[0] == "bind":
                    try:
                        token = args[1]
                    except IndexError:
                        if dis_id := uLocal.get_qq_bind_discord(event.get_user_id()):
                            await matcher.finish(f"你已绑定 Discord({dis_id})", at_sender=True)
                        await matcher.finish(
                            f"你还未绑定 Discord, 请到消息转发频道下发送「{DISCORD_COMMAND_PREFIX}bind <uid>」进行绑定",
                            at_sender=True,
                        )
                    if (
                            token in gv.temp_bind_discord
                            and gv.temp_bind_qq[event.get_user_id()] == token
                    ):
                        set_qq_bind(gv.temp_bind_discord[token], event.get_user_id())
                        await uSend.send_message(
                            f"<@{gv.temp_bind_discord[token]}> QQ `{event.get_user_id()}` 绑定成功",
                            fwd
                        )
                        del gv.temp_bind_qq[event.get_user_id()]
                        del gv.temp_bind_discord[token]
                        await matcher.finish(f"Discord 绑定成功", at_sender=True)
                    else:
                        await matcher.finish("绑定 token 无效", at_sender=True)
                elif args[0] == "debug":
                    logger.info("Value of message_id_records: " + str(gv.message_id_records))
                    await matcher.finish("Success", at_sender=True)
                elif args[0] == "preview":
                    if event.reply:
                        reply = str(event.reply.message)
                        if reply.startswith("[CQ:forward") and enable_forward_msg_parse:
                            forward_msg_id = reply[15:-1].replace(",content=&", "")
                            chat_uuid = await uForward.get_forward_mapping(forward_msg_id)
                            await matcher.finish(uForward.get_preview_url(chat_uuid))

            await matcher.finish(
                BOT_NAME
                + " 命令帮助\n"
                + QQ_COMMAND_PREFIX + QQ_COMMAND_NAME
                + " bind <token> - 绑定 Discord 账户\n"
                + QQ_COMMAND_PREFIX + QQ_COMMAND_NAME
                + " debug - 在日志中获取 message_id_records",
                + QQ_COMMAND_PREFIX + QQ_COMMAND_NAME
                + " preview - 获取转发消息预览（回复转发消息时使用）",
                at_sender=True,
            )
        uid = event.get_user_id()
        message = event.get_message()
        origin_message = str(message)
        if origin_message.startswith("[CQ:forward") and enable_forward_msg_parse:
            forward_msg_id = origin_message[15:-1]
            forward_data = await uForward.get_forward_msg(forward_msg_id)
            chat_uuid = await uForward.upload_forward_msg(forward_data, forward_msg_id)
            preview_url = uForward.get_preview_url(chat_uuid)
            origin_message = f"[{FORWARD_MSG_PLACEHOLDER}]({preview_url})"
        else:
            origin_message = uLocal.process_text(origin_message)
        msg, attachments = uLocal.render_message_for_discord(message)
        if origin_message.startswith(f"[{FORWARD_MSG_PLACEHOLDER}]("):
            msg = origin_message
            attachments = []
        if msg.startswith(DISCORD_COMMAND_PREFIX * 4):
            await uSend.send_message(msg[2:], fwd)
            return
        msg_nocq = copy.deepcopy(msg)
        if event.reply:
            if reply_to_dc_id := uLocal.get_another_message_id(
                event.reply.message_id, "qq"
            ):
                msg_content = (
                    (
                        await uDownload.get_discord_message_content(
                            reply_to_dc_id, fwd, removereply=True
                        )
                    )
                    .strip()
                    .replace("\n", " ")
                )
                msg_nocq = (
                    f"> {uLocal.generate_message_link(reply_to_dc_id, fwd)}\n> *{msg_content}*\n"
                    + msg_nocq
                )
        if not msg_nocq.strip() and not attachments:
            return
        sender_name = uLocal.get_qq_sender_name(event.sender, uid)
        msg_id = await uSend.webhook_send_message(
            sender_name + SUFFIX,
            uLocal.get_qq_avatar_url(uid),
            msg_nocq,
            fwd,
            attachments,
        )
        uLocal.record_message_id(event.message_id, msg_id)


@nonebot.on_notice().handle()
async def _(matcher: Matcher, bot: Bot, event: GroupRecallNoticeEvent):
    try:
        group_id = event.group_id
    except Exception:
        return
    for fwd in uLocal.get_forwards(event.group_id, "qq-groups"):
        if dc_id := uLocal.get_another_message_id(event.message_id, "qq"):
            async with httpx.AsyncClient() as client:
                await client.patch(
                    url=uLocal.get_discord_channel(fwd["discord-channel"])["webhook-url"] + "/messages/" + dc_id,
                    headers={"Content-Type": "application/json"},
                    json={
                        "content": "||"
                        + (await uDownload.get_discord_message_content(dc_id, fwd, e=False))
                        + "||"
                    },
                )


async def forward_qq_group_file_to_discord(bot: Bot, event: GroupUploadNoticeEvent):
    try:
        group_id = event.group_id
    except Exception:
        return
    file_info = event.file
    filename = file_info.name
    if str(event.user_id) == str(getattr(bot, "self_id", "")):
        logger.debug(f"Skip bridged QQ group file upload: GroupID={group_id} File={filename}")
        return

    forwards = uLocal.get_forwards(group_id, "qq-groups")
    if not forwards:
        return

    file_url = None
    try:
        result = await bot.call_api(
            "get_group_file_url",
            group_id=group_id,
            file_id=file_info.id,
            busid=file_info.busid,
        )
        file_url = result["url"]
    except FinishedException:
        raise
    except Exception:
        logger.exception(f"Failed to get QQ group file url: {filename}")

    sender_name = await uLocal.get_group_member_name(
        bot,
        group_id,
        event.user_id,
    )
    is_video = uLocal.is_video_file(filename, file_url)
    if file_url:
        content = VIDEO_PLACEHOLDER if is_video else f" [文件: {filename}] "
        attachments = [
            {
                "type": "video" if is_video else "file",
                "url": file_url,
                "filename": filename,
                "placeholder": "",
                "size": file_info.size,
                "is_video": is_video,
            }
        ]
    else:
        media_type = "视频" if is_video else "文件"
        content = f" [{media_type}转发失败: {filename}] "
        attachments = []
    for fwd in forwards:
        try:
            await uSend.webhook_send_message(
                sender_name + SUFFIX,
                uLocal.get_qq_avatar_url(event.user_id),
                content,
                fwd,
                attachments,
            )
        except FinishedException:
            raise
        except Exception:
            logger.exception(
                f"Failed to forward QQ group file to Discord: GroupID={group_id} File={filename}"
            )


@nonebot.on_notice().handle()
async def _(matcher: Matcher, bot: Bot, event: GroupUploadNoticeEvent):
    await forward_qq_group_file_to_discord(bot, event)


@nonebot.on_message().handle()
async def _(matcher: Matcher, bot: Bot):
    if not gv.already_started_discord_bot:
        gv.qq_bot = bot
        gv.already_started_discord_bot = True
        for bot_id, bot_token in gv.forward_config["discord-bots"].items():
            gv.discord_bot_threads.append(threading.Thread(target=bDiscord.startDiscordBot, args=(bot_token, bot_id)))
            gv.discord_bot_threads[-1].start()
            logger.success(f"Discord Bot {bot_id} thread started")
        matcher.destroy()
