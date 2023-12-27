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
from aiogram.filters import StateFilter
from states.add_video_to_lesson import AddVideo
from states.add_additional_meterials import AddAdditionalMaterials
from states.add_description import AddLessonDescription
from states.delete_media_from_lesson import DeleteLessonMedia
from states.add_homework import AddHomework, AddTeachersComment
from states.add_user_homework import AddUserHomework
from states.edit_homework import EditHomework
from states.edit_name import EditLessonName

router = Router()  


@router.callback_query(F.data.startswith("select_lesson_"))
async def select_lesson(callback: CallbackQuery, state: FSMContext):
    admins_ids = [admin.user_telegram_id for admin in await db_requests.get_admins()]
    if not callback.data[14:].isnumeric():
        await callback.answer('Запустите курс заново из меню', show_alert=True)
        return
    if await state.get_state() == 'AddUserHomework:waiting_for_media':
        fsmdata = await state.get_data()
        user_homework = fsmdata.get('user_homework')
        
        user = await db_requests.get_user_by_telegram_id(callback.from_user.id)
        message_text = f'📚 <b>Ученик {user.user_name} прислал домашнее задание на проверку.</b>'
        builder = InlineKeyboardBuilder()
        builder.button(text='📖 Проверить домашнее задание', callback_data=f'check_user_homework_{user_homework.id}')
        for admin in admins_ids:
            await bot.send_message(admin, message_text, reply_markup=builder.as_markup())

    await state.clear()
    lesson = await db_requests.get_lesson_by_id(callback.data[14:])
    lesson_media = await db_requests.get_lesson_media(lesson.id)
    builder = InlineKeyboardBuilder()
    message_text = (f'👉🏻 Вы выбрали урок <b>{lesson.title}</b> в модуле <b>{lesson.module.title}</b>.\n\n')
    if lesson.description:
        message_text += lesson.description

    builder.button(text=f'👀 Смотреть видео ({len(lesson_media)})', callback_data=f'watch_lesson_{lesson.id}')
    builder.button(text='📖 Домашнее задание', callback_data=f'homework_lesson_{lesson.id}')
    if lesson.resources:
        builder.button(text='🔍 Дополнительные материалы', url=lesson.resources)
    else:
        builder.button(text='🔍 Дополнительные материалы', callback_data=f'additional_materials_{lesson.id}')
    if callback.from_user.id in admins_ids or callback.from_user.id == config.ROOT_ADMIN:
        builder.button(text='➕ Добавить видео', callback_data=f'add_media_to_lesson_{lesson.id}')
        builder.button(text='🗑 Удалить видео', callback_data=f'delete_media_from_lesson_{lesson.id}')
        builder.button(text='✏️ Изменить название урока', callback_data=f'edit_lesson_name_{lesson.id}')
        if lesson.description:
            builder.button(text='✏️ Изменить описание', callback_data=f'add_lesson_description_{lesson.id}')
        else:
            builder.button(text='✏️ Добавить описание', callback_data=f'add_lesson_description_{lesson.id}')
        builder.button(text='➕ Добавить доп. материалы', callback_data=f'add_resources_{lesson.id}')
        builder.button(text='🗑 Удалить доп. материалы', callback_data=f'delete_resources_{lesson.id}')
        builder.button(text='🗑 Удалить урок', callback_data=f'm_delete_lesson_{lesson.id}')
    builder.button(text='🔙 Выбор урока', callback_data=f'select_module_{lesson.module.id}')
    builder.adjust(1)
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("edit_lesson_name_"))
async def edit_lesson_name(callback: CallbackQuery, state: FSMContext):
    lesson = await db_requests.get_lesson_by_id(callback.data[17:])
    await state.update_data(lesson=lesson)
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{lesson.id}')
    message_text = (f'Текущее название урока: <b>{lesson.title}</b>\n\n'
                    'Пришлите новое название или вернитесь к уроку.')
    await state.set_state(EditLessonName.waiting_for_text)
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.message(F.text, StateFilter(EditLessonName.waiting_for_text))
async def new_lesson_name_recieved(message: Message, state: FSMContext):
    fsmdata = await state.get_data()
    lesson = fsmdata.get('lesson')
    upload_status = await db_requests.edit_lesson_name(lesson.id, message.text)
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{lesson.id}')
    if upload_status:
        await message.answer(f'✅ Изменил название урока', reply_markup=builder.as_markup())
    else:
        await message.answer(f'❌ Ошибка изменения названия урока в базе данных.\n\nСвяжитесь с разработчиком.', reply_markup=builder.as_markup())
    await state.clear()


