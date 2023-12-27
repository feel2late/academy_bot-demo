from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.filters.command import Command
from aiogram import F
import db_requests
from aiogram import Router
from aiogram.fsm.context import FSMContext
import datetime
from bot_init import bot
import config
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from handlers.menu import courses
from handlers.course import check_course_availability
import asyncio



router = Router()  


@router.message(Command('start'))
async def start(message: types.Message, state: FSMContext):
    user = await db_requests.get_user_by_telegram_id(message.from_user.id)
    bot_settings = await db_requests.get_bot_settings()
    admins = await db_requests.get_admins()
    if not user:
        user_id = await db_requests.add_new_user(message.from_user.id, message.from_user.full_name, datetime.datetime.utcnow())
        if not user_id:
            await message.answer('Ошибка регистрации. Информация уже отправлена администратору. Пожалуйста, попробуйте позже.')
            try:
                await bot.send_message(config.ROOT_ADMIN, 'Ошибка регистрации пользователя.')
            except:
                pass
            for admin in admins:
                try:
                    await bot.send_message(admin.user_telegram_id, 'Возникла ошибка регистрации нового пользователя. Пожалуйста, свяжитесь с разработчиком.')
                except:
                    pass # ничего не нужно делать, т.к. админ скорее всего заблокировал бота
            return
    if bot_settings:
        if bot_settings.welcome_message:
            await message.answer(bot_settings.welcome_message)
        else:
            await message.answer(config.WELCOME_MESSAGE_EXAMPLE)
    else:
        await message.answer('Проинициализируйте настройки /initialization')
    if bot_settings.welcome_video_id:
        await message.answer_video(bot_settings.welcome_video_id)
    await courses(message, state)


@router.message(F.new_chat_members)
async def add_bot_to_chat(message: types.Message, state: FSMContext):
    bot_obj = await bot.get_me()
    builder = InlineKeyboardBuilder()
    admins_ids = [admin.user_telegram_id for admin in await db_requests.get_admins()]

    for chat_member in message.new_chat_members:
        if chat_member.id == bot_obj.id:
            if message.from_user.id not in admins_ids:
                await message.answer('Только мой администратор может добавлять меня в группы. Пока 👋')
                await bot.leave_chat(message.chat.id)
            else:          
                message_text = ('Привет! 👋\n'
                                'Чтобы я мог добавить ссылку на этот чат в курс, дайте мне права администратора в этой группе и нажмите кнопку ниже.')
                builder.button(text='🔄 Проверить права администратора', callback_data=f'check_bot_for_admin')
                await message.answer(message_text, reply_markup=builder.as_markup())
        else:
            user = await db_requests.get_user_by_telegram_id(chat_member.id)
            course = await db_requests.get_course_by_chat_id(message.chat.id)
            if await check_course_availability(user.id, course.id) or chat_member.id in admins_ids:
                message_text = (f'{chat_member.full_name}, добро пожаловать в чат учеников курса <b>"{course.title}"</b>!\n\n'
                                'Здесь вы можете задавать вопросы, делиться впечатлениями и переживаниями. А другие ученики и автор курса помогут и поддержут вас 🤗')
                await message.answer(message_text)
                return
            message_text = f'{chat_member.full_name} простите, чтобы находиться в этом чате, вы должны купить курс.\nВсего доброго 👋'
            await message.answer(message_text)
            await asyncio.sleep(3)
            await bot.ban_chat_member(message.chat.id, chat_member.id)
            try:
                await bot.unban_chat_member(message.chat.id, chat_member.id)
            except:
                pass

@router.callback_query(F.data == "check_bot_for_admin")
async def check_bot_for_admin(callback: CallbackQuery, state: FSMContext):
    chat_admins = await bot.get_chat_administrators(callback.message.chat.id)
    builder = InlineKeyboardBuilder()
    bot_admin = False
    for admin in chat_admins:
        if admin.user.id == bot.id:
            bot_admin = True
            await callback.message.edit_reply_markup(answer_reply_markup='')
            courses = await db_requests.get_all_courses(for_admin=True)
            message_text = ('Выберите курс, к которому нужно привязать этот чат.\n\n'
                            '⚠️ Если к курсу уже привязан другой чат, я перепривяжу и добавлю к курсу ЭТОТ чат.\n\n'
                            'Не удаляйте меня из группы, я буду проверять, чтобы у вступивших в группу был куплен этот курс. Если нет, я буду удалять его из группы.')
            for course in courses:
                builder.button(text=course.title, callback_data=f'set_chat_link_for_course_{course.id}')
            builder.adjust(1)
            await callback.message.edit_text(message_text, reply_markup=builder.as_markup())
    if not bot_admin:
        message_text = 'У меня всё ещё нет прав администратора.'
        await callback.answer(message_text, show_alert=True)
        return


@router.callback_query(F.data.startswith("set_chat_link_for_course_"))
async def set_chat_link_for_course(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(answer_reply_markup='')
    course = await db_requests.get_course_by_id(callback.data[25:])
    invite_link: str = await bot.export_chat_invite_link(callback.message.chat.id)
    invite_id = invite_link.split('+')
    await db_requests.set_course_chat_link(course.id, invite_id[1], callback.message.chat.id)
    message_text = ('🎊 Поздравляю! Теперь в курсе есть ссылка на эту группу.\n\n'
                    'Ваши ученики смогут переходить сюда по кнопке "💬 Чат курса" в меню курса.\n\n'
                    f'Или просто перешлите им эту ссылку: {invite_link}\n'
                    '⚠️ Не удаляйте меня из группы! Иначе ссылка перестанет работать.')
    await callback.message.answer(message_text)


@router.message(Command('my_id'))
async def get_chat_id(message: Message):
    await message.answer(f'You telegram id: {message.from_user.id}')


@router.message(Command('group_id'))
async def get_chat_id(message: Message):
    await message.answer(f'Group id: {message.chat.id}')