from pydantic import BaseModel
from nonebot import get_plugin_config


class Config(BaseModel):
    dmb_http_proxy: str = "http://127.0.0.1:7890"
    dmb_qq_bind_file: str = "data/discord_message_bridge_qq_bind.json"
    dmb_forwards_config_file: str = "data/discord_message_bridge_forwards.yaml"
    dmb_max_message_id_record: int = 3000
    dmb_forward_failed_reaction: str = "😢"
    dmb_max_reply_preview_length: int = 100
    dmb_prefix: str = "[Discord] "
    dmb_image_placeholder: str = " [图片] "
    dmb_edit_placeholder: str = "[编辑消息] "
    dmb_delete_placeholder: str = "[消息已被删除]"
    dmb_bot_name: str = "Discord Message Bridge"
    dmb_qq_command: str = "dmb"
    dmb_discord_command_prefix: str = "~"
    dmb_qq_command_prefix: str = "."
    dmb_no_traceback: bool = False
    dmb_qq_send_interval: float = 0.2


config = get_plugin_config(Config)


# 网络代理地址，若不需要请留空
HTTP_PROXY = config.dmb_http_proxy

# 转发失败时添加的 reaction 名称 (支持自定义表情符号)
QQ_FORWARD_FAILED = config.dmb_forward_failed_reaction

# QQ - Discord 用户 id 绑定文件路径
qq_bind_file = config.dmb_qq_bind_file

# 转发配置文件路径
forwards_config_file = config.dmb_forwards_config_file

# 转发回复消息时显示的原消息内容的最大长度
MAX_REPLY_PREVIEW_LENGTH = config.dmb_max_reply_preview_length

# 记录 QQ 与 Discord 消息互相对应 id 的最大数量
MAX_MESSAGE_ID_RECORD = config.dmb_max_message_id_record

# 转发消息前缀
PREFIX = config.dmb_prefix

# 转发图片占位符
IMAGE_PLACEHOLDER = config.dmb_image_placeholder

# 编辑消息占位符
EDIT_PLACEHOLDER = config.dmb_edit_placeholder

# 消息已被删除占位符
DELETE_PLACEHOLDER = config.dmb_delete_placeholder

# Bot 名称
BOT_NAME = config.dmb_bot_name

# QQ 机器人命令名
QQ_COMMAND_NAME = config.dmb_qq_command

# QQ 机器人命令前缀
QQ_COMMAND_PREFIX = config.dmb_qq_command_prefix

# Discord 机器人命令前缀
DISCORD_COMMAND_PREFIX = config.dmb_discord_command_prefix

# 关闭报错反馈
NO_TRACEBACK = config.dmb_no_traceback

# 一对多发送消息间隔
QQ_SEND_INTERVAL = config.dmb_qq_send_interval
