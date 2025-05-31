from ..config import *
import httpx


async def get_forward_msg(id):
    async with httpx.AsyncClient() as client:
        data = await client.post(
            FORWARD_MSG_GET_URL,
            headers={"Authorization": "Bearer "+FORWARD_MSG_GET_TOKEN},
            data={"message_id": id}
        )
        return data

async def upload_forward_msg(data):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            FORWARD_MSG_UPLOAD_SERVER+"/upload",
            json=data
        )
        if response.status_code == 200:
            return response.json().get("chat_uuid", "")
        else:
            raise Exception("Failed to upload forward message")

def get_preview_url(uuid):
    return FORWARD_MSG_PREVIEW_URL + uuid