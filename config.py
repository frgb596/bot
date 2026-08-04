import os
from dotenv import load_dotenv
load_dotenv()

# Discord
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN missing")

# --- Two login methods ---
# 1) Paste tokens (traditional)
APP_RT = os.getenv("APP_RT")
APP_AT = os.getenv("APP_AT")

# 2) Roblox login (recommended)
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE", None)

# If both provided, Roblox takes precedence.
BLOXFLIP_AUTH = os.getenv("BLOXFLIP_AUTH", None)  # optional, can be used directly

# Channels
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "1533441681519804466"))

# Model paths
MINES_MODEL_PATH = os.getenv("MINES_MODEL_PATH", "models/mines_model.h5")
TOWERS_MODEL_PATH = os.getenv("TOWERS_MODEL_PATH", "models/towers_model.h5")
