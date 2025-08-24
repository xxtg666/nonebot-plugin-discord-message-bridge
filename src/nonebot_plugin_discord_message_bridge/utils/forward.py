from ..config import *
from .. import global_vars as gv
import httpx


async def get_forward_msg(message_id):
    """使用nonebot2的方法获取合并转发消息"""
    try:
        # 使用nonebot2的call_api方法获取合并转发消息
        result = await gv.qq_bot.call_api("get_forward_msg", message_id=message_id)
        return {
            "data": result
        }
    except Exception as e:
        raise Exception(f"Failed to get forward message: {e}")

async def upload_forward_msg(data, id):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            FORWARD_MSG_SERVER + "/upload/" + id,
            json=data
        )
        if response.status_code == 200:
            return response.json().get("chat_uuid", "")
        else:
            raise Exception("Failed to upload forward message")

def get_preview_url(uuid):
    return FORWARD_MSG_SERVER + "/?id=" + uuid

async def get_forward_mapping(id):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            FORWARD_MSG_SERVER + "/mapping/" + id
        )
        if response.status_code == 200:
            return response.json().get("chat_uuid", "")
        else:
            raise Exception("Failed to get forward message mapping")