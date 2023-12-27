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
from states.add_description import AddModuleDescription
from states.set_module_duration import SetModuleDuration
from states.edit_name import EditModuleName
from aiogram.filters import StateFilter


router = Router()  


@router.callback_query(F.data.startswith("select_module_"))
async def select_module(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    module = await db_requests.get_module_by_id(callback.data[14:])
    builder = InlineKeyboardBuilder()
    lessons = await db_requests.get_lessons_by_module_id(module.id)
    user = await db_requests.get_user_by_telegram_id(callback.from_user.id)
    date_added_course = await db_requests.get_date_added_course_to_user(user.id, module.course.id)
    modules_in_course = await db_requests.get_course_modules(module.course.id)
    admins_ids = [admin.user_telegram_id for admin in await db_requests.get_admins()]
    offset = 0

    for module_in_course in modules_in_course:
        if module_in_course.title != module.title:
            offset += module_in_course.duration
        else:
            break
    if callback.from_user.id in admins_ids or callback.from_user.id == config.ROOT_ADMIN or (datetime.datetime.utcnow() - date_added_course).total_seconds() / 60 / 60 >= offset:
        for id, lesson in enumerate(lessons):
            builder.button(text=f'{id+1}. {lesson.title}', callback_data=f'select_lesson_{lesson.id}')
        if callback.from_user.id in admins_ids or callback.from_user.id == config.ROOT_ADMIN:
            builder.button(text='➕ Добавить урок', callback_data=f'add_new_lesson_to_{module.id}')
            builder.button(text='✏️ Изменить название модуля', callback_data=f'edit_module_name_{module.id}')
            if module.description:
                builder.button(text='✏️ Изменить описание', callback_data=f'add_module_description_{module.id}')
            else:
                builder.button(text='✏️ Добавить описание', callback_data=f'add_module_description_{module.id}')
            builder.button(text=f'⏱ Дедлайн ({module.duration} ч.)', callback_data=f'set_module_duration_{module.id}')
            builder.button(text='🗑 Удалить модуль', callback_data=f'm_delete_module_{module.id}')
        builder.button(text='🔙 Выбор модуля', callback_data=f'select_course_{module.course.id}')
        builder.adjust(1)
        message_text = f'👉🏻 Вы выбрали модуль <b>{module.title}</b> в курсе <b>{module.course.title}</b>.\n\n'
        if module.description:
            message_text += f'{module.description}\n\n'
        message_text += 'Выберите урок.'
    else:
        opened_date = date_added_course + datetime.timedelta(hours=offset+3)
        message_text = f'Упс! 🫣\nМодуль {module.title} вам ещё не доступен. Он откроется в <b>{datetime.datetime.strftime(opened_date, "%H:%M %d.%m.%y")} МСК.</b>'
        builder.button(text='🔙 Выбор модуля', callback_data=f'select_course_{module.course.id}')
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("edit_module_name_"))
async def edit_module_name(callback: CallbackQuery, state: FSMContext):
    module = await db_requests.get_module_by_id(callback.data[17:])
    await state.update_data(module=module)
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 К модулю', callback_data=f'select_module_{module.id}')
    message_text = (f'Текущее название модуля: <b>{module.title}</b>\n\n'
                    'Пришлите новое название или вернитесь к модулю.')
    await state.set_state(EditModuleName.waiting_for_text)
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.message(F.text, StateFilter(EditModuleName.waiting_for_text))
async def new_module_name_recieved(message: Message, state: FSMContext):
    fsmdata = await state.get_data()
    module = fsmdata.get('module')
    upload_status = await db_requests.edit_module_name(module.id, message.text)
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 К модулю', callback_data=f'select_module_{module.id}')
    if upload_status:
        await message.answer(f'✅ Изменил название модуля', reply_markup=builder.as_markup())
    else:
        await message.answer(f'❌ Ошибка изменения названия модуля в базе данных.\n\nСвяжитесь с разработчиком.', reply_markup=builder.as_markup())
    await state.clear()


@router.callback_query(F.data.startswith("add_module_description_"))
async def add_module_description(callback: CallbackQuery, state: FSMContext):
    module = await db_requests.get_module_by_id(callback.data[23:])
    await state.update_data(module=module)
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 К модулю', callback_data=f'select_module_{module.id}')
    if module.description:
        message_text = (f'Текущее описание для урока <b>{module.title}</b>:\n\n'
                        f'"{module.description}"\n\n'
                        'Пришлите новое описание или вернитесь к модулю.')
    else:
        message_text = 'Пришлите новое описание к модулю.'
    await state.set_state(AddModuleDescription.waiting_for_text)
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.message(F.text, StateFilter(AddModuleDescription.waiting_for_text))
async def lesson_resources_link_recieved(message: Message, state: FSMContext):
    fsmdata = await state.get_data()
    module = fsmdata.get('module')
    if len(message.text) < 2500:
        description_text = message.text
    else:
        builder = InlineKeyboardBuilder()
        builder.button(text='🔙 К модулю', callback_data=f'select_module_{module.id}')
        await message.answer('Описание к уроку слишком длинное. Постарайтесь уместить его в 1000 символов.\n\nДля подсчёта количества символов можно использовать https://pr-cy.ru/textlength/', reply_markup=builder.as_markup())
        return
    
    upload_status = await db_requests.add_description_for_module(module.id, description_text)
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 К модулю', callback_data=f'select_module_{module.id}')
    if upload_status:
        await message.answer(f'✅ Добавил описание к модулю.', reply_markup=builder.as_markup())
    else:
        await message.answer(f'❌ Ошибка добавления описания в базу данных.\n\nСвяжитесь с разработчиком.', reply_markup=builder.as_markup())
    await state.clear()


@router.callback_query(F.data.startswith("set_module_duration_"))
async def set_module_offset(callback: CallbackQuery, state: FSMContext):
    module = await db_requests.get_module_by_id(callback.data[20:])
    await state.update_data(module=module)
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 К модулю', callback_data=f'select_module_{module.id}')
    if module.duration != 0:
        message_text = (f'Текущая продолжительность модуля <b>{module.duration}</b> часов.\n\n'
                        'Пришлите новую продолжительность <b>в часах</b> или вернитесь к модулю.')
    else:
        message_text = 'Пришлите новую продолжительность модуля <b>в часах</b>.'
    await state.set_state(SetModuleDuration.waiting_for_new_time)
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.message(F.text, StateFilter(SetModuleDuration.waiting_for_new_time))
async def module_duration_recieved(message: Message, state: FSMContext):
    fsmdata = await state.get_data()
    module = fsmdata.get('module')
    if message.text.isdigit():
        duration = message.text
    else:
        builder = InlineKeyboardBuilder()
        builder.button(text='🔙 К модулю', callback_data=f'select_module_{module.id}')
        await message.answer('Продолжительность модуля должна быть указана в часах. Пожалуйста, пришлите количество часов целым числом.', reply_markup=builder.as_markup())
        return
    
    upload_status = await db_requests.set_module_duration(module.id, duration)
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 К модулю', callback_data=f'select_module_{module.id}')
    if upload_status:
        await message.answer(f'✅ Добавил продолжительность модуля.', reply_markup=builder.as_markup())
    else:
        await message.answer(f'❌ Ошибка добавления продолжительности модуля в базу данных.\n\nСвяжитесь с разработчиком.', reply_markup=builder.as_markup())
    await state.clear()