@router.callback_query(F.data.startswith("check_user_homework_"))
async def check_user_homework(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(answer_reply_markup='')
    user_homework = await db_requests.get_user_homework_by_id(callback.data[20:])
    
    user_homework_media_for_send = []
    for media in user_homework.media:
        if media.video_id:
            user_homework_media_for_send.append(types.InputMediaVideo(media=media.video_id))
        elif media.photo_id:
            user_homework_media_for_send.append(types.InputMediaPhoto(media=media.photo_id))
        elif media.text:
            await callback.message.answer(media.text)
    if len(user_homework_media_for_send) > 0:
        await bot.send_media_group(callback.from_user.id, user_homework_media_for_send)
    message_text = 'Поставьте оценку выполненному домашнему заданию ученика'
    builder = InlineKeyboardBuilder()
    builder.button(text='⭐️', callback_data=f'grade_homework_{user_homework.id}.rate_1')
    builder.button(text='⭐️⭐️', callback_data=f'grade_homework_{user_homework.id}.rate_2')
    builder.button(text='⭐️⭐️⭐️', callback_data=f'grade_homework_{user_homework.id}.rate_3')
    builder.button(text='⭐️⭐️⭐️⭐️', callback_data=f'grade_homework_{user_homework.id}.rate_4')
    builder.button(text='⭐️⭐️⭐️⭐️⭐️', callback_data=f'grade_homework_{user_homework.id}.rate_5')
    builder.adjust(1)
    await callback.message.answer(message_text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("grade_homework_"))
async def grade_homework(callback: CallbackQuery, state: FSMContext):
    callback_message = callback.data.split('.')
    user_homework = await db_requests.get_user_homework_by_id(callback_message[0][15:])
    rate = int(callback_message[1][5:])
    user = await db_requests.get_user_by_id(user_homework.user_id)
    lesson = await db_requests.get_lesson_by_id(user_homework.lesson_id)
    await db_requests.rate_user_homework(user_homework.id, rate)
    await state.update_data(user_homework=user_homework)
    await state.set_state(AddTeachersComment.waiting_for_text)
    builder = InlineKeyboardBuilder()
    builder.button(text='❌ Не оставлять комментарий', callback_data=f'cancel_from_')  
    try:
        user_message_text = f'⚠️ Автор курса поставил оценку <b>{rate}</b> вашему домашнему заданию к уроку "{lesson.title}"!'
        await bot.send_message(user.user_telegram_id, user_message_text)
    except:
        pass
    
    await callback.message.edit_text(f'✅ Вы оценили домашнее задание ученика {user.user_name} к уроку {lesson.title} на {rate}.\n\nПришлите ваш комментарий к работе ученика.', reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("homework_lesson_"))
async def homework_lesson(callback: CallbackQuery, state: FSMContext):
    homework = await db_requests.get_lesson_homework(callback.data[16:])
    admins_ids = [admin.user_telegram_id for admin in await db_requests.get_admins()]
    if not homework:
        if callback.from_user.id in admins_ids:
            await state.set_state(AddHomework.waiting_for_text)
            await state.update_data(lesson_id=callback.data[16:])
            message_text = 'Для этого урока нет домашнего задания. Пришлите текст домашнего задания <i>одним сообщением</i>.'
            builder = InlineKeyboardBuilder()
            builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{callback.data[16:]}')
            await callback.message.edit_text(message_text, reply_markup=builder.as_markup())
            return
        else:
            await callback.answer('🤷‍♀️ К этому уроку нет домашнего задания', show_alert=True)
            return
    else:
        user = await db_requests.get_user_by_telegram_id(callback.from_user.id)
        user_homework = await db_requests.get_user_homework(user.id, callback.data[16:])
        message_text = f'Домашнее задание к уроку <b>{homework.lesson.title}</b>:\n\n' + homework.content
        if hasattr(user_homework, 'grade') and user_homework.grade:
            message_text += f'\n\n🌟 Вы получили за это задание оценку <b>{user_homework.grade}</b>.'
        if hasattr(user_homework, 'teachers_comment') and user_homework.teachers_comment:
            message_text += f'\n\n📋 Комментарий преподавателя к вашему домашнему заданию:\n<b>{user_homework.teachers_comment}</b>.'
        builder = InlineKeyboardBuilder()
        if callback.from_user.id in admins_ids:
            builder.button(text='✏️ Изменить текст задания', callback_data=f'change_homework_{homework.id}')    
            if homework.user_homework_required:
                builder.button(text='✅ Требуется сдача задания', callback_data=f'edit_user_homework_required_{homework.id}')
            else:
                builder.button(text='❌ Не требуется сдача задания', callback_data=f'edit_user_homework_required_{homework.id}')
        if homework.user_homework_required:
            builder.button(text='📚 Отправить решение на проверку', callback_data=f'upload_user_homework_{homework.lesson.id}')
        builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{callback.data[16:]}')
        builder.adjust(1)
        await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("edit_user_homework_required_"))
