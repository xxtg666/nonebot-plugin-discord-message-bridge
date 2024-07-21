from pydantic import BaseModel
from nonebot import get_plugin_config


class Config(BaseModel):
    dmb_http_proxy: str = "http://127.0.0.1:7890"
    dmb_qq_bind_file: str = "data/discord_message_bridge_qq_bind.json"
    dmb_max_message_id_record: int = 3000
    dmb_forward_failed_reaction: str = "cry"
    dmb_max_reply_preview_length: int = 100
    dmb_prefix: str = "[Discord] "
    dmb_bot_name: str = "Discord Message Bridge"
    dmb_qq_sudo_format: str = "/sudo {Q} {C}"
    dmb_qq_command: str = "dmb"
    dmb_discord_command_prefix: str = "~"
    dmb_qq_command_prefix: str = "."


config = get_plugin_config(Config)


# 网络代理地址，若不需要请留空
HTTP_PROXY = config.dmb_http_proxy

# Discord Bot Token
TOKEN = config.dmb_bot_token

# Discord Webhook URL
WEBHOOK_URL = config.dmb_webhook_url

# Discord Webhook ID (WEBHOOK_URL 中的那一串数字)
WEBHOOK_ID = config.dmb_webhook_id

# Discord 服务器 ID
GUILD_ID = config.dmb_guild_id

# Discord 频道 ID
CHANNEL_ID = config.dmb_channel_id

# QQ 群号
QQ_ID = config.dmb_qq_id

# 转发失败时添加的 reaction 名称 (支持自定义表情符号)
QQ_FORWARD_FAILED = config.dmb_forward_failed_reaction

# QQ - Discord 用户 id 绑定文件路径
qq_bind_file = config.dmb_qq_bind_file

# 转发回复消息时显示的原消息内容的最大长度
MAX_REPLY_PREVIEW_LENGTH = config.dmb_max_reply_preview_length

# 记录 QQ 与 Discord 消息互相对应 id 的最大数量
MAX_MESSAGE_ID_RECORD = config.dmb_max_message_id_record

# 转发消息前缀
PREFIX = config.dmb_prefix

# Bot 名称
BOT_NAME = config.dmb_bot_name

# QQ 机器人命令名
QQ_COMMAND = config.dmb_qq_command

# QQ 机器人命令前缀
QQ_COMMAND_PREFIX = config.dmb_qq_command_prefix

# Discord 机器人命令前缀
DISCORD_COMMAND_PREFIX = config.dmb_discord_command_prefix

# QQ 转发机器人以用户身份调用其它机器人时发送消息的格式
# 若其它机器人支持此功能，才可使用，否则请留空
# {Q} 自动替换为用户对应的 QQ 号
# {C} 自动替换为用户发送的内容
QQ_SUDO_FORMAT = config.dmb_qq_sudo_format
