from nonebot import logger
import random
import json
import html
import re
import os

from ..config import *
from .. import global_vars as gv


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
    cq_images = re.findall(r"\[CQ:image.*?\d+\]", string) + re.findall(
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
                gv.message_id_records.remove(i)
                gv.message_id_records.append(i)
                return i[1]
    elif this == "dc":
        for i in gv.message_id_records:
            if i[1] == str(_id):
                gv.message_id_records.remove(i)
                gv.message_id_records.append(i)
                return i[0]
    return None


def record_message_id(qq_id, dc_id):
    gv.message_id_records.append((str(qq_id), str(dc_id)))
    if len(gv.message_id_records) > MAX_MESSAGE_ID_RECORD:
        gv.message_id_records.pop(0)


def get_bot_token(bot_id):
    return gv.forward_config["discord-bots"][bot_id]


def get_qq_group_id(qq_group_num):
    return gv.forward_config["qq-groups"][qq_group_num]


def get_discord_channel(discord_channel_num):
    return gv.forward_config["discord-channels"][discord_channel_num]


def generate_message_link(discord_message_id, fwd):
    return f"https://discord.com/channels/{get_discord_channel(fwd['discord-channel'])['guild-id']}/{get_discord_channel(fwd['discord-channel'])['channel-id']}/{discord_message_id}"


def load_forward_config():
    for discord_channel in gv.forward_config["discord-channels"]:
        gv.forward_config["discord-channels"][discord_channel]["webhook-id"] = int(gv.forward_config["discord-channels"][discord_channel]["webhook-url"].split("/")[5])
    gv.loaded_forward_config["qq-groups"] = {}
    gv.loaded_forward_config["discord-channels"] = {}
    for forward in gv.forward_config["forwards"]:
        forward["discord-prefix"] = forward.get("discord-prefix", PREFIX)
        forward["silent"] = forward.get("silent", False)
        discord_channel = gv.forward_config["discord-channels"][forward["discord-channel"]]["channel-id"]
        qq_group = gv.forward_config["qq-groups"][forward["qq-group"]]
        _type = "silent" if forward["silent"] else "normal"
        if forward["type"] == 0 or forward["type"] == 2:
            logger.info(f"[DMB] {_type} Forward: [Discord]{discord_channel} -> [QQ]{qq_group}")
            try:
                gv.loaded_forward_config["discord-channels"][discord_channel].append(forward)
            except KeyError:
                gv.loaded_forward_config["discord-channels"][discord_channel] = [forward]
        if forward["type"] == 0 or forward["type"] == 1:
            logger.info(
                f"[DMB] {_type} Forward: [QQ]{qq_group} -> [Discord]{discord_channel}")
            try:
                gv.loaded_forward_config["qq-groups"][qq_group].append(forward)
            except KeyError:
                gv.loaded_forward_config["qq-groups"][qq_group] = [forward]


def get_forwards(forward_id, _type):
    try:
        return gv.loaded_forward_config[_type][forward_id]
    except KeyError:
        return []


class NoneAsyncWith:
    async def __aenter__(self):
        pass
    async def __aexit__(self, exc_type, exc, tb):
        pass