async def homework_lesson(callback: CallbackQuery, state: FSMContext):
    homework = await db_requests.get_homework_by_id(callback.data[28:])
    await db_requests.edit_user_homework_required(homework.id)
    admins_ids = [admin.user_telegram_id for admin in await db_requests.get_admins()]
    builder = InlineKeyboardBuilder()
    if callback.from_user.id in admins_ids:
        builder.button(text='✏️ Изменить текст задания', callback_data=f'change_homework_{homework.id}')    
        if homework.user_homework_required:
            builder.button(text='✅ Требуется сдача задания', callback_data=f'edit_user_homework_required_{homework.id}')
        else:
            builder.button(text='❌ Не требуется сдача задания', callback_data=f'edit_user_homework_required_{homework.id}')
    if homework.user_homework_required:
        builder.button(text='📚 Отправить решение на проверку', callback_data=f'upload_user_homework_{homework.lesson.id}')
    builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{homework.lesson.id}')
    builder.adjust(1)
    await callback.message.edit_reply_markup(reply_markup=builder.as_markup())


@router.message(F.text, StateFilter(AddHomework.waiting_for_text))
async def homework_text_recieved(message: Message, state: FSMContext):
    fsmdata = await state.get_data()
    lesson_id = fsmdata.get('lesson_id')
    upload_status = await db_requests.add_homework_content(lesson_id, message.text)
    await state.set_state()
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{lesson_id}')
    if upload_status:
        await message.answer(f'✅ Добавил домашнее задание (текст) к уроку', reply_markup=builder.as_markup())
    else:
        await message.answer(f'❌ Ошибка добавления задания (или его текста) в базу данных.\n\nСвяжитесь с разработчиком.', reply_markup=builder.as_markup())
    await state.clear()


