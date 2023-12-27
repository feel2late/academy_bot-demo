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

from aiogram.filters import StateFilter


router = Router()  

@router.callback_query(F.data == "admin_menu")
async def admin_menu(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text='👥 Список пользователей', callback_data='get_all_users')
    builder.button(text='📊 Список заказов', callback_data='get_all_orders')
    builder.button(text='⚙️ Настройки бота', callback_data='bot_settings')
    builder.button(text='🔙 Список курсов', callback_data='courses')
    builder.adjust(1)
    message_text = 'Вы в админ меню.'
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.callback_query(F.data == "add_new_course")
async def add_new_course(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddCourse.title)
    builder = InlineKeyboardBuilder()
    builder.button(text='❌ Отмена', callback_data='cancel_from_')
    message_text = 'Пожалуйста, пришлите название для нового курса.'
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.message(StateFilter(AddCourse.title))
async def course_title_recieved(message: Message, state: FSMContext):
    if len(message.text) < 50:
        course_title = message.text
    else:
        builder = InlineKeyboardBuilder()
        builder.button(text='❌ Отмена', callback_data='cancel_from_')
        await message.answer('Название курса слишком длинное. Попробуйте его укоротить.', reply_markup=builder.as_markup())
        return
    await state.set_state()
    course_id = await db_requests.add_new_course(course_title)
    if course_id:
        builder = InlineKeyboardBuilder()
        builder.button(text='➕ Добавить модуль на курс', callback_data=f'add_new_module_to_{course_id}')
        builder.button(text='🔙 Выбор курса', callback_data='courses')
        builder.adjust(1)
        await message.answer('✅ Курс успешно добавлен', reply_markup=builder.as_markup())
    else:
        await message.answer('❌ Ошибка добавления курса. Обратитесь к разработчику.')


@router.callback_query(F.data.startswith("add_new_module_to_"))
async def add_new_course(callback: CallbackQuery, state: FSMContext):
    course_id = callback.data[18:]
    course = await db_requests.get_course_by_id(course_id)
    await state.update_data(course_id=course_id)
    await state.set_state(AddModule.title)
    builder = InlineKeyboardBuilder()
    builder.button(text='❌ Отмена', callback_data=f'select_course_{course.id}')
    message_text = (f'Вы добавляете новый модуль в курс <b>{course.title}</b>\n\n'
                    'Пожалуйста, пришлите название для модуля.')
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.message(StateFilter(AddModule.title))
async def course_title_recieved(message: Message, state: FSMContext):
    if len(message.text) < 80:
        module_title = message.text
    else:
        builder = InlineKeyboardBuilder()
        builder.button(text='❌ Отмена', callback_data='cancel_from_')
        await message.answer('Название модуля слишком длинное. Попробуйте его укоротить.', reply_markup=builder.as_markup())
        return
    await state.set_state()
    fsmdata = await state.get_data()
    course_id = fsmdata.get('course_id')
    module_id = await db_requests.add_new_module(course_id, module_title)
    if module_id:
        builder = InlineKeyboardBuilder()
        builder.button(text='➕ Добавить первый урок в модуль', callback_data=f'add_new_lesson_to_{module_id}')
        builder.button(text='🔙 Назад к курсу', callback_data=f'select_course_{course_id}')
        builder.adjust(1)
        await message.answer('✅ Модуль успешно добавлен', reply_markup=builder.as_markup())
    else:
        await message.answer('❌ Ошибка добавления курса. Обратитесь к разработчику.')


@router.callback_query(F.data.startswith("add_new_lesson_to_"))
async def add_new_lesson(callback: CallbackQuery, state: FSMContext):
    module_id = callback.data[18:]
    module = await db_requests.get_module_by_id(module_id)
    await state.update_data(module_id=module_id)
    await state.set_state(AddLesson.title)
    builder = InlineKeyboardBuilder()
    builder.button(text='❌ Отмена', callback_data=f'select_module_{module_id}')
    message_text = (f'Вы добавляете новый урок в модуль <b>{module.title}</b>\n\n'
                    'Пожалуйста, пришлите название для урока.')
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.message(StateFilter(AddLesson.title))
async def lesson_title_recieved(message: Message, state: FSMContext):
    if len(message.text) < 50:
        lesson_title = message.text
    else:
        builder = InlineKeyboardBuilder()
        builder.button(text='❌ Отмена', callback_data='cancel_from_')
        await message.answer('Название урока слишком длинное. Попробуйте его укоротить.', reply_markup=builder.as_markup())
        return
    await state.set_state()
    fsmdata = await state.get_data()
    module_id = fsmdata.get('module_id')
    lesson_id = await db_requests.add_new_lesson(module_id, lesson_title)
    if module_id:
        builder = InlineKeyboardBuilder()
        builder.button(text='🔙 Назад к модулю', callback_data=f'select_module_{module_id}')
        builder.adjust(1)
        await message.answer('✅ Урок успешно добавлен', reply_markup=builder.as_markup())
    else:
        await message.answer('❌ Ошибка добавления урока. Обратитесь к разработчику.')


