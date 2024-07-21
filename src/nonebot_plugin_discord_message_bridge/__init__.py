import nonebot
from nonebot import logger
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment
from nonebot.adapters.onebot.v11.message import Message
from nonebot.adapters.onebot.v11.event import GroupRecallNoticeEvent
from nonebot.params import CommandArg
from discord import app_commands
import threading
import traceback
import asyncio
import discord
import httpx
import copy
import json
import time
import os

from .config import *
from .utils import local as uLocal
from .utils import send as uSend
from .utils import download as uDownload

os.environ["HTTP_PROXY"] = HTTP_PROXY
os.environ["HTTPS_PROXY"] = HTTP_PROXY
already_start_discord_bot = False
discord_bot_started = False
intents = discord.Intents.default()
intents.message_content = True
bot_restart_time = 0
dcclient = discord.Client(intents=intents, proxy=HTTP_PROXY)
if not os.path.exists(qq_bind_file):
    json.dump({}, uLocal.safe_open(qq_bind_file, "w"))
temp_bind_qq = {}  # qq:rid
temp_bind_dis = {}  # rid:dis
temp_message_ids = []  # (qq:dc)
qq_commad_name = QQ_COMMAND_PREFIX + QQ_COMMAND

def get_otherside_message_id(_id, this):
    if this == "qq":
        for i in temp_message_ids:
            if i[0] == str(_id):
                return i[1]
    elif this == "dc":
        for i in temp_message_ids:
            if i[1] == str(_id):
                return i[0]
    return None


def add_temp_message_id(qq_id, dc_id):
    temp_message_ids.append((str(qq_id), str(dc_id)))
    if len(temp_message_ids) > 1000:
        temp_message_ids.pop(0)


def set_qq_bind(discord_id, qq_id):
    qq_bind = json.load(open(qq_bind_file, "r"))
    qq_bind[str(discord_id)] = str(qq_id)
    json.dump(qq_bind, open(qq_bind_file, "w"))


async def send_list_message(content_list):
    for i in content_list:
        if not i[1]:
            await uSend.send_message(i[0], CHANNEL_ID)
        else:
            await gbot.send_group_msg(group_id=QQ_ID, message=i[0])


def process_xdbot_command(discord_id, command):
    discord_id = str(discord_id)
    global temp_bind_qq, temp_bind_dis
    command = command.replace(DISCORD_COMMAND_PREFIX, "", 1)
    if command.startswith("bind"):
        try:
            qq_id = command.split(" ")[1]
            if qq_id in temp_bind_qq:
                if temp_bind_dis[temp_bind_qq[qq_id]] == discord_id:
                    return [
                        (
                            f"<@{discord_id}> 你已在请求绑定QQ号,请在QQ群内发送 `{qq_commad_name} bind {temp_bind_qq[qq_id]}` 进行绑定",
                            False,
                        ),
                        (
                            f"[CQ:at,qq={qq_id}] 请发送「{qq_commad_name} bind {temp_bind_qq[qq_id]}」绑定 Discord({discord_id}) 如果这不是你的操作, 请忽略本条消息",
                            True,
                        ),
                    ]
                else:
                    del temp_bind_qq[qq_id]
                    del temp_bind_dis[temp_bind_qq[qq_id]]
            rid = uLocal.genRandomID(24)
            temp_bind_qq[qq_id] = rid
            temp_bind_dis[rid] = discord_id
            return [
                (f"<@{discord_id}> 请在QQ群内发送 `{qq_commad_name} bind {rid}` 进行绑定", False),
                (
                    f"[CQ:at,qq={qq_id}] 请发送「{qq_commad_name} bind {rid}」绑定 Discord({discord_id}) 如果这不是你的操作, 请忽略本条消息",
                    True,
                ),
            ]
        except:
            if qq_id := uLocal.get_qq_bind(discord_id):
                return [(f"<@{discord_id}> 你已绑定QQ号 `{qq_id}`", False)]
            return [
                (
                    f"<@{discord_id}> 命令格式错误,应为: `{DISCORD_COMMAND_PREFIX}bind <uid>`",
                    False,
                )
            ]
    if not (qq_id := uLocal.get_qq_bind(discord_id)):
        return [
            (f"<@{discord_id}> 请先使用 `{DISCORD_COMMAND_PREFIX}bind <uid>` 绑定QQ号", False)
        ]
    if not QQ_SUDO_FORMAT:
        return [
            (
                f"<@{discord_id}> 您已绑定过QQ号 可以使用 `{DISCORD_COMMAND_PREFIX}bind <uid>` 修改绑定",
                False,
            )
        ]
    return [(f"{QQ_SUDO_FORMAT.format(Q=qq_id, C=command)}", True)]


