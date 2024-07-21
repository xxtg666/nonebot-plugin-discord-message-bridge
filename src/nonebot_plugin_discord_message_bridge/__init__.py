import nonebot
from nonebot import logger
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.adapters.onebot.v11.message import Message
from nonebot.adapters.onebot.v11.event import GroupRecallNoticeEvent
from nonebot.params import CommandArg
import threading
import httpx
import copy
import json
import os

from .config import *
from .utils import local as uLocal
from .utils import send as uSend
from .utils import download as uDownload
from .bots import discordbot as bDiscord
import global_vars as gv

os.environ["HTTP_PROXY"] = HTTP_PROXY
os.environ["HTTPS_PROXY"] = HTTP_PROXY
if not os.path.exists(qq_bind_file):
    json.dump({}, uLocal.safe_open(qq_bind_file, "w"))


def set_qq_bind(discord_id, qq_id):
    qq_bind = json.load(open(qq_bind_file, "r"))
    qq_bind[str(discord_id)] = str(qq_id)
    json.dump(qq_bind, open(qq_bind_file, "w"))


@nonebot.on_message().handle()
async def _(matcher: Matcher, bot: Bot, event: GroupMessageEvent):
    try:
        if event.group_id == QQ_ID:
            channel = CHANNEL_ID
        else:
            return
    except:
        return
    logger.debug(
        f"Received message from QQ: Message={str(event.get_message())} UserID={event.get_user_id()} GroupID={event.group_id} MessageID={event.message_id} "
        f"ReplyMessageID={event.reply.message_id if event.reply else None} SenderNickname={event.sender.nickname}"
    )
    msg = uLocal.replace_cq_at_with_ids(uLocal.process_text(str(event.get_message())))
    if msg.startswith(DISCORD_COMMAND_PREFIX * 2):
        await uSend.send_message(msg[2:], channel)
        return
    uid = event.get_user_id()
    msg_nocq = copy.deepcopy(msg)
    images = uLocal.get_url(msg)
    for i in uLocal.get_cq_images(msg):
        msg_nocq = msg_nocq.replace(i, " [图片] ")
    if event.reply:
        if reply_to_dc_id := uLocal.get_another_message_id(
            event.reply.message_id, "qq"
        ):
            msg_content = (
                (
                    await uDownload.get_discord_message_content(
                        reply_to_dc_id, removereply=True
                    )
                )
                .strip()
                .replace("\n", " ")
            )
            msg_nocq = (
                f"> {uLocal.generate_message_link(reply_to_dc_id)}\n> *{msg_content}*\n"
                + msg_nocq
            )
    msgid = await uSend.webhook_send_message(
        event.sender.nickname + " [QQ]", uLocal.get_qq_avatar_url(uid), msg_nocq, images
    )
    uLocal.record_message_id(event.message_id, msgid)


@nonebot.on_notice().handle()
async def _(matcher: Matcher, bot: Bot, event: GroupRecallNoticeEvent):
    try:
        if event.group_id != QQ_ID:
            return
    except:
        return
    if dc_id := uLocal.get_another_message_id(event.message_id, "qq"):
        async with httpx.AsyncClient() as client:
            await client.patch(
                url=WEBHOOK_URL + "/messages/" + dc_id,
                headers={"Content-Type": "application/json"},
                json={
                    "content": "||"
                    + (await uDownload.get_discord_message_content(dc_id, False))
                    + "||"
                },
            )


@nonebot.on_message().handle()
async def _(matcher: Matcher, bot: Bot):
    if not gv.already_started_discord_bot:
        gv.qq_bot = bot
        gv.already_started_discord_bot = True
        gv.discord_bot_thread = threading.Thread(target=bDiscord.startDiscordBot)
        gv.discord_bot_thread.start()
        logger.success("Discord Bot thread started")
        matcher.destroy()


@nonebot.on_command(QQ_COMMAND).handle()
async def _(
    matcher: Matcher, bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()
):
    try:
        if event.group_id == QQ_ID:
            channel = CHANNEL_ID
        else:
            return
    except:
        return
    args = args.extract_plain_text().strip().split(" ")
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
                channel,
            )
            del gv.temp_bind_qq[event.get_user_id()]
            del gv.temp_bind_discord[token]
            await matcher.finish(f"Discord 绑定成功", at_sender=True)
        else:
            await matcher.finish("绑定 token 无效", at_sender=True)
    elif args[0] == "restart":
        gv.discord_bot_thread = None
        gv.discord_bot_thread = threading.Thread(target=bDiscord.startDiscordBot)
        gv.discord_bot_thread.start()
        await matcher.finish("正在尝试重启转发 Bot", at_sender=True)
    elif args[0] == "debug":
        logger.info("Value of message_id_records: " + str(gv.message_id_records))
        await matcher.finish("Success", at_sender=True)
    await matcher.finish(
        BOT_NAME
        + " 命令帮助\n"
        + gv.qq_command_name
        + " bind <token> - 绑定 Discord 账户\n"
        + gv.qq_command_name
        + " restart - 手动重启转发 Bot\n"
        + gv.qq_command_name
        + " debug - 在日志中获取 message_id_records",
        at_sender=True,
    )
