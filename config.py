from pydantic import BaseModel
from nonebot import get_plugin_config


class Config(BaseModel):
    token: str
    webhook_url: str
    webhook_id: int
    guild_id: int
    channel_id: int
    qq_id: int
    log_file: str = "data/dmb_log.txt"
    qq_bind_file: str = "data/discord_message_bridge_qq_bind.json"
    qq_bind_file_2: str = "data/discord_message_bridge_qq_bind_2.json"
    qq_forward_failed: str = "cry"
    max_reply_preview_length: int = 100
    http_proxy: str = "http://127.0.0.1:7890"
    prefix: str = "[Discord] "
    bot_name: str = "Discord Message Bridge"
    qq_sudo_format: str = "/sudo {Q} {C}"
    qq_command: str = "dmb"
    discord_command_prefix: str = "~"
    qq_command_prefix: str  = "."

config = get_plugin_config(Config)


# 网络代理地址，若不需要请留空
HTTP_PROXY = config.http_proxy

# Discord Bot Token
TOKEN = config.token

# Discord Webhook URL
WEBHOOK_URL = config.webhook_url

# Discord Webhook ID (WEBHOOK_URL 中的那一串数字)
WEBHOOK_ID = config.webhook_id

# Discord 服务器 ID
GUILD_ID = config.guild_id

# Discord 频道 ID
CHANNEL_ID = config.channel_id

# QQ 群号
QQ_ID = config.qq_id

# 转发失败时添加的 reaction 名称 (支持自定义表情符号)
QQ_FORWARD_FAILED = config.qq_forward_failed

# 日志文件路径
LOG_FILE = config.log_file

# QQ - Discord 用户 id 绑定文件路径
qq_bind_file = config.qq_bind_file
qq_bind_file_2 = config.qq_bind_file_2

# 转发回复消息时显示的原消息内容的最大长度
MAX_REPLY_PREVIEW_LENGTH = config.max_reply_preview_length

# 转发消息前缀
PREFIX = config.prefix

# Bot 名称
BOT_NAME = config.bot_name

# QQ 机器人命令名
QQ_COMMAND = config.qq_command

# QQ 机器人命令前缀
QQ_COMMAND_PREFIX = config.qq_command_prefix

# Discord 机器人命令前缀
DISCORD_COMMAND_PREFIX = config.discord_command_prefix

# QQ 转发机器人以用户身份调用其它机器人时发送消息的格式
# 若其它机器人支持此功能，才可使用，否则请留空
# {Q} 自动替换为用户对应的 QQ 号
# {C} 自动替换为用户发送的内容
QQ_SUDO_FORMAT = config.qq_sudo_format
