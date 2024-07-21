from nonebot import logger
import httpx

from .. import global_vars as gv


async def webhook_send_message(username, avatar_url, content, fwd, images=[]):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url=fwd.WEBHOOK_URL + "?wait=true",
            data={"username": username, "avatar_url": avatar_url, "content": content},
            files=[
                (
                    f"file[{idx+1}]",
                    (
                        f"file{idx+1}.jpg",
                        (await client.get(img_url)).content,
                        "image/jpeg",
                    ),
                )
                for idx, img_url in enumerate(images)
            ],
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
            url=f"https://discord.com/api/v10/channels/{fwd.CHANNEL}/messages",
            headers={"Authorization": f"Bot {fwd.TOKEN}"},
            data={"content": f"<{name}> {content}"},
            files=files,
        )


async def send_message(content, fwd):
    async with httpx.AsyncClient() as client:
        await client.post(
            url=f"https://discord.com/api/channels/{fwd.CHANNEL_ID}/messages",
            headers={"Authorization": f"Bot {fwd.TOKEN}", "User-Agent": "DiscordBot"},
            data={"content": content},
        )


async def send_list_message(content_list, fwd):
    for i in content_list:
        if not i[1]:
            await send_message(i[0], fwd)
        else:
            await gv.qq_bot.send_group_msg(group_id=fwd.QQ_GROUP_ID, message=i[0])