@router.callback_query(F.data.startswith("m_delete_"))
async def delete(callback: CallbackQuery, state: FSMContext):
    type = callback.data[9:15]
    item_id = callback.data[16:]
    translate = {'course': 'курс', 'module': 'модуль', 'lesson': 'урок'}
    if type == 'course':
        item = await db_requests.get_course_by_id(item_id)
    elif type == 'module':
        item = await db_requests.get_module_by_id(item_id)
    elif type == 'lesson':
        item = await db_requests.get_lesson_by_id(item_id)
    
    await state.update_data(type=type, item_id=item_id)
    message_text = f'Вы уверены, что хотите удалить {translate.get(type)} <b>"{item.title}"</b>?'
    builder = InlineKeyboardBuilder()
    builder.button(text='✅ Да', callback_data='confirm_delete')
    builder.button(text='❌ НЕТ!', callback_data=f'select_{type}_{item_id}')
    builder.adjust(1)
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())
    

@router.callback_query(F.data == "confirm_delete")
async def confirm_delete(callback: CallbackQuery, state: FSMContext):
    fsmdata = await state.get_data()
    type = fsmdata.get('type')
    item_id = fsmdata.get('item_id')
    builder = InlineKeyboardBuilder()
    
    if type == 'course':
        builder.button(text='🔙 Выбор курса', callback_data='courses')
        result = await db_requests.delete_course(item_id)
    elif type == 'module':
        module = await db_requests.get_module_by_id(item_id)
        course = await db_requests.get_course_by_id(module.course.id)
        builder.button(text='🔙 Выбор модуля', callback_data=f'select_course_{course.id}')
        result = await db_requests.delete_module(item_id)
    elif type == 'lesson':
        lesson = await db_requests.get_lesson_by_id(item_id)
        module = await db_requests.get_module_by_id(lesson.module.id)
        builder.button(text='🔙 Выбор урока', callback_data=f'select_module_{module.id}')
        result = await db_requests.delete_lesson(item_id)

    if result:
        await callback.message.edit_text('✅ Удаление прошло успешно.', reply_markup=builder.as_markup())
    else:
        await callback.message.edit_text('❌ Ошибка удаления. Обратитесь к разработчику.', reply_markup=builder.as_markup())
        
    
@router.callback_query(F.data == "get_all_users")
async def get_all_users(callback: CallbackQuery, state: FSMContext):
    all_users = await db_requests.get_all_users()
    message_text = 'Список всех зарегистрированных пользователей:\n\n'
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 Админ меню', callback_data='admin_menu')
    
    for id, user in enumerate(all_users):
        message_text += f'{id+1}) {user.user_name}\n'
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.callback_query(F.data == "get_all_orders")
async def get_all_orders(callback: CallbackQuery, state: FSMContext):
    orders = await db_requests.get_all_orders()
    message_text = 'Список всех созданных заказов:\n\n'
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 Админ меню', callback_data='admin_menu')
    
    for id, order in enumerate(orders):
        message_text += (f'{id+1}) {order.user.user_name} заказал "{order.course.title}" {order.order_date}. Оплата: {"✅" if order.paid else "❌"}\n\n')

    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("admin_send_message_to_all_users_course_"))
async def admin_send_message_to_all_users(callback: CallbackQuery, state: FSMContext):
    course = await db_requests.get_course_by_id(callback.data[39:])
    await state.update_data(course=course)
    await state.set_state(SendMessageToAllUsers.text)
    message_text = 'Пришлите текст, который вы хотите разослать ученикам текущего курса.'
    builder = InlineKeyboardBuilder()
    builder.button(text='❌ Отмена', callback_data='cancel_from_')
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.message(StateFilter(SendMessageToAllUsers.text))
async def text_message_recieved(message: Message, state: FSMContext):
    await state.update_data(message_text=message.text)
    builder = InlineKeyboardBuilder()
    builder.button(text='✅ Отправить', callback_data='confirm_send_message_to_users')
    builder.button(text='❌ Отмена', callback_data='cancel_from_')
    builder.adjust(1)
    await message.answer('Проверьте текст.\n\nЕсли всё верно, нажмите "✅ Отправить"\nЕсли передумали, нажмите "❌ Отмена"\nЕсли хотите что-то исправить, просто пришлите мне новый вариант')
    await message.answer(message.text, reply_markup=builder.as_markup())


@router.callback_query(F.data == 'confirm_send_message_to_users', StateFilter(SendMessageToAllUsers.text))
async def confirm_send_message_to_users(callback: CallbackQuery, state: FSMContext):
    await state.set_state()
    await callback.message.delete()
    fsmdata = await state.get_data()
    course = fsmdata.get('course')
    message_text = fsmdata.get('message_text')
    users_count = 0
    for user in course.users:
        user = await db_requests.get_user_by_id(user.user_id)
        try:
            await bot.send_message(user.user_telegram_id, message_text)
            users_count += 1
        except:
            pass
    await callback.message.answer(f'{users_count} учеников получили сообщение.')


'''@router.message(F.video)
async def lesson_additional_video_recieved(message: Message):
    print(message.video.file_id)'''


@router.message(Command("initialization")) 
async def initialization(message: Message, state: FSMContext):
    bot_settings = await db_requests.get_bot_settings()
    if not bot_settings:
        await db_requests.init_bot_settings(message.from_user.id, message.from_user.full_name)
        await message.answer('Настройки бота инициализированы.\nВы назначены первым администратором бота.')
        await message.answer(config.welcome_message_example)