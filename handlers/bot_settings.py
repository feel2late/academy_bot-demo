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
from states.add_new_course import AddCourse, AddModule, AddLesson
from states.send_message_to_all_users import SendMessageToAllUsers
from states.state_bot_settings import SetAuthorContact, SetWelcomeMessage, SetWelcomeVideo
from states.set_social_media import SetSocialMedia

from aiogram.filters import StateFilter


router = Router()  

@router.callback_query(F.data == "bot_settings")
async def admin_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    builder.button(text='🙋🏼‍♀️ Приветственное сообщение', callback_data='set_welcome_message')
    builder.button(text='🎥 Приветственное видео', callback_data='set_welcome_video')
    builder.button(text='📧 Контакты автора / соц.сети', callback_data='author_contacts')
    builder.button(text='🔙 Админ меню', callback_data='admin_menu')
    builder.adjust(1)
    message_text = 'Вы в админ меню.'
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.callback_query(F.data == "set_welcome_message")
async def set_welcome_message(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SetWelcomeMessage.text)
    builder = InlineKeyboardBuilder()
    builder.button(text='❌ Отмена', callback_data='bot_settings')
    message_text = ('Пришлите приветственное сообщение, которое будет отображаться пользователям при первом запуске бота.\n\n'
                    'Посмотреть как бот встречает новых пользователей вы можете отправив команду /start')
    set_welcome_message_msg = await callback.message.edit_text(message_text, reply_markup=builder.as_markup())
    await state.update_data(set_welcome_message_msg=set_welcome_message_msg)


@router.message(StateFilter(SetWelcomeMessage.text))
async def welcome_message_recieved(message: Message, state: FSMContext):
    fsmdata = await state.get_data()
    await fsmdata.get('set_welcome_message_msg').edit_reply_markup(answer_markup='')
    await state.set_state()
    await db_requests.set_welcome_message(message.text)
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 Назад', callback_data='bot_settings')
    message_text = f'✅ Установлено следующее приветственное сообщение:\n\n{message.text}'
    await message.answer(message_text, reply_markup=builder.as_markup())


@router.callback_query(F.data == "set_welcome_video")
async def set_welcome_video(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SetWelcomeVideo.video)
    builder = InlineKeyboardBuilder()
    builder.button(text='❌ Отмена', callback_data='bot_settings')
    message_text = ('Пришлите приветственное видео, которое будет отображаться пользователям при первом запуске бота.\n\n'
                    'Посмотреть как бот встречает новых пользователей вы можете отправив команду /start')
    set_welcome_video_msg = await callback.message.edit_text(message_text, reply_markup=builder.as_markup())
    await state.update_data(set_welcome_video_msg=set_welcome_video_msg)


@router.message(F.video, StateFilter(SetWelcomeVideo.video))
async def welcome_video_recieved(message: Message, state: FSMContext):
    fsmdata = await state.get_data()
    await fsmdata.get('set_welcome_video_msg').edit_reply_markup(answer_markup='')
    await state.set_state()
    await db_requests.set_welcome_video(message.video.file_id)
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 Назад', callback_data='bot_settings')
    message_text = f'✅ Приветственное видео загружено'
    await message.answer(message_text, reply_markup=builder.as_markup())
    
    
@router.callback_query(F.data == "author_contacts")
async def author_contact(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    bot_settings = await db_requests.get_bot_settings()
    builder = InlineKeyboardBuilder()
    builder.button(text='Номер телефона', callback_data='edit_social_media_phonenumber')
    builder.button(text='Личный Telegram', callback_data='edit_social_media_telegram')
    builder.button(text='Личный Instagram', callback_data='edit_social_media_instagram')
    builder.button(text='Личный VK', callback_data='edit_social_media_vk')
    builder.button(text='Группа в Telegram', callback_data='edit_social_media_telegram_group')
    builder.button(text='Группа в VK', callback_data='edit_social_media_vk_group')
    builder.button(text='🔙 Назад', callback_data='bot_settings')
    builder.adjust(1)
    message_text = (f'<b>Номер телефона</b>: {bot_settings.author_phone_number if bot_settings.author_phone_number else "❌"}\n'
                    f'<b>Telegram</b>: {bot_settings.author_telegram if bot_settings.author_telegram else "❌"}\n'
                    f'<b>Instagram</b>: {bot_settings.author_instagram if bot_settings.author_instagram else "❌"}\n'
                    f'<b>VK</b>: {bot_settings.author_vk if bot_settings.author_vk else "❌"}\n'
                    f'<b>Группа Telegram</b>: {bot_settings.author_telegram_public if bot_settings.author_telegram_public else "❌"}\n'
                    f'<b>Группа VK</b>: {bot_settings.author_vk_public if bot_settings.author_vk_public else "❌"}\n\n'
                    '<b>Выберите что хотите изменить:</b>')
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())
    

