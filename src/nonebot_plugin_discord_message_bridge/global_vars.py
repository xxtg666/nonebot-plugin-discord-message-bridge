from .config import *

qq_bot = None
discord_bot_thread = None
already_started_discord_bot = False
temp_bind_qq = {}  # qq:rid
temp_bind_discord = {}  # rid:dis
message_id_records = []  # (qq:dc)
qq_command_name = QQ_COMMAND_PREFIX + QQ_COMMAND
bot_restart_times = 0
discord_bot_started = False
