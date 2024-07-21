import random
import json
import html
import re
import os

from ..config import *


def generate_message_link(dc_id):
    return f"https://discord.com/channels/{GUILD_ID}/{CHANNEL_ID}/{dc_id}"


def get_qq_bind(discord_id):
    return json.load(open(qq_bind_file, "r")).get(str(discord_id), False)


def get_qq_bind_discord(qq_id):
    return json.load(open(qq_bind_file_2, "r")).get(str(qq_id), False)


def genRandomID(k: int = 8) -> str:
    return "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=k))


def get_avatar_url(uid):
    return "http://q1.qlogo.cn/g?b=qq&nk=" + str(uid) + "&s=640"


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
    ids = json.load(open(qq_bind_file_2, "r"))

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


def safe_open(file_path, mode):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    return open(file_path, mode)