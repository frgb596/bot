import os
from dotenv import load_dotenv
load_dotenv()

# Discord
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN missing")

# --- 认证方式 1: 传统 Cookie 登录 (备用) ---
# Bloxflip cookies (both required)
APP_RT = os.getenv("APP_RT")
APP_AT = os.getenv("APP_AT")
if not APP_RT or not APP_AT:
    raise ValueError("Both APP_RT and APP_AT are required")

# --- 认证方式 2: Roblox Cookie 登录 (推荐，参考 ege 项目) ---
# 如果提供了 ROBLOX_COOKIE，将优先使用此方式生成 token
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE", None)

# Optional: still allow Authorization header if you have one
BLOXFLIP_AUTH = os.getenv("BLOXFLIP_AUTH", None)

# Channels
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "1533441681519804466"))

# Model paths
MINES_MODEL_PATH = os.getenv("MINES_MODEL_PATH", "models/mines_model.h5")
SLIDE_MODEL_PATH = os.getenv("SLIDE_MODEL_PATH", "models/slide_model.h5")
SLIDE_HISTORY_FILE = os.getenv("SLIDE_HISTORY_FILE", "data/slide_history.csv")
