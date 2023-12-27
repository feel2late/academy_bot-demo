from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext


router = Router()  
    
@router.callback_query(F.data.startswith('cancel_from_'), StateFilter('*'))
async def cancel_state(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(answer_markup='')
    await state.clear()
    await callback.message.answer('❌ Действие отменено.')

