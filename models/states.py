from aiogram.fsm.state import State, StatesGroup

class UploadList(StatesGroup): waiting_for_list = State()
class SetChatIdState(StatesGroup): waiting_for_chat_id = State()
class SetChannelIdState(StatesGroup): waiting_for_channel_id = State()
class VerifyList(StatesGroup): waiting_for_verify = State()
class AdminAdd(StatesGroup): waiting_for_id = State()
class AdminRemove(StatesGroup): waiting_for_id = State()
class DictationStartMessage(StatesGroup): waiting_for_start_message = State()
class SetIntervalState(StatesGroup): waiting_for_interval = State()
class SetInviteLinkState(StatesGroup): waiting_for_link = State()
class LotoRegistration(StatesGroup): waiting_for_numbers = State()
class SeaBattleRegistration(StatesGroup): waiting_for_cells = State()
class LotoBroadcast(StatesGroup): waiting_for_message = State()
class SeaBattleBroadcast(StatesGroup): waiting_for_message = State()

class LotoSettingsFlow(StatesGroup):
    waiting_for_target_chat = State(); waiting_for_deadline = State()
    waiting_for_start_message = State(); waiting_for_buttons = State()
    waiting_for_bans = State(); waiting_for_finalists = State()

class LotoTriggerInput(StatesGroup): waiting_for_triggers = State()

class SeaBattleSettingsFlow(StatesGroup):
    waiting_for_target_chat = State(); waiting_for_deadline = State()
    waiting_for_start_message = State(); waiting_for_buttons = State()
    waiting_for_triggers = State(); waiting_for_finalists = State()
    waiting_for_bans = State()

class SeaBattleTriggerInput(StatesGroup): waiting_for_triggers = State()