@router.callback_query(F.data.startswith("add_media_to_lesson_"))
async def add_media_to_lesson(callback: CallbackQuery, state: FSMContext):
    lesson = await db_requests.get_lesson_by_id(callback.data[20:])
    await state.set_state(AddVideo.waiting_for_file)
    await state.update_data(lesson=lesson)
    message_text = ('Пришлите файлы в том порядке, в котором они должны будут отображаться ученику.\n'
                    'Вы можете добавить несколько файлов, просто пришлите мне их по очереди.\n\n'
                    '<b>Когда закончите - нажмите /stop_upload или "🔙 К уроку"</b>')
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{lesson.id}')
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.message(F.video, StateFilter(AddVideo.waiting_for_file))
async def lesson_video_recieved(message: Message, state: FSMContext):
    fsmdata = await state.get_data()
    lesson = fsmdata.get('lesson')
    media_name = message.video.file_name.split('.') # Загружаем название видео до точки, чтобы отсечь расширение файла
    upload_status = await db_requests.add_media_to_lesson(message.video.file_id, lesson.id, media_name[0])
    
    if upload_status:
        builder = InlineKeyboardBuilder()
        builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{lesson.id}')
        await message.answer(f'✅ Добавил видео <b>{media_name[0]}</b> к уроку.\n\nВы можете прислать ещё или вернуться к уроку.', reply_markup=builder.as_markup())
    else:
        await message.answer(f'❌ Ошибка добавления видео <b>{message.video.file_name}</b> в базу данных.\n\nСвяжитесь с разработчиком.')
    

