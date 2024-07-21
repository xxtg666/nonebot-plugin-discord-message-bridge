from .config import *

qq_bot = None
already_started_discord_bot = False
discord_bot_threads = []
temp_bind_qq = {}  # qq:rid
temp_bind_discord = {}  # rid:dis
message_id_records = []  # (qq:dc)
qq_command_name = QQ_COMMAND_PREFIX + QQ_COMMAND
forward_config = {}