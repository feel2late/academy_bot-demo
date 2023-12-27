from aiogram.fsm.state import State, StatesGroup


class SetWelcomeMessage(StatesGroup):
    text = State()

class SetWelcomeVideo(StatesGroup):
    video = State()
    
class SetAuthorContact(StatesGroup):
    contact = State()
    


