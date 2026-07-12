from pydantic import BaseModel
from nonebot import get_plugin_config


class Config(BaseModel):
    # 网络代理地址，若不需要请留空
    dmb_http_proxy: str = "http://127.0.0.1:7890"
    
    # QQ - Discord 用户 id 绑定文件路径
    dmb_qq_bind_file: str = "data/discord_message_bridge_qq_bind.json"
    
    # 转发配置文件路径
    dmb_forwards_config_file: str = "data/discord_message_bridge_forwards.yaml"
    
    # 记录 QQ 与 Discord 消息互相对应 id 的最大数量
    dmb_max_message_id_record: int = 6000
    
    # 转发失败时添加的 reaction 名称 (支持自定义表情符号)
    dmb_forward_failed_reaction: str = "😢"
    
    # 转发回复消息时显示的原消息内容的最大长度
    dmb_max_reply_preview_length: int = 100
    
    # Discord -> QQ 转发消息前缀
    dmb_prefix: str = "[Discord] "
    
    # QQ -> Discord 转发消息后缀
    dmb_suffix: str = " [QQ]"
    
    # 转发图片占位符
    dmb_image_placeholder: str = " [图片] "

    # 转发视频占位符
    dmb_video_placeholder: str = " [视频] "

    # 编辑消息占位符
    dmb_edit_placeholder: str = "[编辑消息] "
    
    # 消息已被删除占位符
    dmb_delete_placeholder: str = "[消息已被删除]"
    
    # 撤回消息时是否同步删除另一端消息；关闭时使用删除占位符
    dmb_delete_on_recall: bool = False

    # QQ -> Discord 转发时是否优先显示 QQ 群名片
    dmb_use_qq_group_card: bool = True

    # Bot 名称
    dmb_bot_name: str = "Discord Message Bridge"
    
    # QQ 机器人命令名
    dmb_qq_command: str = "dmb"
    
    # Discord 机器人命令前缀
    dmb_discord_command_prefix: str = "~"
    
    # QQ 机器人命令前缀
    dmb_qq_command_prefix: str = "."
    
    # 关闭报错反馈
    dmb_no_traceback: bool = False
    
    # 一对多发送消息间隔
    dmb_qq_send_interval: float = 0.2
    
    # 合并转发消息回复占位符
    dmb_forward_msg_placeholder: str = "[合并转发]"
    
    # 转发消息上传服务器，请部署 https://github.com/xxtg666/Forward-Message-Server 后修改为其 SERVER_URL
    dmb_forward_msg_server: str = ""

    # Discord 附件上传大小限制（字节），超过后只发送文件信息，不上传附件
    dmb_discord_upload_limit: int = 10 * 1024 * 1024


config = get_plugin_config(Config)

HTTP_PROXY = config.dmb_http_proxy
QQ_FORWARD_FAILED = config.dmb_forward_failed_reaction
qq_bind_file = config.dmb_qq_bind_file
forwards_config_file = config.dmb_forwards_config_file
MAX_REPLY_PREVIEW_LENGTH = config.dmb_max_reply_preview_length
MAX_MESSAGE_ID_RECORD = config.dmb_max_message_id_record
PREFIX = config.dmb_prefix
SUFFIX = config.dmb_suffix
IMAGE_PLACEHOLDER = config.dmb_image_placeholder
VIDEO_PLACEHOLDER = config.dmb_video_placeholder
EDIT_PLACEHOLDER = config.dmb_edit_placeholder
DELETE_PLACEHOLDER = config.dmb_delete_placeholder
DELETE_ON_RECALL = config.dmb_delete_on_recall
USE_QQ_GROUP_CARD = config.dmb_use_qq_group_card
BOT_NAME = config.dmb_bot_name
QQ_COMMAND_NAME = config.dmb_qq_command
QQ_COMMAND_PREFIX = config.dmb_qq_command_prefix
DISCORD_COMMAND_PREFIX = config.dmb_discord_command_prefix
NO_TRACEBACK = config.dmb_no_traceback
QQ_SEND_INTERVAL = config.dmb_qq_send_interval
FORWARD_MSG_PLACEHOLDER = config.dmb_forward_msg_placeholder
FORWARD_MSG_SERVER = config.dmb_forward_msg_server
DISCORD_UPLOAD_LIMIT = config.dmb_discord_upload_limit
