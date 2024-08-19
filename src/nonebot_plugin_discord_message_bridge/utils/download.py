import httpx
import re

from ..config import *
from . import local as uLocal


async def get_discord_message_content(message_id, fwd, e=True, removereply=False):
    async with httpx.AsyncClient() as client:
        url = f"https://discord.com/api/v10/channels/{uLocal.get_discord_channel(fwd['discord-channel'])['channel-id']}/messages/{message_id}"
        headers = {"Authorization": f"Bot {uLocal.get_bot_token(uLocal.get_discord_channel(fwd['discord-channel'])['bot'])}"}
        response = await client.get(url, headers=headers)
        message = response.json()["content"]
        if removereply:
            if message.startswith("||") and message.endswith("||"):
                _message = message[2:-2]
            else:
                _message = message
            if _message.startswith(">"):
                _message = _message.split("\n")
                if re.search(
                    r"> https://discord.com/channels/\d+/\d+/\d+", _message[0]
                ):
                    if _message[1].startswith("> *") and _message[1].endswith("*"):
                        message = "\n".join(_message[2:])
        if len(message) > MAX_REPLY_PREVIEW_LENGTH and e:
            message = message[:MAX_REPLY_PREVIEW_LENGTH] + "..."
        return message


async def download_image(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.content