@router.message(Command('stop_upload'), StateFilter(AddVideo.waiting_for_file))
async def stop_upload(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer('Ок, я сохранил видео для урока. Вернитесь к уроку через меню.')


@router.callback_query(F.data.startswith("upload_user_homework_"))
async def add_media_to_lesson(callback: CallbackQuery, state: FSMContext):
    user = await db_requests.get_user_by_telegram_id(callback.from_user.id)
    user_homework = await db_requests.get_user_homework(user.id, callback.data[21:])
    if not user_homework:
        user_homework = await db_requests.add_user_homework(user.id, callback.data[21:])
        if user_homework:
            await state.set_state(AddUserHomework.waiting_for_media)
            await state.update_data(user_homework=user_homework)
            message_text = ('Пришлите выполненое домашнее задание. Это может быть фото, видео или текст.\n\n'
                            'Все фото, видео и текстовые сообщения (не файлы или документы, а сообщения) что вы пришлёте, я добавлю в ваше домашнее задание.\n\n'
                            'Чтобы завершить загрузку вернитесь через кнопку "🔙 К уроку"')
            builder = InlineKeyboardBuilder()
            builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{callback.data[21:]}')
            await callback.message.edit_text(message_text, reply_markup=builder.as_markup())
    else:
        await state.set_state(AddUserHomework.waiting_for_media)
        await state.update_data(user_homework=user_homework)
        message_text = ('Пришлите выполненое домашнее задание. Это может быть фото, видео или текст.\n\n'
                        'Все фото, видео и текстовые сообщения (не файлы или документы, а сообщения) что вы пришлёте, я добавлю в ваше домашнее задание.\n\n'
                        'Чтобы завершить загрузку вернитесь через кнопку "🔙 К уроку"')
        builder = InlineKeyboardBuilder()
        builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{callback.data[21:]}')
        await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.message(F.video, StateFilter(AddUserHomework.waiting_for_media))
async def user_homework_video_recieved(message: Message, state: FSMContext):
    fsmdata = await state.get_data()
    user_homework = fsmdata.get('user_homework')
    upload_status = await db_requests.add_user_homework_media(user_homework.id, video_id=message.video.file_id)
    if upload_status:
        builder = InlineKeyboardBuilder()
        builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{user_homework.lesson_id}')
        await message.answer(f'✅ Добавил видео к домашнему заданию.\n\nВы можете прислать ещё или завершить загрузку вернувшись к уроку.', reply_markup=builder.as_markup())
    else:
        builder = InlineKeyboardBuilder()
        builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{user_homework.lesson_id}')
        await message.answer(f'❌ Ошибка добавления видео в базу данных.\n\nСвяжитесь с автором курса.', reply_markup=builder.as_markup())


@router.message(F.photo, StateFilter(AddUserHomework.waiting_for_media))
async def user_homework_photo_recieved(message: Message, state: FSMContext):
    fsmdata = await state.get_data()
    user_homework = fsmdata.get('user_homework')
    upload_status = await db_requests.add_user_homework_media(user_homework.id, photo_id=message.photo[-1].file_id)
    if upload_status:
        builder = InlineKeyboardBuilder()
        builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{user_homework.lesson_id}')
        await message.answer(f'✅ Добавил фото к домашнему заданию.\n\nВы можете прислать ещё или завершить загрузку вернувшись к уроку.', reply_markup=builder.as_markup())
    else:
        builder = InlineKeyboardBuilder()
        builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{user_homework.lesson_id}')
        await message.answer(f'❌ Ошибка добавления фото в базу данных.\n\nСвяжитесь с автором курса.', reply_markup=builder.as_markup())

    
@router.message(F.text, StateFilter(AddUserHomework.waiting_for_media))
async def user_homework_text_recieved(message: Message, state: FSMContext):
    fsmdata = await state.get_data()
    user_homework = fsmdata.get('user_homework')
    upload_status = await db_requests.add_user_homework_media(user_homework.id, text=message.text)
    if upload_status:
        builder = InlineKeyboardBuilder()
        builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{user_homework.lesson_id}')
        await message.answer(f'✅ Добавил ваше сообщение к домашнему заданию.\n\nВы можете прислать ещё или завершить загрузку вернувшись к уроку.', reply_markup=builder.as_markup())
    else:
        builder = InlineKeyboardBuilder()
        builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{user_homework.lesson_id}')
        await message.answer(f'❌ Ошибка добавления сообщения в базу данных.\n\nСвяжитесь с автором курса.', reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("watch_lesson_"))
async def add_media_to_lesson(callback: CallbackQuery, state: FSMContext):
    lesson = await db_requests.get_lesson_by_id(callback.data[13:])
    lesson_media = await db_requests.get_lesson_media(lesson.id)
    
    if len(lesson_media) == 0:
        await callback.answer('Для этого урока пока нет видео 🤔', show_alert=True)
        return
    
    for media in lesson_media:
        await callback.message.answer_video(video=media.media_id, caption=media.media_name, protect_content=True)
    
    await callback.message.edit_reply_markup(answer_reply_markup='')
    message_text = 'Хотите вернуться назад к уроку или получить дополнительные материалы?'
    builder = InlineKeyboardBuilder()
    builder.button(text='🔍 Дополнительные материалы', callback_data=f'additional_materials_{lesson.id}')
    builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{lesson.id}')
    builder.adjust(1)
    await callback.message.answer(message_text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("add_resources_"))
async def add_resources_link(callback: CallbackQuery, state: FSMContext):
    lesson = await db_requests.get_lesson_by_id(callback.data[14:])
    await state.set_state(AddAdditionalMaterials.waiting_for_media)
    await state.update_data(lesson=lesson)
    message_text = ('Пришлите дополнительные материалы. Это могут быть видео, фото и текстовые сообщения.\nПо завершению добавления, нажмите "🔙 К уроку"')
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{lesson.id}')
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.message(F.text, StateFilter(AddAdditionalMaterials.waiting_for_media))
async def lesson_additional_text_recieved(message: Message, state: FSMContext):
    fsmdata = await state.get_data()
    lesson = fsmdata.get('lesson')
    upload_status = await db_requests.add_additional_materials(lesson.id, text=message.text)
    
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{lesson.id}')
    if upload_status:
        await message.answer(f'✅ Добавил текст в дополнительные материалы к уроку {lesson.title}.', reply_markup=builder.as_markup())
    else:
        await message.answer(f'❌ Ошибка добавления текста в базу данных.\n\nСвяжитесь с разработчиком.', reply_markup=builder.as_markup())
    


@router.message(F.video, StateFilter(AddAdditionalMaterials.waiting_for_media))
async def lesson_additional_video_recieved(message: Message, state: FSMContext):
    fsmdata = await state.get_data()
    lesson = fsmdata.get('lesson')
    upload_status = await db_requests.add_additional_materials(lesson.id, video_id=message.video.file_id)
    
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{lesson.id}')
    if upload_status:
        await message.answer(f'✅ Добавил видео в дополнительные материалы к уроку {lesson.title}.', reply_markup=builder.as_markup())
    else:
        await message.answer(f'❌ Ошибка добавления видео в базу данных.\n\nСвяжитесь с разработчиком.', reply_markup=builder.as_markup())
    


@router.message(F.photo, StateFilter(AddAdditionalMaterials.waiting_for_media))
async def lesson_additional_photo_recieved(message: Message, state: FSMContext):
    fsmdata = await state.get_data()
    lesson = fsmdata.get('lesson')
    upload_status = await db_requests.add_additional_materials(lesson.id, photo_id=message.photo[-1].file_id)
    
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{lesson.id}')
    if upload_status:
        await message.answer(f'✅ Добавил фото в дополнительные материалы к уроку {lesson.title}.', reply_markup=builder.as_markup())
    else:
        await message.answer(f'❌ Ошибка добавления фото в базу данных.\n\nСвяжитесь с разработчиком.', reply_markup=builder.as_markup())
    
    

@router.callback_query(F.data.startswith("additional_materials_"))
async def additional_materials(callback: CallbackQuery, state: FSMContext):
    lesson = await db_requests.get_lesson_by_id(callback.data[21:])
    
    if not lesson.additional_materials:
        await callback.answer('🙅‍♀️ Для данного урока нет дополнительных материалов.', show_alert=True)
        return
    await callback.message.delete()
    media_for_send = []
    for media in lesson.additional_materials:
        if media.video_id:
            media_for_send.append(types.InputMediaVideo(media=media.video_id))
        elif media.photo_id:
            media_for_send.append(types.InputMediaPhoto(media=media.photo_id))
        elif media.text:
            await callback.message.answer(media.text)
    if len(media_for_send) > 0:
        await bot.send_media_group(callback.from_user.id, media_for_send)
    message_text = 'Это все дополнительные материалы. Вернуться к уроку?'
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{lesson.id}')
    await callback.message.answer(message_text, reply_markup=builder.as_markup())
    

@router.callback_query(F.data.startswith("add_lesson_description_"))
async def add_lesson_description(callback: CallbackQuery, state: FSMContext):
    lesson = await db_requests.get_lesson_by_id(callback.data[23:])
    await state.update_data(lesson=lesson)
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{lesson.id}')
    if lesson.description:
        message_text = (f'Текущее описание для урока <b>{lesson.title}</b>:\n\n'
                        f'"{lesson.description}"\n\n'
                        'Пришлите новое описание или вернитесь к уроку.')
    else:
        message_text = 'Пришлите новое описание к уроку.'
    await state.set_state(AddLessonDescription.waiting_for_text)
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.message(F.text, StateFilter(AddLessonDescription.waiting_for_text))
async def lesson_resources_link_recieved(message: Message, state: FSMContext):
    fsmdata = await state.get_data()
    lesson = fsmdata.get('lesson')
    if len(message.text) < 2500:
        description_text = message.text
    else:
        builder = InlineKeyboardBuilder()
        builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{lesson.id}')
        await message.answer('Описание к уроку слишком длинное. Постарайтесь уместить его в 1000 символов.\n\nДля подсчёта количества символов можно использовать https://pr-cy.ru/textlength/', reply_markup=builder.as_markup())
        return
    
    upload_status = await db_requests.add_description_for_lesson(lesson.id, description_text)
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{lesson.id}')
    if upload_status:
        await message.answer(f'✅ Добавил описание к уроку.', reply_markup=builder.as_markup())
    else:
        await message.answer(f'❌ Ошибка добавления описания в базу данных.\n\nСвяжитесь с разработчиком.', reply_markup=builder.as_markup())
    await state.clear()


@router.callback_query(F.data.startswith("delete_media_from_lesson_"))
async def delete_media_from_lesson(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    lesson = await db_requests.get_lesson_by_id(callback.data[25:])
    lesson_media = await db_requests.get_lesson_media(lesson.id)
    await state.update_data(lesson=lesson)
    message_text = ('Под каждым медиа файлом указан его ID.\n'
                    'Нажмите кнопку с тем ID, файл которого нужно удалить, а затем вернитесь к уроку.')
    builder = InlineKeyboardBuilder()
    await state.set_state(DeleteLessonMedia.waiting_for_id)
    for media in lesson_media:
        await callback.message.answer_video(video=media.media_id, caption=f'<b>ID файла - {media.id}</b>')
        builder.button(text=f'{media.id}', callback_data=f'delete_media_{media.id}')
    builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{lesson.id}')
    builder.adjust(4)
    await callback.message.answer(message_text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("delete_media_"), StateFilter(DeleteLessonMedia.waiting_for_id))
async def delete_media(callback: CallbackQuery, state: FSMContext):
    delete_status = await db_requests.delete_media_from_lesson(callback.data[13:])
    if not delete_status:
        await callback.message.edit_text('❌ Ошибка удаления файла. Обратитесь к разработчику.')
    builder = InlineKeyboardBuilder()
    fsmdata = await state.get_data()
    lesson = fsmdata.get('lesson')
    lesson_media = await db_requests.get_lesson_media(lesson.id)
    for media in lesson_media:
        builder.button(text=f'{media.id}', callback_data=f'delete_media_{media.id}')
    builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{lesson.id}')
    builder.adjust(4)
    await callback.message.edit_reply_markup(reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("change_homework_"))
async def add_media_to_lesson(callback: CallbackQuery, state: FSMContext):
    homework = await db_requests.get_homework_by_id(callback.data[16:])
    await state.set_state(EditHomework.waiting_for_text)
    await state.update_data(homework=homework)
    message_text = ('Пришлите новый текст домашнего задания.')
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{homework.lesson.id}')
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.message(F.text, StateFilter(EditHomework.waiting_for_text))
async def lesson_video_recieved(message: Message, state: FSMContext):
    fsmdata = await state.get_data()
    homework = fsmdata.get('homework')
    new_homework = await db_requests.edit_homework_content(homework.id, message.text)
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{homework.lesson.id}')
    await message.answer(f'✅ Новый текст домашнего задания к уроку {homework.lesson.title}:\n{new_homework.content}', reply_markup=builder.as_markup())


@router.message(F.text, StateFilter(AddTeachersComment.waiting_for_text))
async def teachers_comemnt_recieved(message: Message, state: FSMContext):
    await state.update_data(teachers_comment=message.text)
    message_text = ('Вы добавили комментарий к работе ученика:\n\n'
                    f'<b>{message.text}</b>\n\n'
                    'Сохранить? Если хотите изменить текст комментария - просто сейчас пришлите мне новый комментарий.')
    builder = InlineKeyboardBuilder()
    builder.button(text='✅ Сохранить', callback_data=f'add_teachers_comment_to_user_homework')
    builder.button(text='❌ Не оставлять комментарий', callback_data=f'cancel_from_')  
    builder.adjust(1)
    await message.answer(message_text, reply_markup=builder.as_markup())


@router.callback_query(F.data == "add_teachers_comment_to_user_homework")
async def add_teachers_comment_to_user_homework(callback: CallbackQuery, state: FSMContext):
    fsmdata = await state.get_data()
    user_homework = fsmdata.get('user_homework')
    user = await db_requests.get_user_by_id(user_homework.user_id)
    lesson = await db_requests.get_lesson_by_id(user_homework.lesson_id)
    teachers_comment = fsmdata.get('teachers_comment')
    message_for_user = f'Автор курса оставил комментарий к вашему домашнему заданию к уроку <b>{lesson.title}</b>'
    await db_requests.add_teachers_comment(user_homework.id, teachers_comment)
    await state.clear()
    await bot.send_message(user.user_telegram_id, message_for_user)
    await callback.message.edit_text('✅ Комментарий к работе ученика сохранён')