import os
from dotenv import load_dotenv

load_dotenv()

# Discord
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN missing")

# Bloxflip cookies (both required)
APP_RT = os.getenv("APP_RT")
APP_AT = os.getenv("APP_AT")
if not APP_RT or not APP_AT:
    raise ValueError("Both APP_RT and APP_AT are required")

# Optional: still allow Authorization header if you have one
BLOXFLIP_AUTH = os.getenv("BLOXFLIP_AUTH", None)

# Channels
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "1533441681519804466"))

# Model paths
MINES_MODEL_PATH = os.getenv("MINES_MODEL_PATH", "models/mines_model.h5")
SLIDE_MODEL_PATH = os.getenv("SLIDE_MODEL_PATH", "models/slide_model.h5")
SLIDE_HISTORY_FILE = os.getenv("SLIDE_HISTORY_FILE", "data/slide_history.csv")
