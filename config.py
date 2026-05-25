import os
from PIL import ImageFont

BOT_TOKEN = os.getenv("BOT_TOKEN")
MAIN_ADMIN_ID_STR = os.getenv("MAIN_ADMIN_ID")

if not BOT_TOKEN or not MAIN_ADMIN_ID_STR:
    raise ValueError("BOT_TOKEN и MAIN_ADMIN_ID обязательны")

MAIN_ADMIN_ID = int(MAIN_ADMIN_ID_STR)
DATA_FILE = "bot_data.json"

try:
    FONT_TITLE = ImageFont.truetype("Arial.ttf", 28)
    FONT_NUMBERS = ImageFont.truetype("Arial.ttf", 24)
    FONT_CELL = ImageFont.truetype("Arial.ttf", 21)
    FONT_DATE = ImageFont.truetype("Arial.ttf", 16)
except IOError:
    FONT_TITLE = ImageFont.load_default()
    FONT_NUMBERS = ImageFont.load_default()
    FONT_CELL = ImageFont.load_default()
    FONT_DATE = ImageFont.load_default()
