import nonebot
from nonebot import logger
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.adapters.onebot.v11.event import GroupRecallNoticeEvent
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
    json.dump({}, uLocal.safe_open(qq_bind_file, "w"))
if not os.path.exists(forwards_config_file):
    uYaml.dump(uYaml.default_config_data, forwards_config_file)
    logger.warning(f"转发配置文件已生成于 ( {os.path.abspath(forwards_config_file)} ) , 请配置后重启插件.")
    logger.warning("参考配置文件: https://github.com/xxtg666/nonebot-plugin-discord-message-bridge/blob/main/docs/dmb-config-example.yaml")
gv.forward_config = uYaml.load(forwards_config_file)
uLocal.load_forward_config()

if FORWARD_MSG_GET_URL and FORWARD_MSG_GET_TOKEN and FORWARD_MSG_UPLOAD_SERVER and FORWARD_MSG_PREVIEW_URL:
    enable_forward_msg_parse = True
else:
    enable_forward_msg_parse = False
    logger.warning(
        "未配置转发消息获取地址与上传服务器, 将无法解析转发消息, 请在配置文件中设置 `dmb_forward_msg_get_url`, `dmb_forward_msg_get_token`, `dmb_forward_msg_upload_server` 和 `dmb_forward_msg_preview_url`"
    )


def set_qq_bind(discord_id, qq_id):
    qq_bind = json.load(open(qq_bind_file, "r"))
    qq_bind[str(discord_id)] = str(qq_id)
    json.dump(qq_bind, open(qq_bind_file, "w"))


@nonebot.on_message().handle()
async def _(matcher: Matcher, bot: Bot, event: GroupMessageEvent):
    try:
        group_id = event.group_id
    except Exception:
        return
    for fwd in uLocal.get_forwards(event.group_id, "qq-groups"):
        logger.debug(
            f"Received message from QQ: Message={str(event.get_message())} UserID={event.get_user_id()} GroupID={event.group_id} MessageID={event.message_id} "
            f"ReplyMessageID={event.reply.message_id if event.reply else None} SenderNickname={event.sender.nickname}"
        )
        if event.get_plaintext().startswith(QQ_COMMAND_NAME) and not fwd["silent"]:
            args = event.get_plaintext().strip().split(" ")[1:]
            if args:
                if args[0] == "bind":
                    try:
                        token = args[1]
                    except:
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
            await matcher.finish(
                BOT_NAME
                + " 命令帮助\n"
                + QQ_COMMAND_NAME
                + " bind <token> - 绑定 Discord 账户\n"
                + QQ_COMMAND_NAME
                + " debug - 在日志中获取 message_id_records",
                at_sender=True,
            )
        uid = event.get_user_id()
        message = event.get_message()
        origin_message = str(message)
        if origin_message.startswith("[CQ:forward") and enable_forward_msg_parse:
            forward_msg_id = origin_message[15:-1]
            forward_data = await uForward.get_forward_msg(forward_msg_id)
            chat_uuid = await uForward.upload_forward_msg(forward_data)
            preview_url = uForward.get_preview_url(chat_uuid)
            origin_message = f"[{FORWARD_MSG_PLACEHOLDER}]({preview_url})"
        else:
            origin_message = uLocal.process_text(origin_message)
        msg = uLocal.replace_cq_at_with_ids(origin_message)
        if msg.startswith(DISCORD_COMMAND_PREFIX * 2):
            await uSend.send_message(msg[2:], fwd)
            return
        msg_nocq = copy.deepcopy(msg)
        images = uLocal.get_url(msg)
        for i in uLocal.get_cq_images(msg):
            msg_nocq = msg_nocq.replace(i, IMAGE_PLACEHOLDER)
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
        msg_id = await uSend.webhook_send_message(
            event.sender.nickname + SUFFIX, uLocal.get_qq_avatar_url(uid), msg_nocq, fwd, images
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
