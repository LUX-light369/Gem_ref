import io
import random
from datetime import datetime
from typing import List
from PIL import Image, ImageDraw
from aiogram.types import BufferedInputFile
from config import FONT_TITLE, FONT_NUMBERS, FONT_CELL, FONT_DATE
from services.game_logic import COLS, parse_cells

def generate_loto_card(username: str, numbers: List[str], registered_at: datetime) -> BufferedInputFile:
    img = Image.new("RGB", (450, 280), (random.randint(180, 240), random.randint(180, 240), random.randint(180, 240)))
    draw = ImageDraw.Draw(img)
    text = f"@{username}" if username else "Аноним"
    bbox = draw.textbbox((0, 0), text, font=FONT_TITLE)
    draw.text(((450 - (bbox[2]-bbox[0])) / 2, 10), text, fill="black", font=FONT_TITLE)
    sorted_nums = sorted(numbers, key=lambda x: int(x) if x.isdigit() else x)
    cell_w, cell_h, start_x, start_y = 70, 40, (450 - 70 * 5) / 2, 60
    for row in range(3):
        for col in range(5):
            num = sorted_nums[row * 5 + col]; x, y = start_x + col * cell_w, start_y + row * cell_h
            draw.rectangle([x, y, x + cell_w, y + cell_h], outline="black", width=1)
            bbox = draw.textbbox((0, 0), str(num), font=FONT_NUMBERS)
            draw.text((x + (cell_w - (bbox[2]-bbox[0])) / 2, y + (cell_h - (bbox[3]-bbox[1])) / 2), str(num), fill="black", font=FONT_NUMBERS)
    dt_str = registered_at.strftime("%d.%m.%Y %H:%M (Нск)")
    bbox = draw.textbbox((0, 0), dt_str, font=FONT_DATE)
    draw.text(((450 - (bbox[2] - bbox[0])) / 2, start_y + 3 * cell_h + 5), dt_str, fill="black", font=FONT_DATE)
    bio = io.BytesIO(); img.save(bio, format="PNG"); bio.seek(0)
    return BufferedInputFile(bio.read(), filename="loto_card.png")

def generate_sea_battle_card(username: str, cells: List[str], registered_at: datetime) -> BufferedInputFile:
    img = Image.new("RGB", (520, 600), (random.randint(180, 240), random.randint(180, 240), random.randint(180, 240)))
    draw = ImageDraw.Draw(img)
    text = f"@{username}" if username else "Аноним"
    bbox = draw.textbbox((0,0), text, font=FONT_TITLE)
    draw.text(((520 - (bbox[2]-bbox[0]))//2, 10), text, fill="black", font=FONT_TITLE)
    cell_size, start_x, start_y = 40, 60, max(60, bbox[3] + 80)
    for i, ch in enumerate(COLS): draw.text((start_x + i * cell_size + 15, start_y - 30), ch, fill="black", font=FONT_CELL)
    for i in range(10): draw.text((start_x - 25, start_y + i * cell_size + 12), str(i+1), fill="black", font=FONT_CELL)
    cells_set = parse_cells(cells)
    for r in range(10):
        for c in range(10):
            x, y = start_x + c * cell_size, start_y + r * cell_size
            draw.rectangle([x, y, x + cell_size, y + cell_size], outline="black", width=1)
            if (r, c) in cells_set: draw.rectangle([x+2, y+2, x+cell_size-2, y+cell_size-2], fill="navy")
    dt_str = registered_at.strftime("%d.%m.%Y %H:%M (Нск)")
    bbox = draw.textbbox((0,0), dt_str, font=FONT_DATE)
    draw.text(((520 - (bbox[2] - bbox[0]))//2, start_y + 10*cell_size + 20), dt_str, fill="black", font=FONT_DATE)
    bio = io.BytesIO(); img.save(bio, format="PNG"); bio.seek(0)
    return BufferedInputFile(bio.read(), filename="sea_battle_card.png")
