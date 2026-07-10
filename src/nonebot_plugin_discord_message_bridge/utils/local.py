from nonebot import logger
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.exception import FinishedException
import random
import json
import html
import re
import os
import time
from urllib.parse import urlparse

from ..config import *
from .. import global_vars as gv


def _load_qq_bind():
    with open(qq_bind_file, "r", encoding="utf-8") as file:
        return json.load(file)


def get_qq_bind(discord_id):
    return _load_qq_bind().get(str(discord_id), False)


def get_qq_bind_discord(qq_id):
    return {qq: dis for dis, qq in _load_qq_bind().items()}.get(
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


def _parse_cq_params(params):
    result = {}
    for item in params.split(","):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        result[key] = process_text(value)
    return result


def _get_attachment_url(params):
    url = params.get("url")
    if url:
        return url
    file = params.get("file", "")
    if file.startswith(("http://", "https://")):
        return file
    return ""


def _get_filename(params, url, cq_type):
    filename = (
        params.get("name")
        or params.get("file_name")
        or params.get("file")
        or os.path.basename(urlparse(url).path)
    )
    filename = os.path.basename(str(filename))
    return filename or cq_type


def _build_attachment(cq_type, params, placeholder):
    url = _get_attachment_url(params)
    if not url:
        return None
    filename = _get_filename(params, url, cq_type)
    return {
        "type": cq_type,
        "url": url,
        "filename": filename,
        "placeholder": placeholder,
        "size": params.get("size"),
        "is_video": cq_type == "video" or is_video_file(filename, url),
    }


def get_cq_attachments(string):
    attachments = []
    for match in re.finditer(r"\[CQ:(?P<type>[a-zA-Z0-9_-]+)(?P<params>(?:,[^\]]*)?)\]", string):
        cq_type = match.group("type")
        if cq_type not in {"image", "mface", "file", "video"}:
            continue
        params = _parse_cq_params(match.group("params").lstrip(","))
        attachment = _build_attachment(cq_type, params, match.group(0))
        if attachment:
            attachments.append(attachment)
    return attachments


def get_message_attachments(message):
    attachments = []
    for segment in message:
        cq_type = getattr(segment, "type", "")
        if cq_type not in {"image", "mface", "file", "video"}:
            continue
        params = getattr(segment, "data", {}) or {}
        attachment = _build_attachment(cq_type, params, str(segment))
        if attachment:
            attachments.append(attachment)
    return attachments


def render_message_for_discord(message):
    text = ""
    attachments = []
    for segment in message:
        cq_type = getattr(segment, "type", "")
        data = getattr(segment, "data", {}) or {}
        if cq_type == "text":
            text += process_text(data.get("text", ""))
            continue
        if cq_type == "at":
            qq = str(data.get("qq", ""))
            dis_id = get_qq_bind_discord(qq)
            text += f"<@{dis_id}>" if dis_id else str(segment)
            continue
        if cq_type in {"image", "mface"}:
            attachment = _build_attachment(cq_type, data, str(segment))
            if attachment:
                attachments.append(attachment)
            text += IMAGE_PLACEHOLDER
            continue
        if cq_type in {"file", "video"}:
            continue
        if cq_type == "reply":
            continue
        text += process_text(str(segment))
    return text, attachments


def render_discord_text_for_qq(text):
    """Build QQ text segments without parsing user-controlled CQ codes."""
    message = Message()
    position = 0
    for match in re.finditer(r"<@!?(\d+)>", text):
        if match.start() > position:
            message += MessageSegment.text(text[position : match.start()])
        qq_id = get_qq_bind(match.group(1))
        if qq_id:
            message += MessageSegment.at(qq_id)
        else:
            message += MessageSegment.text(match.group(0))
        position = match.end()
    if position < len(text):
        message += MessageSegment.text(text[position:])
    return message


def get_cq_images(string):
    cq_images = re.findall(r"\[CQ:image.*?\d+\]", string) + re.findall(
        r"\[CQ:mface.*?\]", string
    )
    return cq_images


def _has_extension(extension_list, *values):
    for value in values:
        if not value:
            continue
        parsed = urlparse(str(value))
        target = parsed.path if parsed.scheme else str(value).split("?", 1)[0]
        if target.lower().endswith(extension_list):
            return True
    return False


def is_video_file(filename="", url="", content_type=""):
    if content_type and content_type.split(";", 1)[0].lower().startswith("video/"):
        return True
    return _has_extension(
        (
            ".mp4",
            ".mov",
            ".m4v",
            ".webm",
            ".mkv",
            ".avi",
            ".flv",
            ".wmv",
            ".mpeg",
            ".mpg",
        ),
        filename,
        url,
    )


def is_image_file(filename="", url="", content_type=""):
    if content_type and content_type.split(";", 1)[0].lower().startswith("image/"):
        return True
    return _has_extension(
        (
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".webp",
            ".bmp",
            ".tif",
            ".tiff",
        ),
        filename,
        url,
    )


def format_file_size(size):
    try:
        size = int(size)
    except (TypeError, ValueError):
        return "未知大小"
    units = ("B", "KiB", "MiB", "GiB")
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} {unit}"
        value /= 1024


def get_qq_sender_name(sender, fallback):
    if sender:
        card = getattr(sender, "card", None)
        nickname = getattr(sender, "nickname", None)
        if isinstance(sender, dict):
            card = sender.get("card")
            nickname = sender.get("nickname")
        return str(nickname or card or fallback)
    return str(fallback)


async def get_group_member_name(bot, group_id, user_id):
    try:
        member = await bot.call_api(
            "get_group_member_info",
            group_id=group_id,
            user_id=user_id,
            no_cache=False,
        )
    except FinishedException:
        raise
    except Exception:
        logger.warning(
            f"Failed to get QQ group member info: GroupID={group_id} UserID={user_id}"
        )
        return str(user_id)
    return get_qq_sender_name(member, user_id)


def replace_cq_at_with_ids(msg):
    pattern = r"\[CQ:at,qq=(\d+)\]"
    ids = {qq: dis for dis, qq in _load_qq_bind().items()}

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
    ids = _load_qq_bind()

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


def record_uploaded_group_file(group_id, filename):
    gv.uploaded_group_files.append((str(group_id), str(filename), time.time()))
    if len(gv.uploaded_group_files) > 100:
        gv.uploaded_group_files.pop(0)


def consume_uploaded_group_file(group_id, filename, ttl=120):
    now = time.time()
    gv.uploaded_group_files[:] = [
        item for item in gv.uploaded_group_files if now - item[2] <= ttl
    ]
    for item in list(gv.uploaded_group_files):
        if item[0] == str(group_id) and item[1] == str(filename):
            gv.uploaded_group_files.remove(item)
            return True
    return False


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
