import random
import re
from typing import List, Set, Tuple, Dict
from datetime import timedelta, datetime

COLS = "АБВГДЕЖЗИК"
SLOT_VALUES = [5, 3, 4, 7]
CARD_LIFETIME_DAYS = 2
dice_sequences: Dict[int, Dict[int, List[int]]] = {}

def now_novosibirsk() -> datetime:
    return datetime.now() + timedelta(hours=7)

def is_recent_card(registered_at: datetime) -> bool:
    return (now_novosibirsk() - registered_at) <= timedelta(days=CARD_LIFETIME_DAYS)

def parse_list(text: str) -> List[str]:
    return [p.strip() for p in re.split(r'[,\s]+', text.strip()) if p.strip()]

def parse_cells(cells: List[str]) -> Set[Tuple[int, int]]:
    result = set()
    for c in cells:
        c = c.strip().upper()
        if len(c) < 2: continue
        letter, num = c[0], c[1:]
        if letter in COLS and num.isdigit() and 1 <= int(num) <= 10:
            result.add((int(num)-1, COLS.index(letter)))
    return result

def validate_ships(cells_set: Set[Tuple[int, int]]) -> bool:
    if len(cells_set) != 15: return False
    visited, ships = set(), []
    for cell in cells_set:
        if cell in visited: continue
        stack, ship = [cell], set()
        while stack:
            r, c = stack.pop()
            if (r, c) in visited: continue
            visited.add((r, c)); ship.add((r, c))
            for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                if (r+dr, c+dc) in cells_set and (r+dr, c+dc) not in visited: stack.append((r+dr, c+dc))
        if len({rr for rr,_ in ship}) > 1 and len({cc for _,cc in ship}) > 1: return False
        ships.append(ship)
    from collections import Counter
    sz = Counter(len(s) for s in ships)
    if sz.get(1,0) != 4 or sz.get(2,0) != 2 or sz.get(3,0) != 1 or sz.get(4,0) != 1: return False
    cell_to_ship = {cell: idx for idx, ship in enumerate(ships) for cell in ship}
    for idx, ship in enumerate(ships):
        for r, c in ship:
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    if dr == 0 and dc == 0: continue
                    nr, nc = r+dr, c+dc
                    if (nr, nc) in cell_to_ship and cell_to_ship[(nr, nc)] != idx: return False
    return True

def generate_random_sea_battle_cells() -> List[str]:
    while True:
        field = [[0]*10 for _ in range(10)]
        try:
            place_ship(field, 4); place_ship(field, 3); place_ship(field, 2); place_ship(field, 2)
            for _ in range(4): place_ship(field, 1)
            return [f"{COLS[c]}{r+1}" for r in range(10) for c in range(10) if field[r][c] == 1]
        except Exception: continue

def place_ship(field: List[List[int]], size: int):
    for _ in range(100):
        orientation = random.choice(['h', 'v'])
        r = random.randint(0, 9 if orientation == 'h' else 10 - size)
        c = random.randint(0, 10 - size if orientation == 'h' else 9)
        coords = [(r, c+i) if orientation == 'h' else (r+i, c) for i in range(size)]
        if all(field[rr][cc] == 0 for rr, cc in coords) and all(
            not any(field[nr][nc] for nr in range(max(0, rr-1), min(10, rr+2))
                    for nc in range(max(0, cc-1), min(10, cc+2)) if (nr, nc) not in coords) for rr, cc in coords):
            for rr, cc in coords: field[rr][cc] = 1
            return
    raise Exception("Не удалось разместить корабль")

async def process_dice_sequence(chat_id: int, user_id: int, value: int) -> int | None:
    seq = dice_sequences.setdefault(chat_id, {}).setdefault(user_id, [])
    seq.append(value)
    if len(seq) == 3:
        total = sum(seq) * (2 if seq[0] == seq[1] == seq[2] else 1)
        del dice_sequences[chat_id][user_id]
        return total
    return None

def calc_slot_sum(value: int) -> int:
    v = value - 1
    i, j, k = v // 16, (v // 4) % 4, v % 4
    total = SLOT_VALUES[i] + SLOT_VALUES[j] + SLOT_VALUES[k]
    return total * 2 if i == j == k else total
