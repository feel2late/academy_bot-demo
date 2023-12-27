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
from states.delete_media_from_lesson import DeleteAdditionalMaterials
from states.add_homework import AddHomework
from states.add_user_homework import AddUserHomework

router = Router()  

@router.callback_query(F.data.startswith("delete_resources_"))
async def delete_additional_materials_from_lesson(callback: CallbackQuery, state: FSMContext):
    lesson = await db_requests.get_lesson_by_id(callback.data[17:])
    if not lesson.additional_materials:
        await callback.answer('К этому уроку нет дополнительных материалов.', show_alert=True)
        return
    await callback.message.delete()
    await state.update_data(lesson=lesson)
    message_text = ('Под каждым медиа файлом указан его ID.\n'
                    'Нажмите кнопку с тем ID, файл которого нужно удалить, а затем вернитесь к уроку.')
    builder = InlineKeyboardBuilder()
    await state.set_state(DeleteAdditionalMaterials.waiting_for_id)
    for media in lesson.additional_materials:
        if media.video_id:
            await bot.send_video(callback.from_user.id, video=media.video_id, caption=f'<b>ID файла - {media.id}</b>')
            builder.button(text=f'{media.id}', callback_data=f'delete_media_{media.id}')
        elif media.photo_id:
            await bot.send_photo(callback.from_user.id, photo=media.photo_id, caption=f'<b>ID файла - {media.id}</b>')
            builder.button(text=f'{media.id}', callback_data=f'delete_media_{media.id}')
        elif media.text:
            await callback.message.answer(media.text)
            await callback.message.answer(f'<b>ID текстового файла - {media.id}</b>')
            builder.button(text=f'{media.id}', callback_data=f'delete_media_{media.id}')
        
    builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{lesson.id}')
    builder.adjust(4)
    await callback.message.answer(message_text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("delete_media_"), StateFilter(DeleteAdditionalMaterials.waiting_for_id))
async def delete_media(callback: CallbackQuery, state: FSMContext):
    delete_status = await db_requests.delete_additional_materials(callback.data[13:])
    if not delete_status:
        await callback.message.edit_text('❌ Ошибка удаления файла. Обратитесь к разработчику.')
    builder = InlineKeyboardBuilder()
    fsmdata = await state.get_data()
    lesson = fsmdata.get('lesson')
    for media in lesson.additional_materials:
        builder.button(text=f'{media.id}', callback_data=f'delete_media_{media.id}')
    builder.button(text='🔙 К уроку', callback_data=f'select_lesson_{lesson.id}')
    builder.adjust(4)
    await callback.message.edit_reply_markup(reply_markup=builder.as_markup())