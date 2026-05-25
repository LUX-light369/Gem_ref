from datetime import datetime
from typing import List, Optional

class ChatSettings:
    def __init__(self):
        self.items: List[str] = []; self.index: int = 0; self.interval: float = 2.0
        self.status: str = "stopped"; self.dice_enabled: bool = False
        self.slot_enabled: bool = False; self.loto_enabled: bool = False
        self.sea_battle_enabled: bool = False
        self.loto_triggers: List[str] = ["стоп"]; self.loto_trigger_enabled: bool = True
        self.sea_battle_triggers: List[str] = ["залп"]; self.sea_battle_trigger_enabled: bool = True
        self.muted_users: List[int] = []
        self.loto_finalists_count: int = 3; self.loto_finalists: List[str] = []
        self.loto_finalists_disabled: bool = False
        self.sea_battle_finalists_count: int = 3; self.sea_battle_finalists: List[str] = []
        self.sea_battle_finalists_disabled: bool = False
        self.dictation_start_message: Optional[str] = None

    def to_dict(self):
        return {
            "items": self.items, "index": self.index, "interval": self.interval,
            "status": self.status, "dice_enabled": self.dice_enabled,
            "slot_enabled": self.slot_enabled, "loto_enabled": self.loto_enabled,
            "sea_battle_enabled": self.sea_battle_enabled,
            "loto_triggers": self.loto_triggers, "loto_trigger_enabled": self.loto_trigger_enabled,
            "sea_battle_triggers": self.sea_battle_triggers, "sea_battle_trigger_enabled": self.sea_battle_trigger_enabled,
            "muted_users": self.muted_users, "loto_finalists_count": self.loto_finalists_count,
            "loto_finalists": self.loto_finalists, "loto_finalists_disabled": self.loto_finalists_disabled,
            "sea_battle_finalists_count": self.sea_battle_finalists_count,
            "sea_battle_finalists": self.sea_battle_finalists, "sea_battle_finalists_disabled": self.sea_battle_finalists_disabled,
            "dictation_start_message": self.dictation_start_message,
        }

    @classmethod
    def from_dict(cls, d: dict):
        obj = cls()
        for k, v in d.items():
            if hasattr(obj, k):
                if k in ("loto_triggers", "sea_battle_triggers") and isinstance(v, str): v = [v]
                setattr(obj, k, v)
        return obj

class LotoUserData:
    def __init__(self, username: str, numbers: List[str]):
        self.username = username; self.numbers = numbers
        self.registered_at = datetime.now()
        self.card_message_id: Optional[int] = None; self.photo_file_id: Optional[str] = None

    def to_dict(self):
        return {"username": self.username, "numbers": self.numbers, "registered_at": self.registered_at.isoformat(), "card_message_id": self.card_message_id, "photo_file_id": self.photo_file_id}

    @classmethod
    def from_dict(cls, d: dict):
        obj = cls.__new__(cls)
        obj.username = d["username"]; obj.numbers = d["numbers"]; obj.registered_at = datetime.fromisoformat(d["registered_at"])
        obj.card_message_id = d.get("card_message_id"); obj.photo_file_id = d.get("photo_file_id")
        return obj

class SeaBattleUserData:
    def __init__(self, username: str, cells: List[str]):
        self.username = username; self.cells = cells
        self.registered_at = datetime.now()
        self.card_message_id: Optional[int] = None; self.photo_file_id: Optional[str] = None

    def to_dict(self):
        return {"username": self.username, "cells": self.cells, "registered_at": self.registered_at.isoformat(), "card_message_id": self.card_message_id, "photo_file_id": self.photo_file_id}

    @classmethod
    def from_dict(cls, d: dict):
        obj = cls.__new__(cls)
        obj.username = d["username"]; obj.cells = d["cells"]; obj.registered_at = datetime.fromisoformat(d["registered_at"])
        obj.card_message_id = d.get("card_message_id"); obj.photo_file_id = d.get("photo_file_id")
        return obj
