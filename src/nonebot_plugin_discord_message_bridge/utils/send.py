from nonebot import logger
import httpx
import json
import mimetypes
import os
import tempfile
import uuid

from .. import global_vars as gv
from ..config import DISCORD_UPLOAD_LIMIT
from . import local as uLocal


DOWNLOAD_CHUNK_SIZE = 64 * 1024


def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_webhook_username(username):
    username = str(username).strip() or "QQ"
    return username[:80]


def _append_status_lines(content, lines):
    if not lines:
        return content
    return (content + "\n" + "\n".join(lines)).strip()


async def _download_attachment(client, attachment):
    async with client.stream(
        "GET", attachment["url"], follow_redirects=True
    ) as response:
        response.raise_for_status()
        content_length = _to_int(response.headers.get("content-length"))
        if content_length is not None and content_length > DISCORD_UPLOAD_LIMIT:
            return None, content_length, response.headers.get("content-type")

        content = bytearray()
        async for chunk in response.aiter_bytes(DOWNLOAD_CHUNK_SIZE):
            content.extend(chunk)
            if len(content) > DISCORD_UPLOAD_LIMIT:
                return None, len(content), response.headers.get("content-type")
        return bytes(content), len(content), response.headers.get("content-type")


async def webhook_send_message(
    username,
    avatar_url,
    content,
    fwd,
    attachments=None,
):
    if attachments is None:
        attachments = []
    async with httpx.AsyncClient(follow_redirects=True) as client:
        files = []
        skipped = []
        failed = []
        for attachment in attachments:
            size = _to_int(attachment.get("size"))
            if size is not None and size > DISCORD_UPLOAD_LIMIT:
                skipped.append((attachment, "文件过大未上传"))
                continue
            try:
                file_content, downloaded_size, response_content_type = (
                    await _download_attachment(client, attachment)
                )
            except Exception as exception:
                logger.warning(
                    "Failed to download attachment "
                    f"{attachment.get('filename', 'file')}: {type(exception).__name__}"
                )
                failed.append(attachment)
                continue
            attachment["size"] = downloaded_size
            if file_content is None:
                skipped.append((attachment, "文件过大未上传"))
                continue
            content_type = (
                response_content_type
                or mimetypes.guess_type(attachment["filename"])[0]
                or "application/octet-stream"
            )
            filename = _safe_filename(attachment.get("filename", "file"))
            files.append(
                (
                    f"files[{len(files)}]",
                    (
                        filename,
                        file_content,
                        content_type,
                    ),
                )
            )
        if skipped:
            skipped_text = "\n".join(
                f"[{reason}] {attachment['filename']} ({uLocal.format_file_size(attachment.get('size'))}): {attachment['url']}"
                for attachment, reason in skipped
            )
            content = _append_status_lines(content, [skipped_text])
        if failed:
            failed_text = "\n".join(
                f"[附件下载失败] {attachment['filename']}: {attachment['url']}"
                for attachment in failed
            )
            content = _append_status_lines(content, [failed_text])
        payload = {
            "username": _normalize_webhook_username(username),
            "avatar_url": avatar_url,
            "content": content,
        }
        webhook_url = uLocal.get_discord_channel(fwd["discord-channel"])[
            "webhook-url"
        ]
        webhook_url = str(
            httpx.URL(webhook_url).copy_merge_params({"wait": "true"})
        )
        try:
            if files:
                resp = await client.post(
                    url=webhook_url,
                    data={"payload_json": json.dumps(payload, ensure_ascii=False)},
                    files=files,
                )
            else:
                resp = await client.post(url=webhook_url, json=payload)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exception:
            status_code = exception.response.status_code
            raise RuntimeError(
                f"Discord webhook returned HTTP {status_code}"
            ) from None
        except httpx.RequestError as exception:
            raise RuntimeError(
                f"Discord webhook request failed: {type(exception).__name__}"
            ) from None
        response_data = resp.json()
        logger.debug(
            f"Discord webhook message sent: MessageID={response_data.get('id')}"
        )
        return response_data["id"]


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
    completed = False
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            async with client.stream("GET", file_url) as response:
                response.raise_for_status()
                with open(file_path, "wb") as file:
                    async for chunk in response.aiter_bytes(DOWNLOAD_CHUNK_SIZE):
                        file.write(chunk)
        completed = True
    finally:
        if not completed:
            remove_cached_file(file_path)
    return file_path


def remove_cached_file(file_path):
    if not file_path:
        return
    try:
        os.remove(file_path)
    except FileNotFoundError:
        pass
    except OSError as exception:
        logger.warning(f"Failed to remove attachment cache {file_path}: {exception}")


async def send_message(content, fwd):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url=f"https://discord.com/api/channels/{uLocal.get_discord_channel(fwd['discord-channel'])['channel-id']}/messages",
            headers={"Authorization": f"Bot {uLocal.get_bot_token(uLocal.get_discord_channel(fwd['discord-channel'])['bot'])}", "User-Agent": "DiscordBot"},
            data={"content": content},
        )
        response.raise_for_status()


async def send_list_message(content_list, fwd):
    for i in content_list:
        if not i[1]:
            await send_message(i[0], fwd)
        else:
            await gv.qq_bot.send_group_msg(group_id=uLocal.get_qq_group_id(fwd['qq-group']), message=i[0])