def startDiscordBot():
    global bot_restart_time
    global dcclient
    time_1 = time.time()
    if bot_restart_time > 3:
        asyncio.run(
            gbot.send_group_msg(
                group_id=QQ_ID, message=PREFIX + "转发 Bot 短时间启动失败次数过多,已停止"
            )
        )
        return
    if bot_restart_time != 0:
        asyncio.run(
            gbot.send_group_msg(
                group_id=QQ_ID, message=PREFIX + f"转发 Bot 正在重启 ({bot_restart_time}次)"
            )
        )
    try:
        dcclient = discord.Client(intents=intents, proxy=HTTP_PROXY)

        @dcclient.event
        async def on_message(message):
            if message.author.id == dcclient.user.id or str(message.webhook_id) == str(
                WEBHOOK_ID
            ):
                return
            logger.debug(
                f"Received message from Discord: Message={message.content} UserID={message.author.id} ChannelID={message.channel.id} MessageID={message.id}"
                f" ReplyMessageID={message.reference.message_id if message.reference else None}"
            )
            if message.content.startswith(DISCORD_COMMAND_PREFIX):
                await send_list_message(
                    process_xdbot_command(message.author.id, message.content)
                )
                return
            ms = Message(
                uLocal.replace_ids_with_cq_at(
                    PREFIX + f"<{message.author.name}> {message.content}"
                )
            )
            if message.channel.id == CHANNEL_ID:
                try:
                    async with message.channel.typing():
                        if message.attachments:
                            for atta in message.attachments:
                                ms += MessageSegment.image(
                                    await uDownload.download_image(atta.url)
                                )
                        if message.reference:
                            if reply_to_qq_id := get_otherside_message_id(
                                message.reference.message_id, "dc"
                            ):
                                ms = MessageSegment.reply(int(reply_to_qq_id)) + ms
                        msg_id = (
                            await gbot.send_group_msg(group_id=QQ_ID, message=ms)
                        )["message_id"]
                        add_temp_message_id(msg_id, message.id)
                except:
                    await message.add_reaction(
                        discord.utils.get(message.guild.emojis, name=QQ_FORWARD_FAILED)
                    )
                    await message.reply("```" + traceback.format_exc() + "```")

        @dcclient.event
        async def on_message_edit(before, after):
            if before.author.id == dcclient.user.id or str(before.webhook_id) == str(
                WEBHOOK_ID
            ):
                return
            if before.channel.id == CHANNEL_ID:
                async with before.channel.typing():
                    if qq_id := get_otherside_message_id(before.id, "dc"):
                        ms = (
                            MessageSegment.reply(int(qq_id)) + "[编辑消息] " + after.content
                        )
                        msg_id = (
                            await gbot.send_group_msg(group_id=QQ_ID, message=ms)
                        )["message_id"]
                        add_temp_message_id(msg_id, before.id)

        @dcclient.event
        async def on_message_delete(message):
            if message.author.id == dcclient.user.id or str(message.webhook_id) == str(
                WEBHOOK_ID
            ):
                return
            if message.channel.id == CHANNEL_ID:
                async with message.channel.typing():
                    if qq_id := get_otherside_message_id(message.id, "dc"):
                        ms = MessageSegment.reply(int(qq_id)) + "[消息已被删除]"
                        msg_id = (
                            await gbot.send_group_msg(group_id=QQ_ID, message=ms)
                        )["message_id"]
                        add_temp_message_id(msg_id, message.id)

        dctree = app_commands.CommandTree(dcclient)

        @dctree.command(name="debug-dmb", description="Get temp_message_ids")
        async def debug_dmb(interaction):
            logger.info("Value of temp_message_ids: " + str(temp_message_ids))
            await interaction.response.send_message(f"Success")

        @dcclient.event
        async def on_ready():
            global discord_bot_started
            await dctree.sync(guild=discord.Object(id=GUILD_ID))
            discord_bot_started = True
            logger.success("Discord Bot started")

        dcclient.run(TOKEN)
    except:
        del dcclient
        time_2 = time.time()
        asyncio.run(
            gbot.send_group_msg(
                group_id=QQ_ID,
                message=PREFIX
                + f"转发 Bot 异常断开连接 (已运行{int(time_2-time_1)}秒)\n"
                + traceback.format_exc().split("\n")[-2],
            )
        )
        if time_2 - time_1 <= 90:
            bot_restart_time += 1
            startDiscordBot()
        else:
            bot_restart_time = 1
            startDiscordBot()


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
        if reply_to_dc_id := get_otherside_message_id(event.reply.message_id, "qq"):
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
        event.sender.nickname + " [QQ]", uLocal.get_avatar_url(uid), msg_nocq, images
    )
    add_temp_message_id(event.message_id, msgid)


