from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.adapters.onebot.v11.message import Message
from nonebot import logger
from discord import app_commands
import traceback
import asyncio
import discord
import time

from .. import global_vars as gv
from ..config import *
from ..utils import send as uSend
from ..utils import local as uLocal
from ..utils import download as uDownload


intents = discord.Intents.default()
intents.message_content = True


def process_bind_command(discord_id, command):
    discord_id = str(discord_id)
    command = command.replace(DISCORD_COMMAND_PREFIX, "", 1)
    if command.startswith("bind"):
        try:
            qq_id = command.split(" ")[1]
            if qq_id in gv.temp_bind_qq:
                if gv.temp_bind_discord[gv.temp_bind_qq[qq_id]] == discord_id:
                    return [
                        (
                            f"<@{discord_id}> 你已在请求绑定QQ号,请在QQ群内发送 `{gv.qq_command_name} bind {gv.temp_bind_qq[qq_id]}` 进行绑定",
                            False,
                        ),
                        (
                            f"[CQ:at,qq={qq_id}] 请发送「{gv.qq_command_name} bind {gv.temp_bind_qq[qq_id]}」绑定 Discord({discord_id}) 如果这不是你的操作, 请忽略本条消息",
                            True,
                        ),
                    ]
                else:
                    del gv.temp_bind_qq[qq_id]
                    del gv.temp_bind_discord[gv.temp_bind_qq[qq_id]]
            rid = uLocal.genRandomID(16)
            gv.temp_bind_qq[qq_id] = rid
            gv.temp_bind_discord[rid] = discord_id
            return [
                (
                    f"<@{discord_id}> 请在QQ群内发送 `{gv.qq_command_name} bind {rid}` 进行绑定",
                    False,
                ),
                (
                    f"[CQ:at,qq={qq_id}] 请发送「{gv.qq_command_name} bind {rid}」绑定 Discord({discord_id}) 如果这不是你的操作, 请忽略本条消息",
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
            (
                f"<@{discord_id}> 请先使用 `{DISCORD_COMMAND_PREFIX}bind <uid>` 绑定QQ号",
                False,
            )
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
    time_1 = time.time()
    if gv.bot_restart_times > 3:
        asyncio.run(
            gv.qq_bot.send_group_msg(
                group_id=QQ_ID,
                message=PREFIX + "转发 Bot 短时间启动失败次数过多,已停止",
            )
        )
        return
    if gv.bot_restart_times != 0:
        asyncio.run(
            gv.qq_bot.send_group_msg(
                group_id=QQ_ID,
                message=PREFIX + f"转发 Bot 正在重启 ({gv.bot_restart_times}次)",
            )
        )
    try:
        discord_client = discord.Client(intents=intents, proxy=HTTP_PROXY)

        @discord_client.event
        async def on_message(message):
            if message.author.id == discord_client.user.id or str(
                message.webhook_id
            ) == str(WEBHOOK_ID):
                return
            logger.debug(
                f"Received message from Discord: Message={message.content} UserID={message.author.id} ChannelID={message.channel.id} MessageID={message.id}"
                f" ReplyMessageID={message.reference.message_id if message.reference else None}"
            )
            if message.content.startswith(DISCORD_COMMAND_PREFIX):
                await uSend.send_list_message(
                    process_bind_command(message.author.id, message.content)
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
                            if reply_to_qq_id := uLocal.get_another_message_id(
                                message.reference.message_id, "dc"
                            ):
                                ms = MessageSegment.reply(int(reply_to_qq_id)) + ms
                        msg_id = (
                            await gv.qq_bot.send_group_msg(group_id=QQ_ID, message=ms)
                        )["message_id"]
                        uLocal.record_message_id(msg_id, message.id)
                except:
                    await message.add_reaction(
                        discord.utils.get(message.guild.emojis, name=QQ_FORWARD_FAILED)
                    )
                    await message.reply("```" + traceback.format_exc() + "```")

        @discord_client.event
        async def on_message_edit(before, after):
            if before.author.id == discord_client.user.id or str(
                before.webhook_id
            ) == str(WEBHOOK_ID):
                return
            if before.channel.id == CHANNEL_ID:
                async with before.channel.typing():
                    if qq_id := uLocal.get_another_message_id(before.id, "dc"):
                        ms = (
                            MessageSegment.reply(int(qq_id))
                            + "[编辑消息] "
                            + after.content
                        )
                        msg_id = (
                            await gv.qq_bot.send_group_msg(group_id=QQ_ID, message=ms)
                        )["message_id"]
                        uLocal.record_message_id(msg_id, before.id)

        @discord_client.event
        async def on_message_delete(message):
            if message.author.id == discord_client.user.id or str(
                message.webhook_id
            ) == str(WEBHOOK_ID):
                return
            if message.channel.id == CHANNEL_ID:
                async with message.channel.typing():
                    if qq_id := uLocal.get_another_message_id(message.id, "dc"):
                        ms = MessageSegment.reply(int(qq_id)) + "[消息已被删除]"
                        msg_id = (
                            await gv.qq_bot.send_group_msg(group_id=QQ_ID, message=ms)
                        )["message_id"]
                        uLocal.record_message_id(msg_id, message.id)

        dctree = app_commands.CommandTree(discord_client)

        @dctree.command(name="debug-dmb", description="Get message_id_records")
        async def debug_dmb(interaction):
            logger.info("Value of message_id_records: " + str(gv.message_id_records))
            await interaction.response.send_message(f"Success")

        @discord_client.event
        async def on_ready():
            global discord_bot_started
            await dctree.sync(guild=discord.Object(id=GUILD_ID))
            discord_bot_started = True
            logger.success("Discord Bot started")

        discord_client.run(TOKEN)
    except:
        del discord_client
        time_2 = time.time()
        asyncio.run(
            gv.qq_bot.send_group_msg(
                group_id=QQ_ID,
                message=PREFIX
                + f"转发 Bot 异常断开连接 (已运行{int(time_2-time_1)}秒)\n"
                + traceback.format_exc().split("\n")[-2],
            )
        )
        if time_2 - time_1 <= 90:
            gv.bot_restart_times += 1
            startDiscordBot()
        else:
            gv.bot_restart_times = 1
            startDiscordBot()
