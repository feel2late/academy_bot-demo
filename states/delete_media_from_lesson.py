from aiogram.fsm.state import State, StatesGroup


class DeleteLessonMedia(StatesGroup):
    waiting_for_id = State()


class DeleteAdditionalMaterials(StatesGroup):
    waiting_for_id = State()


