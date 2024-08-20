from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.adapters.onebot.v11.message import Message
from nonebot import logger
from discord import app_commands
import traceback
import discord
import asyncio

from .. import global_vars as gv
from ..config import *
from ..utils import send as uSend
from ..utils import local as uLocal
from ..utils import download as uDownload


intents = discord.Intents.default()
intents.message_content = True


def process_bind_command(discord_id, command, fwd):
    discord_id = str(discord_id)
    command = command.replace(DISCORD_COMMAND_PREFIX, "", 1)
    if command.startswith("bind"):
        try:
            qq_id = command.split(" ")[1]
            if qq_id in gv.temp_bind_qq:
                if gv.temp_bind_discord[gv.temp_bind_qq[qq_id]] == discord_id:
                    return [
                        (
                            f"<@{discord_id}> 你已在请求绑定QQ号,请在QQ群({uLocal.get_qq_group_id(fwd['qq-group'])})内发送 `{QQ_COMMAND_NAME} bind {gv.temp_bind_qq[qq_id]}` 进行绑定",
                            False,
                        ),
                        (
                            f"[CQ:at,qq={qq_id}] 请发送「{QQ_COMMAND_NAME} bind {gv.temp_bind_qq[qq_id]}」绑定 Discord({discord_id}) 如果这不是你的操作, 请忽略本条消息",
                            True,
                        ),
                    ]
                else:
                    del gv.temp_bind_qq[qq_id]
                    del gv.temp_bind_discord[gv.temp_bind_qq[qq_id]]
            rid = uLocal.genRandomID(8)
            gv.temp_bind_qq[qq_id] = rid
            gv.temp_bind_discord[rid] = discord_id
            return [
                (
                    f"<@{discord_id}> 请在QQ群({uLocal.get_qq_group_id(fwd['qq-group'])})内发送 `{QQ_COMMAND_NAME} bind {rid}` 进行绑定",
                    False,
                ),
                (
                    f"[CQ:at,qq={qq_id}] 请发送「{QQ_COMMAND_NAME} bind {rid}」绑定 Discord({discord_id}) 如果这不是你的操作, 请忽略本条消息",
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
    return [
        (
            f"<@{discord_id}> 您已绑定过QQ号 可以使用 `{DISCORD_COMMAND_PREFIX}bind <uid>` 修改绑定",
            False,
        )
    ]


def startDiscordBot(bot_token, bot_id):
    try:
        discord_client = discord.Client(intents=intents, proxy=HTTP_PROXY)

        @discord_client.event
        async def on_message(message):
            for fwd in uLocal.get_forwards(message.channel.id, "discord-channels"):
                if message.author.id == discord_client.user.id or str(
                    message.webhook_id
                ) == str(uLocal.get_discord_channel(fwd["discord-channel"])["webhook-id"]):
                    return
                logger.debug(
                    f"Received message from Discord: Message={message.content} UserID={message.author.id} ChannelID={message.channel.id} MessageID={message.id}"
                    f" ReplyMessageID={message.reference.message_id if message.reference else None}"
                )
                if message.content.startswith(DISCORD_COMMAND_PREFIX) and not fwd["silent"]:
                    await uSend.send_list_message(
                        process_bind_command(message.author.id, message.content, fwd), fwd
                    )
                    return
                ms = Message(
                    uLocal.replace_ids_with_cq_at(
                        fwd["discord-prefix"] + f"<{message.author.name}> {message.content}"
                    )
                )
                try:
                    async with (message.channel.typing() if not fwd["silent"] else uLocal.NoneAsyncWith()):
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
                            await gv.qq_bot.send_group_msg(group_id=uLocal.get_qq_group_id(fwd['qq-group']), message=ms)
                        )["message_id"]
                        uLocal.record_message_id(msg_id, message.id)
                except:
                    if not fwd["silent"] and not NO_TRACEBACK:
                        await message.add_reaction(QQ_FORWARD_FAILED)
                        await message.reply("```" + traceback.format_exc() + "```")
                await asyncio.sleep(QQ_SEND_INTERVAL)

        @discord_client.event
        async def on_message_edit(before, after):
            for fwd in uLocal.get_forwards(before.channel.id, "discord-channels"):
                if before.content == after.content:
                    return
                if before.author.id == discord_client.user.id or str(
                    before.webhook_id
                ) == str(uLocal.get_discord_channel(fwd["discord-channel"])["webhook-id"]):
                    return
                async with (before.channel.typing() if not fwd["silent"] else uLocal.NoneAsyncWith()):
                    if qq_id := uLocal.get_another_message_id(before.id, "dc"):
                        ms = (
                            MessageSegment.reply(int(qq_id))
                            + EDIT_PLACEHOLDER
                            + after.content
                        )
                        msg_id = (
                            await gv.qq_bot.send_group_msg(group_id=uLocal.get_qq_group_id(fwd['qq-group']), message=ms)
                        )["message_id"]
                        uLocal.record_message_id(msg_id, before.id)
                await asyncio.sleep(QQ_SEND_INTERVAL)

        @discord_client.event
        async def on_message_delete(message):
            for fwd in uLocal.get_forwards(message.channel.id, "discord-channels"):
                if message.author.id == discord_client.user.id or str(
                    message.webhook_id
                ) == str(uLocal.get_discord_channel(fwd["discord-channel"])["webhook-id"]):
                    return
                async with (message.channel.typing() if not fwd["silent"] else uLocal.NoneAsyncWith()):
                    if qq_id := uLocal.get_another_message_id(message.id, "dc"):
                        ms = MessageSegment.reply(int(qq_id)) + DELETE_PLACEHOLDER
                        msg_id = (
                            await gv.qq_bot.send_group_msg(group_id=uLocal.get_qq_group_id(fwd['qq-group']), message=ms)
                        )["message_id"]
                        uLocal.record_message_id(msg_id, message.id)
                await asyncio.sleep(QQ_SEND_INTERVAL)

        discord_tree = app_commands.CommandTree(discord_client)

        @discord_tree.command(name="debug-dmb", description="Log message_id_records & loaded_forward_config")
        async def debug_dmb(interaction):
            logger.info("Value of message_id_records: " + str(gv.message_id_records))
            logger.info("Value of loaded_forward_config: " + str(gv.loaded_forward_config))
            await interaction.response.send_message(f"Success")

        @discord_client.event
        async def on_ready():
            await discord_tree.sync()
            logger.success(f"Discord Bot {bot_id} started")

        discord_client.run(bot_token)
    except:
        logger.error(traceback.format_exc())
