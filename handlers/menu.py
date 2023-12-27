import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
import db_requests
from aiogram.fsm.context import FSMContext
from bot_init import bot
import json
from aiogram import types
import config


router = Router()  

@router.callback_query(F.data == "courses")
@router.message(Command("courses")) 
async def courses(message: Message, state: FSMContext):
    await state.clear()
    admins_ids = [admin.user_telegram_id for admin in await db_requests.get_admins()]
    if hasattr(message, 'chat') and message.chat.type != 'private':
        await message.answer('Я работаю только в личных сообщениях')
        return
    builder = InlineKeyboardBuilder()
    if message.from_user.id in admins_ids:
        course_list = await db_requests.get_all_courses(for_admin=True)
    else:
        course_list = await db_requests.get_all_courses()
    hidden_courses = False

    for course in course_list:
        if not course.available:
            builder.button(text=f'⚠️ {course.title}', callback_data=f'select_course_{course.id}')
            hidden_courses = True
        else:
            builder.button(text=course.title, callback_data=f'select_course_{course.id}')
    if message.from_user.id in admins_ids or message.from_user.id == config.ROOT_ADMIN:  
        builder.button(text='➕ Создать курс', callback_data='add_new_course')
        builder.button(text='📒 Админ меню', callback_data='admin_menu')
    builder.adjust(1)
    
    if len(course_list) > 0:
        message_text = 'Выберите интересующий вас курс.\n\n'
        if message.from_user.id in admins_ids:
            if hidden_courses:
                message_text += '⚠️ Некоторые курсы не отображаются для пользователей!'
    else:
        message_text = 'Упс, кажется на текущий момент нет доступных курсов.'
    builder.adjust(1)

    try:
        await message.message.edit_text(message_text, reply_markup=builder.as_markup())
    except:
        await message.answer(message_text, reply_markup=builder.as_markup())


@router.message(Command("contact_us")) 
async def contact_us(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    bot_settings = await db_requests.get_bot_settings()
    if bot_settings.author_telegram:
        builder.button(text='Telegram', url=bot_settings.author_telegram)
    if bot_settings.author_instagram:
        builder.button(text='Instagram', url=bot_settings.author_instagram)
    if bot_settings.author_vk:
        builder.button(text='VK', url=bot_settings.author_vk)
    if bot_settings.author_telegram_public:
        builder.button(text='Группа в Telegram', url=bot_settings.author_telegram_public)
    if bot_settings.author_vk_public:
        builder.button(text='Группа в VK', url=bot_settings.author_vk_public)
    builder.adjust(1)
    if bot_settings.author_phone_number:
        message_text = f'Вы можете связаться со мной по телефону {bot_settings.author_phone_number} или по одному из каналов ниже.'
    else:
        if bot_settings.author_telegram or bot_settings.author_instagram or bot_settings.author_vk or bot_settings.author_telegram_public or bot_settings.author_vk_public:
            message_text = f'Вы можете связаться со мной по одному из каналов ниже.'
        else:
            message_text = f'⛔️ Контактные данные не внесены!'
    await message.answer(message_text, reply_markup=builder.as_markup())
    
    