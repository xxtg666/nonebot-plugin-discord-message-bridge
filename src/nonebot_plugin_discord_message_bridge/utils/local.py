import random
import json
import html
import re
import os

from ..config import *
from .. import global_vars as gv


def generate_message_link(discord_message_id, fwd):
    return f"https://discord.com/channels/{fwd.GUILD_ID}/{fwd.CHANNEL_ID}/{discord_message_id}"


def get_qq_bind(discord_id):
    return json.load(open(qq_bind_file, "r")).get(str(discord_id), False)


def get_qq_bind_discord(qq_id):
    return {qq: dis for dis, qq in json.load(open(qq_bind_file, "r")).items()}.get(
        str(qq_id), False
    )


def genRandomID(k: int = 8) -> str:
    return "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=k))


def get_qq_avatar_url(qq_user_id):
    return "http://q1.qlogo.cn/g?b=qq&nk=" + str(qq_user_id) + "&s=640"


def process_text(text: str):
    return html.unescape(text)


def get_url(string):
    url = re.findall(r"url=([^),]+)", string)
    return url


def get_cq_images(string):
    cq_images = re.findall(r"\[CQ:image.*?\]", string) + re.findall(
        r"\[CQ:mface.*?\]", string
    )
    return cq_images


def replace_cq_at_with_ids(msg):
    pattern = r"\[CQ:at,qq=(\d+)\]"
    ids = {qq: dis for dis, qq in json.load(open(qq_bind_file, "r")).items()}

    def replace_id(match):
        id_str = match.group(1)
        if id_str in ids:
            return f"<@{ids[id_str]}>"
        else:
            return match.group(0)

    replaced_msg = re.sub(pattern, replace_id, msg)
    return replaced_msg


def replace_ids_with_cq_at(msg):
    pattern = r"<@(\d+)>"
    ids = json.load(open(qq_bind_file, "r"))

    def replace_id(match):
        id_to_replace = match.group(1)
        return f"[CQ:at,qq={ids.get(id_to_replace, id_to_replace)}]"

    replaced_msg = re.sub(pattern, replace_id, msg)
    return replaced_msg


def safe_open(file_path, mode, *args, **kwargs):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    return open(file_path, mode, *args, **kwargs)


def get_another_message_id(_id, this):
    if this == "qq":
        for i in gv.message_id_records:
            if i[0] == str(_id):
                return i[1]
    elif this == "dc":
        for i in gv.message_id_records:
            if i[1] == str(_id):
                return i[0]
    return None


def record_message_id(qq_id, dc_id):
    gv.message_id_records.append((str(qq_id), str(dc_id)))
    if len(gv.message_id_records) > MAX_MESSAGE_ID_RECORD:
        gv.message_id_records.pop(0)


class ForwardConfig:
    def __init__(self, forward_id):
        self.forward = None
        for forward in gv.forward_config["forwards"]:
            if (forward["channel-id"] == forward_id) or (forward["qq-group-id"] == forward_id):
                self.forward: dict = forward
                break
        if not self.forward:
            return
        self.BOT_ID = self.forward.get("bot-id", None)
        self.TOKEN = gv.forward_config["bots"][self.BOT_ID]
        self.GUILD_ID = self.forward.get("guild-id", None)
        self.CHANNEL_ID = self.forward.get("channel-id", None)
        self.WEBHOOK_URL = self.forward.get("webhook-url", None)
        self.WEBHOOK_ID = self.forward.get("webhook-id", None)
        self.QQ_GROUP_ID = self.forward.get("qq-group-id", None)
        self.QQ_FORWARD_FAILED = self.forward.get("forward-failed-reaction", QQ_FORWARD_FAILED)
        self.DISCORD_COMMAND_PREFIX = self.forward.get("discord-command-prefix", DISCORD_COMMAND_PREFIX)
        self.QQ_SUDO_FORMAT = self.forward.get("qq-sudo-format", QQ_SUDO_FORMAT)
        self.QQ_COMMAND_PREFIX = self.forward.get("qq-command-prefix", QQ_COMMAND_PREFIX)
        self.QQ_COMMAND = self.forward.get("qq-command", QQ_COMMAND)
        self.QQ_COMMAND_NAME = self.QQ_COMMAND_PREFIX + self.QQ_COMMAND
        self.BOT_NAME = self.forward.get("bot-name", BOT_NAME)
        self.PREFIX = self.forward.get("prefix", PREFIX)
        self.IMAGE_PLACEHOLDER = self.forward.get("image-placeholder", IMAGE_PLACEHOLDER)