@nonebot.on_notice().handle()
async def _(matcher: Matcher, bot: Bot, event: GroupRecallNoticeEvent):
    try:
        if event.group_id == QQ_ID:
            channel = CHANNEL_ID
        else:
            return
    except:
        return
    if dc_id := get_otherside_message_id(event.message_id, "qq"):
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
    global already_start_discord_bot
    if not already_start_discord_bot:
        global gbot
        gbot = bot
        already_start_discord_bot = True
        threading.Thread(target=startDiscordBot).start()
        logger.success("Discord Bot thread started")
        matcher.destroy()


@nonebot.on_command(QQ_COMMAND).handle()
async def _(
    matcher: Matcher, bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()
):
    global temp_bind_qq, temp_bind_dis, bot_restart_time, dcclient
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
        if token in temp_bind_dis and temp_bind_qq[event.get_user_id()] == token:
            set_qq_bind(temp_bind_dis[token], event.get_user_id())
            await uSend.send_message(
                f"<@{temp_bind_dis[token]}> QQ `{event.get_user_id()}` 绑定成功", channel
            )
            del temp_bind_qq[event.get_user_id()]
            del temp_bind_dis[token]
            await matcher.finish(f"Discord 绑定成功", at_sender=True)
        else:
            await matcher.finish("绑定 token 无效", at_sender=True)
    elif args[0] == "restart":
        if bot_restart_time >= 3:
            bot_restart_time = 0
            threading.Thread(target=startDiscordBot).start()
            await matcher.finish("正在尝试重启转发 Bot", at_sender=True)
        else:
            await matcher.finish("转发 Bot 正常运行中", at_sender=True)
    elif args[0] == "debug":
        logger.info("Value of temp_message_ids: " + str(temp_message_ids))
        await matcher.finish("Success", at_sender=True)
    await matcher.finish(
        BOT_NAME
        + " 命令帮助\n"
        + qq_commad_name
        + " bind <token> - 绑定 Discord 账户\n"
        + qq_commad_name
        + " restart - 手动重启转发 Bot (仅在自动重启失败后可用)\n"
        + qq_commad_name
        + " debug - 在日志中获取 temp_message_ids",
        at_sender=True,
    )
