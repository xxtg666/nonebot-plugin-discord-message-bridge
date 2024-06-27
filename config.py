# 网络代理地址，若不需要请留空
HTTP_PROXY = "http://127.0.0.1:7890"

# Discord Bot Token
TOKEN = "xxxxxxxxxx"

# Discord Webhook URL
WEBHOOK_URL = "https://discord.com/api/webhooks/xxxxxxxxxx/xxxxxxxxxx"

# Discord Webhook ID (WEBHOOK_URL 中的那一串数字)
WEBHOOK_ID = 0

# Discord 服务器 ID
GUILD_ID = 0

# Discord 频道 ID
CHANNEL_ID = 0

# QQ 群号
QQ_ID = 0

# 转发失败时添加的 reaction 名称 (支持自定义表情符号)
QQ_FORWARD_FAILED = "cry"

# 日志文件路径
LOG_FILE = "data/dmb_log.txt"

# QQ - Discord 用户 id 绑定文件路径
qq_bind_file = "data/discord_message_bridge_qq_bind.json"
qq_bind_file_2 = "data/discord_message_bridge_qq_bind_2.json"

# 转发回复消息时显示的原消息内容的最大长度
MAX_REPLY_PREVIEW_LENGTH = 100

# 转发消息前缀
PREFIX = "[Discord] "

# Bot 名称
BOT_NAME = "Discord Message Bridge"

# QQ 机器人命令名
QQ_COMMAND = "dmb"

# QQ 机器人命令前缀
QQ_COMMAND_PREFIX = "."

# Discord 机器人命令前缀
DISCORD_COMMAND_PREFIX = "~"

# QQ 转发机器人以用户身份调用其它机器人时发送消息的格式
# 若其它机器人支持此功能，才可使用，否则请留空
# {Q} 自动替换为用户对应的 QQ 号
# {C} 自动替换为用户发送的内容
QQ_SUDO_FORMAT = "/sudo {Q} {C}"
