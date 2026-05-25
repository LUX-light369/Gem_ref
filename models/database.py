import json
from datetime import datetime, timedelta
from typing import Dict, Set, Optional
from config import DATA_FILE, MAIN_ADMIN_ID
from models.settings import ChatSettings, LotoUserData, SeaBattleUserData
from services.game_logic import now_novosibirsk, CARD_LIFETIME_DAYS

class BotData:
    def __init__(self):
        self.admins: Set[int] = {MAIN_ADMIN_ID}
        self.default_chat_id: Optional[int] = None
        self.default_channel_id: Optional[int] = None
        self.channel_invite_link: Optional[str] = None
        self.check_subscription: bool = True
        self.chats: Dict[int, ChatSettings] = {}
        self.loto_users: Dict[int, LotoUserData] = {}
        self.sea_battle_users: Dict[int, SeaBattleUserData] = {}
        self.banned_users: Dict[str, datetime] = {}
        self.registered_ever: Set[int] = set()
        self.loto_target_chat: Optional[int] = None
        self.loto_deadline: Optional[datetime] = None
        self.loto_start_message: Optional[str] = None
        self.loto_user_buttons: Dict[str, str] = {}
        self.sea_battle_target_chat: Optional[int] = None
        self.sea_battle_deadline: Optional[datetime] = None
        self.sea_battle_start_message: Optional[str] = None
        self.sea_battle_user_buttons: Dict[str, str] = {}

    def _cleanup_old_data(self):
        now = now_novosibirsk()
        self.banned_users = {u: dt for u, dt in self.banned_users.items() if dt > now}
        limit_dt = now - timedelta(days=CARD_LIFETIME_DAYS)
        self.loto_users = {uid: u for uid, u in self.loto_users.items() if u.registered_at >= limit_dt}
        self.sea_battle_users = {uid: u for uid, u in self.sea_battle_users.items() if u.registered_at >= limit_dt}

    def save(self):
        self._cleanup_old_data()
        data = {
            "admins": list(self.admins), "default_chat_id": self.default_chat_id, "default_channel_id": self.default_channel_id,
            "channel_invite_link": self.channel_invite_link, "check_subscription": self.check_subscription,
            "chats": {str(k): v.to_dict() for k, v in self.chats.items()},
            "loto_users": {str(uid): u.to_dict() for uid, u in self.loto_users.items()},
            "sea_battle_users": {str(uid): u.to_dict() for uid, u in self.sea_battle_users.items()},
            "banned_users": {uname: dt.isoformat() for uname, dt in self.banned_users.items()},
            "registered_ever": list(self.registered_ever), "loto_target_chat": self.loto_target_chat,
            "loto_deadline": self.loto_deadline.isoformat() if self.loto_deadline else None,
            "loto_start_message": self.loto_start_message, "loto_user_buttons": self.loto_user_buttons,
            "sea_battle_target_chat": self.sea_battle_target_chat,
            "sea_battle_deadline": self.sea_battle_deadline.isoformat() if self.sea_battle_deadline else None,
            "sea_battle_start_message": self.sea_battle_start_message, "sea_battle_user_buttons": self.sea_battle_user_buttons,
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls):
        obj = cls()
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f: data = json.load(f)
            obj.admins = set(data.get("admins", [MAIN_ADMIN_ID])); obj.admins.add(MAIN_ADMIN_ID)
            obj.default_chat_id = data.get("default_chat_id"); obj.default_channel_id = data.get("default_channel_id")
            obj.channel_invite_link = data.get("channel_invite_link"); obj.check_subscription = data.get("check_subscription", True)
            for k, v in data.get("chats", {}).items(): obj.chats[int(k)] = ChatSettings.from_dict(v)
            for k, v in data.get("loto_users", {}).items(): obj.loto_users[int(k)] = LotoUserData.from_dict(v)
            for k, v in data.get("sea_battle_users", {}).items(): obj.sea_battle_users[int(k)] = SeaBattleUserData.from_dict(v)
            obj.banned_users = {u: datetime.fromisoformat(dt) for u, dt in data.get("banned_users", {}).items()}
            obj.registered_ever = set(data.get("registered_ever", [])); obj.loto_target_chat = data.get("loto_target_chat")
            if data.get("loto_deadline"): obj.loto_deadline = datetime.fromisoformat(data["loto_deadline"])
            obj.loto_start_message = data.get("loto_start_message"); obj.loto_user_buttons = data.get("loto_user_buttons", {})
            obj.sea_battle_target_chat = data.get("sea_battle_target_chat")
            if data.get("sea_battle_deadline"): obj.sea_battle_deadline = datetime.fromisoformat(data["sea_battle_deadline"])
            obj.sea_battle_start_message = data.get("sea_battle_start_message"); obj.sea_battle_user_buttons = data.get("sea_battle_user_buttons", {})
        except FileNotFoundError: pass
        return obj

bot_data = BotData.load()
