"""
参考:
 https://github.com/Moonlark-Dev/XDbot2/blob/master/src/plugins/Core/plugins/cave.py#L333C2-L377C1
"""

from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment
from typing import cast


class ForwardMessageParser:

    def __init__(self, bot: Bot, segment: MessageSegment) -> None:
        if segment.type != "forward":
            raise TypeError
        self.bot = bot
        self.messages = []
        self.segment = segment

    async def parse(self) -> None:
        self.messages = await self.get_forward(self.segment)

    async def get_forward(self, segment: MessageSegment) -> list[tuple[dict, Message]]:
        response = cast(dict[str, dict], await self.bot.get_forward_msg(id=segment.data["id"]))
        messages = []
        for message_data in response["messages"]:
            message = Message()
            for seg in message_data["content"]:
                message.append(MessageSegment(**seg))
            messages.append((message_data["sender"], message))
        return messages
