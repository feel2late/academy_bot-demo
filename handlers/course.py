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
from states.add_description import AddCourseDescription
from states.edit_name import EditCourseName
from states.add_price_for_course import AddPriceForCourse
from payment.generate_payment_link import generate_payment_link
from handlers.menu import courses


router = Router()  

async def is_course_available_to_user(user_id: int, target_course_id: int) -> bool:
    available_courses = await db_requests.get_courses_available_to_user(user_id)
    for user_course in available_courses:
        if user_course.course_id == target_course_id:
            return True
    return False


async def check_course_availability(user_id: int, course_id: int) -> bool:
    """Проверяет, доступен ли курс пользователю"""
    user = await db_requests.get_user_by_id(user_id)
    courses_available_to_user = await db_requests.get_purchased_courses(user.id)
    for available_course in courses_available_to_user:
        if available_course.course_id and int(available_course.course_id) == int(course_id):
            return True
    return False


@router.callback_query(F.data.startswith("select_course_"))
async def select_course(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    course = await db_requests.get_course_by_id(callback.data[14:])
    user = await db_requests.get_user_by_telegram_id(callback.from_user.id)
    admins_ids = [admin.user_telegram_id for admin in await db_requests.get_admins()]
    offset = 0
    builder = InlineKeyboardBuilder()
    

    if await is_course_available_to_user(user.id, course.id) or callback.from_user.id in admins_ids or callback.from_user.id == config.ROOT_ADMIN:
        modules = await db_requests.get_course_modules(course.id)

        for id, module in enumerate(modules):
            for module_in_course in modules:
                if module_in_course.title != module.title:
                    offset += module_in_course.duration
                else:
                    break
            if callback.from_user.id in admins_ids or callback.from_user.id == config.ROOT_ADMIN:
                builder.button(text=f'{id + 1}. {module.title}', callback_data=f'select_module_{module.id}')
            else:
                date_added_course = await db_requests.get_date_added_course_to_user(user.id, module.course.id)
                opened_date = date_added_course + datetime.timedelta(hours=offset+3)
                if opened_date > datetime.datetime.utcnow():
                    builder.button(text=f'🔒 до {datetime.datetime.strftime(opened_date, "%d.%m")} | {id + 1}. {module.title}', callback_data=f'select_module_{module.id}')
                else:
                    builder.button(text=f'{id + 1}. {module.title}', callback_data=f'select_module_{module.id}')
        if course.chat_link:
            builder.button(text='💬 Чат курса', url=f'tg://join?invite={course.chat_link}')
        else:
            builder.button(text='💬 Чат курса', callback_data='no_course_chat')
        if callback.from_user.id in admins_ids or callback.from_user.id == config.ROOT_ADMIN:
            builder.button(text='➕ Добавить модуль', callback_data=f'add_new_module_to_{course.id}')
            builder.button(text='✏️ Изменить название курса', callback_data=f'edit_course_name_{course.id}')
            if course.description:
                builder.button(text='✏️ Изменить описание курса', callback_data=f'add_course_description_{course.id}')
            else:
                builder.button(text='✏️ Добавить описание курса', callback_data=f'add_course_description_{course.id}')
            if course.price:
                builder.button(text='💲 Изменить стоимость курса', callback_data=f'add_course_price_{course.id}')
            else:
                builder.button(text='💲 Установить стоимость курса', callback_data=f'add_course_price_{course.id}')
            if course.available:
                builder.button(text='✅ Курс отображается', callback_data=f'change_course_available_{course.id}')
            else:
                builder.button(text='❌ Курс не отображается', callback_data=f'change_course_available_{course.id}')
            builder.button(text='📨 Рассылка ученикам курса', callback_data=f'admin_send_message_to_all_users_course_{course.id}')
            builder.button(text='🗑 Удалить курс', callback_data=f'm_delete_course_{course.id}')
        builder.button(text='🔙 Выбор курса', callback_data='courses')
        builder.adjust(1)
        message_text = f'Вы выбрали курс <b>{course.title}</b>.\n\n'
        if course.description:
            message_text += f'{course.description}\n\n'
        message_text += 'Выберите нужный модуль.'

    else:
        message_text = (f'Вы выбрали курс <b>{course.title}</b>\n\n')
        if course.description:
            message_text += f'{course.description}\n\n'
        if course.price == 0:
            message_text += f'Данный курс является абсолютно бесплатным!'
            builder.button(text='🆓 Открыть курс', callback_data=f'buy_course_{course.id}')
        else:
            message_text += f'Данный курс доступен для покупки всего за <b>{course.price} рублей!</b>'
            builder.button(text='🛍 Купить курс', callback_data=f'buy_course_{course.id}')
        builder.button(text='🔙 Выбор курса', callback_data='courses')
        builder.adjust(1)

    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.callback_query(F.data == "no_course_chat")
async def no_course_chat(callback: CallbackQuery):
    await callback.answer('Для этого курса ещё не создан чат', show_alert=True)


@router.callback_query(F.data.startswith("buy_course_"))
async def buy_course(callback: CallbackQuery, state: FSMContext):
    user = await db_requests.get_user_by_telegram_id(callback.from_user.id)
    course = await db_requests.get_course_by_id(callback.data[11:])
    if not user.phone_number:
        await callback.message.delete()
        await state.update_data(course=course)
        if course.price == 0:
            message_text = 'Для открытия курса мне нужен ваш номер телефона. Пожалуйста, нажмите кнопку \"☎️ Отправить свой номер\"'
        else:
            message_text = 'Для создания оплаты мне нужен ваш номер телефона. Пожалуйста, нажмите кнопку \"☎️ Отправить свой номер\"'
        builder = ReplyKeyboardBuilder()
        builder.row(types.KeyboardButton(text="☎️ Отправить свой номер.", request_contact=True))
        await callback.message.answer(message_text, reply_markup=builder.as_markup(resize_keyboard=True))
        return
    else:
        if course.price == 0:
            builder = InlineKeyboardBuilder()
            builder.button(text='🔥 Перейти к курсу!', callback_data=f'select_course_{course.id}')
            now = datetime.datetime.utcnow()
            await db_requests.add_course_to_user(user.id, course.id, now)
            await callback.message.edit_text(f'Вы открыли бесплатный курс <b>{course.title}</b>!', reply_markup=builder.as_markup())
            return
        if not config.SECRET_PRODAMUS_KEY:
            if config.DEMO:
                user = await db_requests.get_user_by_telegram_id(callback.from_user.id)
                now = datetime.datetime.utcnow()
                user_message_text = (f'✅ Для вас открыт доступ к курсу <b>{course.title}</b> в демо режиме.\n'
                                    f'Скорей приступайте к изучению бота!')
                await db_requests.add_course_to_user(user.id, course.id, now)
                builder = InlineKeyboardBuilder()
                builder.button(text='🔥 Перейти к курсу!', callback_data=f'select_course_{course.id}')
                await callback.message.edit_text(user_message_text, reply_markup=builder.as_markup())
                return
            else:   
                builder = InlineKeyboardBuilder()
                builder.button(text='🔙 Выбор курса', callback_data='courses')
                message_text = '⛔️ Платежная система не подключена. Пока что оплатить курс нельзя.'
                await callback.message.edit_text(message_text, reply_markup=builder.as_markup())
                return
        order_id = await db_requests.create_order(course.id, user.id)
        payment_link = await generate_payment_link(order_id, user.phone_number, course.id)
        message_text = (f'Для оплаты доступа к курсу <b>{course.title}</b> нажмите кнопку "💳 Оплатить доступ".\n'
                        '↪️ Вы будете перенаправлены на страницу оплаты.\n\n'
                        'После успешной оплаты бот пришлёт уведомление и вы получите доступ к курсу.\n\n'
                        '⏱ Подтверждение оплаты может занимать до нескольких минут. Пожалуйста, подождите.')
        builder = InlineKeyboardBuilder()
        builder.button(text='💳 Оплатить доступ', url=payment_link)
        builder.button(text='💱 Оплачен напрямую автору', callback_data=f'direct_payment_{course.id}')
        builder.button(text='🔙 Выбор курса', callback_data='courses')
        builder.adjust(1)
        await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.message(F.contact)
async def on_user_shared(message: types.Message, state: FSMContext):
    if message.from_user.id == message.contact.user_id:
        user = await db_requests.get_user_by_telegram_id(message.from_user.id)
        fsmdata = await state.get_data()
        if user.phone_number:
            return
        elif fsmdata.get('course'):
            course = fsmdata.get('course')
            add_phonenumber = await db_requests.add_phonenumber_for_user(user.id, message.contact.phone_number[1:] if message.contact.phone_number.startswith('+') else message.contact.phone_number)
            if add_phonenumber:
                if course.price == 0:
                    builder = InlineKeyboardBuilder()
                    builder.button(text='🔥 Перейти к курсу!', callback_data=f'select_course_{course.id}')
                    now = datetime.datetime.utcnow()
                    await db_requests.add_course_to_user(user.id, course.id, now)
                    await message.answer(f'Вы открыли бесплатный курс <b>{course.title}</b>!', reply_markup=types.ReplyKeyboardRemove())
                    await message.answer('Начать учиться?', reply_markup=builder.as_markup())
                    return
                if not config.SECRET_PRODAMUS_KEY:
                    if config.DEMO:
                        user = await db_requests.get_user_by_telegram_id(message.from_user.id)
                        now = datetime.datetime.utcnow()
                        await db_requests.add_course_to_user(user.id, course.id, now)
                        builder = InlineKeyboardBuilder()
                        builder.button(text='🔥 Перейти к курсу!', callback_data=f'select_course_{course.id}')
                        await message.answer(f'✅ Для вас открыт доступ к курсу <b>{course.title}</b> в демо режиме.\n', reply_markup=types.ReplyKeyboardRemove())
                        await message.answer(f'Скорей приступайте к изучению бота!', reply_markup=builder.as_markup())
                        return
                    else:   
                        builder = InlineKeyboardBuilder()
                        builder.button(text='🔙 Выбор курса', callback_data='courses')
                        await message.answer('⛔️ Платежная система не подключена.', reply_markup=types.ReplyKeyboardRemove())
                        await message.answer('Пока что оплатить курс нельзя 🤷🏻‍♂️', reply_markup=builder.as_markup())
                        return
                order_id = await db_requests.create_order(course.id, user.id)
                payment_link = await generate_payment_link(order_id, user.phone_number, course.id)
                message_text = (f'Для оплаты доступа к курсу <b>{course.title}</b> нажмите кнопку "💳 Оплатить доступ".\n'
                                '↪️ Вы будете перенаправлены на страницу оплаты.\n\n'
                                'После успешной оплаты бот пришлёт уведомление и вы получите доступ к курсу.\n\n'
                                '⏱ Подтверждение оплаты может занимать до нескольких минут. Пожалуйста, подождите.')
                builder = InlineKeyboardBuilder()
                builder.button(text='💳 Оплатить доступ', url=payment_link)
                builder.button(text='💱 Оплачен напрямую автору', callback_data=f'direct_payment_{course.id}')
                builder.button(text='🔙 Выбор курса', callback_data='courses')
                builder.adjust(1)
                await message.answer('✅ Номер телефона успешно привязан к вашему профилю.', reply_markup=types.ReplyKeyboardRemove())
                await message.answer(message_text, reply_markup=builder.as_markup())
            else:
                message_text = 'Ошибка добавления номера телефона. Попробуйте позже или свяжитесь с автором курса.'
                await message.answer(message_text)
        

@router.callback_query(F.data.startswith("direct_payment_"))
async def request_to_course_by_user(callback: CallbackQuery, state: FSMContext):
    course = await db_requests.get_course_by_id(callback.data[15:])
    user = await db_requests.get_user_by_telegram_id(callback.from_user.id)
    admins_ids = [admin.user_telegram_id for admin in await db_requests.get_admins()]
    user_message_text = 'Запрос на предоставление доступа к курсу отправлен автору.'
    message_text = (f'⚠️ Получен запрос от пользователя {user.user_name} (+{user.phone_number}) на открытие курса {course.title}.\n\n'
                    'Если вы получили оплату от данного пользователя за курс, вы можете открыть ему доступ.')
    builder = InlineKeyboardBuilder()
    builder.button(text='✅ Курс оплачен. Открыть доступ', callback_data=f'open_course_{course.id}.user_{user.id}')
    await callback.message.edit_text(user_message_text)
    for admin in admins_ids:
        try:
            await bot.send_message(admin, message_text, reply_markup=builder.as_markup())
        except:
            pass


@router.callback_query(F.data.startswith("open_course_"))
async def open_course_to_user(callback: CallbackQuery, state: FSMContext):
    callback_message = callback.data.split('.')
    course = await db_requests.get_course_by_id(callback_message[0][12:])
    user = await db_requests.get_user_by_id(callback_message[1][5:])
    now = datetime.datetime.utcnow()
    if await check_course_availability(user.id, course.id):
        await callback.message.edit_text(f'✅ Для пользователя {user.user_name} кто-то уже открыл доступ к курсу {course.title}.')
        return
    add_course = await db_requests.add_course_to_user(user.id, course.id, now)
    
    if add_course:
        await bot.send_message(user.user_telegram_id, f'✅ Вам предоставлен доступ к курсу {course.title}.')
        await callback.message.edit_text(f'✅ Для пользователя {user.user_name} открыт доступ к курсу {course.title}')
    else:
        await callback.message.answer('Ошибка открытия курса. Обратитесь к разработчику.')


'''Хендлер на успешное приобритение курса
course = await db_requests.get_course_by_id(callback.data[11:])
        user = await db_requests.get_user_by_telegram_id(callback.from_user.id)
        now = datetime.datetime.utcnow()
        await db_requests.add_course_to_user(user.id, course.id, now)
        message_text = '✅ Курс успешно приобретён.'
        builder = InlineKeyboardBuilder()
        builder.button(text='📂 Открыть курс', callback_data=f'select_course_{course.id}')
        builder.button(text='🔙 Список курсов', callback_data='courses')
        builder.adjust(1)
        await callback.message.edit_text(message_text, reply_markup=builder.as_markup())

'''

@router.callback_query(F.data.startswith("add_course_description_"))
async def add_course_description(callback: CallbackQuery, state: FSMContext):
    course = await db_requests.get_course_by_id(callback.data[23:])
    await state.update_data(course=course)
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 К курсу', callback_data=f'select_course_{course.id}')
    if course.description:
        message_text = (f'Текущее описание для курса <b>{course.title}</b>:\n\n'
                        f'"{course.description}"\n\n'
                        'Пришлите новое описание или вернитесь к курсу.')
    else:
        message_text = 'Пришлите новое описание к курсу.'
    await state.set_state(AddCourseDescription.waiting_for_text)
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.message(F.text, StateFilter(AddCourseDescription.waiting_for_text))
async def course_description_recieved(message: Message, state: FSMContext):
    fsmdata = await state.get_data()
    course = fsmdata.get('course')
    if len(message.text) < 2500:
        description_text = message.text
    else:
        builder = InlineKeyboardBuilder()
        builder.button(text='🔙 К курсу', callback_data=f'select_course_{course.id}')
        await message.answer('Описание к курсу слишком длинное. Постарайтесь уместить его в 1000 символов.\n\nДля подсчёта количества символов можно использовать https://pr-cy.ru/textlength/', reply_markup=builder.as_markup())
        return
    
    upload_status = await db_requests.add_description_for_course(course.id, description_text)
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 К курсу', callback_data=f'select_course_{course.id}')
    if upload_status:
        await message.answer(f'✅ Добавил описание к курсу.', reply_markup=builder.as_markup())
    else:
        await message.answer(f'❌ Ошибка добавления описания в базу данных.\n\nСвяжитесь с разработчиком.', reply_markup=builder.as_markup())
    await state.clear()


@router.callback_query(F.data.startswith("edit_course_name_"))
async def add_course_description(callback: CallbackQuery, state: FSMContext):
    course = await db_requests.get_course_by_id(callback.data[17:])
    await state.update_data(course=course)
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 К курсу', callback_data=f'select_course_{course.id}')
    message_text = (f'Текущее название курса: <b>{course.title}</b>\n\n'
                    'Пришлите новое название или вернитесь к курсу.')
    await state.set_state(EditCourseName.waiting_for_text)
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.message(F.text, StateFilter(EditCourseName.waiting_for_text))
async def new_course_name_recieved(message: Message, state: FSMContext):
    fsmdata = await state.get_data()
    course = fsmdata.get('course')
    upload_status = await db_requests.edit_course_name(course.id, message.text)
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 К курсу', callback_data=f'select_course_{course.id}')
    if upload_status:
        await message.answer(f'✅ Изменил название курса', reply_markup=builder.as_markup())
    else:
        await message.answer(f'❌ Ошибка изменения названия курса в базе данных.\n\nСвяжитесь с разработчиком.', reply_markup=builder.as_markup())
    await state.clear()


@router.callback_query(F.data.startswith("add_course_price_"))
async def add_course_description(callback: CallbackQuery, state: FSMContext):
    course = await db_requests.get_course_by_id(callback.data[17:])
    await state.update_data(course=course)
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 К курсу', callback_data=f'select_course_{course.id}')
    if course.price:
        message_text = (f'Текущая стоимость курса <b>{course.price}</b> рублей.\n\n'
                        'Пришлите новую стоимость или вернитесь к курсу.\n\n'
                        'Вы можете прислать "0", чтобы сделать курс бесплатным.')
    else:
        message_text = 'Пришлите стоимость курса.\nВы можете прислать "0", чтобы сделать курс бесплатным.'
    await state.set_state(AddPriceForCourse.waiting_for_new_price)
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.message(F.text, StateFilter(AddPriceForCourse.waiting_for_new_price))
async def course_price_recieved(message: Message, state: FSMContext):
    fsmdata = await state.get_data()
    course = fsmdata.get('course')
    if message.text.isdigit():
        new_price = int(message.text)
        print(new_price)
    else:
        builder = InlineKeyboardBuilder()
        builder.button(text='🔙 К курсу', callback_data=f'select_course_{course.id}')
        await message.answer('Стоимость курса должна быть указана в рублях без копеек, целым числом.', reply_markup=builder.as_markup())
        return
    
    upload_status = await db_requests.add_price_for_course(course.id, new_price)
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 К курсу', callback_data=f'select_course_{course.id}')
    if upload_status:
        await message.answer(f'✅ Добавил стоимость курса.', reply_markup=builder.as_markup())
    else:
        await message.answer(f'❌ Ошибка добавления стоимости в базу данных.\n\nСвяжитесь с разработчиком.', reply_markup=builder.as_markup())
    await state.clear()


@router.callback_query(F.data.startswith("change_course_available_"))
async def change_course_available(callback: CallbackQuery, state: FSMContext):
    course = await db_requests.get_course_by_id(callback.data[24:])
    admins_ids = [admin.user_telegram_id for admin in await db_requests.get_admins()]
    await db_requests.change_course_availability(course.id)
    modules = await db_requests.get_course_modules(course.id)
    builder = InlineKeyboardBuilder()

    for id, module in enumerate(modules):
        builder.button(text=f'{id + 1}. {module.title}', callback_data=f'select_module_{module.id}')
    if course.chat_link:
        builder.button(text='💬 Чат курса', url=f'tg://join?invite={course.chat_link}')
    else:
        builder.button(text='💬 Чат курса', callback_data='no_course_chat')
    if callback.from_user.id in admins_ids:
        builder.button(text='➕ Добавить модуль', callback_data=f'add_new_module_to_{course.id}')
        if course.description:
            builder.button(text='✏️ Изменить описание', callback_data=f'add_course_description_{course.id}')
        else:
            builder.button(text='✏️ Добавить описание', callback_data=f'add_course_description_{course.id}')
        if course.price:
            builder.button(text='💲 Изменить стоимость', callback_data=f'add_course_price_{course.id}')
        else:
            builder.button(text='💲 Установить стоимость', callback_data=f'add_course_price_{course.id}')
        if course.available:
            builder.button(text='✅ Курс отображается', callback_data=f'change_course_available_{course.id}')
        else:
            builder.button(text='❌ Курс не отображается', callback_data=f'change_course_available_{course.id}')
        builder.button(text='📨 Рассылка', callback_data=f'admin_send_message_to_all_users_course_{course.id}')
        builder.button(text='🗑 Удалить курс', callback_data=f'm_delete_course_{course.id}')
    builder.button(text='🔙 Выбор курса', callback_data='courses')
    builder.adjust(1)
    await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