@router.callback_query(F.data.startswith("edit_social_media_"))
async def edit_social_media(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SetSocialMedia.value)
    social_media_type = callback.data[18:]
    social_media_name = {'phonenumber': 'номера телефона', 'telegram': 'личного telegram', 'instagram': 'личного instagram',
                         'vk': 'личного VK', 'telegram_group': 'группы в telegram', 'vk_group': 'группы в VK'}
    await state.update_data(social_media_type=social_media_type)
    message_text = f'Пришлите ссылку (или значение) для {social_media_name[social_media_type]}.'
    builder = InlineKeyboardBuilder()
    builder.button(text='🗑 Удалить текущее значение', callback_data=f'delete_social_media_{social_media_type}')
    builder.button(text='❌ Отмена', callback_data='author_contacts')
    builder.adjust(1)
    set_new_social_media_value_msg = await callback.message.edit_text(message_text, reply_markup=builder.as_markup())
    await state.update_data(set_new_social_media_value_msg=set_new_social_media_value_msg)


@router.message(StateFilter(SetSocialMedia.value))
async def social_media_value_recieved(message: Message, state: FSMContext):
    fsmdata = await state.get_data()
    await fsmdata.get('set_new_social_media_value_msg').edit_reply_markup(answer_markup='')
    social_media_type = fsmdata.get('social_media_type')
    social_media_name = {'phonenumber': 'номера телефона', 'telegram': 'личного telegram', 'instagram': 'личного instagram',
                         'vk': 'личного VK', 'telegram_group': 'группы в telegram', 'vk_group': 'группы в VK'}
    await state.set_state()
    await db_requests.edit_social_media(social_media_type, message.text)
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 Назад', callback_data='author_contacts')
    message_text = f'✅ Ссылка (значение) для {social_media_name[social_media_type]} изменена.'
    await message.answer(message_text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("delete_social_media_"), StateFilter(SetSocialMedia.value))
async def edit_social_media(callback: CallbackQuery, state: FSMContext):
    social_media_type = callback.data[20:]
    social_media_name = {'phonenumber': 'номера телефона', 'telegram': 'личного telegram', 'instagram': 'личного instagram',
                         'vk': 'личного VK', 'telegram_group': 'группы в telegram', 'vk_group': 'группы в VK'}
    await state.set_state()
    await db_requests.edit_social_media(social_media_type, None)
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 Назад', callback_data='author_contacts')
    message_text = f'✅ Ссылка (значение) для {social_media_name[social_media_type]} удалена.'
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.message(Command("request_admin_rights")) 
async def request_admin_rights(message: Message, state: FSMContext):
    if config.DEMO:
        await db_requests.add_admin(message.from_user.id, message.from_user.full_name)
        await message.answer('Вам выданы права администратора в демо режиме.\nТеперь вы можете открыть админ-меню бота и управлять курсом: /courses')
    else:
        await message.answer('Ваш запрос отправлен root администратору.')
        builder = InlineKeyboardBuilder()
        builder.button(text='✅ Одобрить', callback_data=f'give_admin_rights_{message.from_user.id}')
        message_for_root_admin = f'Получен запрос на админ права от пользователя {message.from_user.id} / {message.from_user.full_name}.'
        try:
            await bot.send_message(config.ROOT_ADMIN, message_for_root_admin, reply_markup=builder.as_markup())
        except:
            pass


@router.message(Command("delete_admins")) 
async def delete_admins(message: Message, state: FSMContext):
    if config.DEMO:
        await db_requests.delete_admins()
        await message.answer('Удалил всех админов из списка.')


@router.callback_query(F.data.startswith("give_admin_rights_"))
async def give_admin_rights_(callback: CallbackQuery, state: FSMContext):
    new_admin_telegram_id = callback.data[18:]
    user = await db_requests.get_user_by_telegram_id(new_admin_telegram_id)
    await db_requests.add_admin(new_admin_telegram_id, user.user_name)
    await bot.send_message(new_admin_telegram_id, '✅ Вам выданы права администратора.')
    await callback.message.edit_text('Права админа выданы')

