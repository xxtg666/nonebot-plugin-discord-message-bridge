from nonebot import logger
import httpx
import mimetypes
import os
import tempfile
import uuid

from .. import global_vars as gv
from ..config import DISCORD_UPLOAD_LIMIT
from . import local as uLocal


def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


async def webhook_send_message(username, avatar_url, content, fwd, attachments=None):
    if attachments is None:
        attachments = []
    async with httpx.AsyncClient() as client:
        files = []
        skipped = []
        for idx, attachment in enumerate(attachments):
            size = _to_int(attachment.get("size"))
            if size is not None and size > DISCORD_UPLOAD_LIMIT:
                skipped.append(attachment)
                continue
            try:
                head = await client.head(attachment["url"], follow_redirects=True)
                content_length = _to_int(head.headers.get("content-length"))
                if content_length is not None and content_length > DISCORD_UPLOAD_LIMIT:
                    attachment["size"] = content_length
                    skipped.append(attachment)
                    continue
            except Exception:
                pass
            resp = await client.get(attachment["url"])
            content_length = _to_int(resp.headers.get("content-length"))
            if content_length is not None and content_length > DISCORD_UPLOAD_LIMIT:
                attachment["size"] = content_length
                skipped.append(attachment)
                continue
            if len(resp.content) > DISCORD_UPLOAD_LIMIT:
                attachment["size"] = len(resp.content)
                skipped.append(attachment)
                continue
            content_type = (
                resp.headers.get("content-type")
                or mimetypes.guess_type(attachment["filename"])[0]
                or "application/octet-stream"
            )
            files.append(
                (
                    f"file[{idx+1}]",
                    (
                        attachment["filename"],
                        resp.content,
                        content_type,
                    ),
                )
            )
        if skipped:
            skipped_text = "\n".join(
                f"[文件过大未上传] {attachment['filename']} ({uLocal.format_file_size(attachment.get('size'))}): {attachment['url']}"
                for attachment in skipped
            )
            content = (content + "\n" + skipped_text).strip()
        resp = await client.post(
            url=uLocal.get_discord_channel(fwd["discord-channel"])["webhook-url"] + "?wait=true",
            data={"username": username, "avatar_url": avatar_url, "content": content},
            files=files,
        )
        logger.debug("server response: " + str(resp.json()))
        return resp.json()["id"]


async def send_message_with_files(file_paths, name, content, fwd):
    async with httpx.AsyncClient() as client:
        files = []
        ix = 0
        for f in file_paths:
            files.append(
                (
                    f"file{ix}",
                    (f"image{ix}.jpg", (await client.get(url=f)).content, "image/jpeg"),
                )
            )
            ix += 1
        await client.post(
            url=f"https://discord.com/api/v10/channels/{uLocal.get_discord_channel(fwd['discord-channel'])['channel-id']}/messages",
            headers={"Authorization": f"Bot {uLocal.get_bot_token(uLocal.get_discord_channel(fwd['discord-channel'])['bot'])}"},
            data={"content": f"<{name}> {content}"},
            files=files,
        )


def _safe_filename(filename):
    filename = os.path.basename(filename) or "file"
    return "".join(ch if ch not in '<>:"/\\|?*' else "_" for ch in filename)


async def download_file_to_cache(file_url, filename):
    cache_dir = os.path.join(tempfile.gettempdir(), "discord_message_bridge")
    os.makedirs(cache_dir, exist_ok=True)
    safe_name = _safe_filename(filename)
    file_path = os.path.abspath(os.path.join(cache_dir, f"{uuid.uuid4().hex}_{safe_name}"))
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(file_url)
        response.raise_for_status()
    with open(file_path, "wb") as file:
        file.write(response.content)
    return file_path


async def send_qq_file(group_id, file_url, filename):
    try:
        file_path = await download_file_to_cache(file_url, filename)
        uLocal.record_uploaded_group_file(group_id, filename)
        await gv.qq_bot.call_api(
            "upload_group_file",
            group_id=group_id,
            file=file_path,
            name=filename,
        )
        return
    except Exception:
        try:
            uLocal.record_uploaded_group_file(group_id, filename)
            await gv.qq_bot.call_api(
                "upload_group_file",
                group_id=group_id,
                file=file_url,
                name=filename,
            )
            return
        except Exception:
            pass
        await gv.qq_bot.send_group_msg(
            group_id=group_id,
            message=f"{'[视频]' if uLocal.is_video_file(filename, file_url) else '[文件]'} {filename}: {file_url}",
        )


async def send_message(content, fwd):
    async with httpx.AsyncClient() as client:
        await client.post(
            url=f"https://discord.com/api/channels/{uLocal.get_discord_channel(fwd['discord-channel'])['channel-id']}/messages",
            headers={"Authorization": f"Bot {uLocal.get_bot_token(uLocal.get_discord_channel(fwd['discord-channel'])['bot'])}", "User-Agent": "DiscordBot"},
            data={"content": content},
        )


async def send_list_message(content_list, fwd):
    for i in content_list:
        if not i[1]:
            await send_message(i[0], fwd)
        else:
            await gv.qq_bot.send_group_msg(group_id=uLocal.get_qq_group_id(fwd['qq-group']), message=i[0])
