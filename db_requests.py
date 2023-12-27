import datetime
import json
import traceback
import secrets
import string
from models import User, Course, UserCourse, Lesson, Homework, UserHomework, Module, LessonMedia, Order, LessonAdditionalMaterials, UserHomeworkMedia, BotSettings, Admins
from models import db
from sqlalchemy import and_, func, or_
import datetime
import config


async def get_all_courses(for_admin=False) -> list:
    """Возвращает все доступные курсы в боте"""
    if for_admin:
        courses = db.query(Course).order_by(Course.id).all()
    else:
        courses = db.query(Course).filter(Course.available == True).order_by(Course.id).all()
    return courses

async def add_new_course(title) -> int:
    """Возвращает значение course.id"""
    course = Course(title=title, available=False)
    try:
        db.add(course)
        db.commit()
        return course.id
    except:
        print(traceback.format_exc())
        return False
    
async def get_course_by_id(course_id: int) -> Course:
    course = db.query(Course).filter(Course.id == course_id).first()
    return course

async def add_new_module(course_id: int, module_title: int) -> int:
    """Возвращает module.id или False, если модуль не добавлен"""
    module = Module(course_id=course_id, title=module_title)
    try:
        db.add(module)
        db.commit()
        return module.id
    except:
        print(traceback.format_exc())
        return False
    
async def add_new_lesson(module_id: int, lesson_title: int) -> int:
    """Возвращает lesson.id или False, если урок не добавлен"""
    lesson = Lesson(module_id=module_id, title=lesson_title)
    try:
        db.add(lesson)
        db.commit()
        return lesson.id
    except:
        print(traceback.format_exc())
        db.rollback()
        return False
    
async def get_user_by_telegram_id(user_telegram_id: int) -> User:
    user = db.query(User).filter(User.user_telegram_id == user_telegram_id).first()
    return user

async def get_courses_available_to_user(user_id: int) -> list[Course]:
    """Возвращает список доступных курсов для пользователя по user.id"""
    available_courses = db.query(UserCourse).filter(UserCourse.user_id == user_id).all()
    return available_courses

async def get_course_modules(course_id: int) -> list[Module]:
    modules = db.query(Module).filter(Module.course_id == course_id).order_by(Module.id).all()
    return modules

async def add_new_user(user_telegram_id: int, user_name: str, registration_date: datetime) -> int:
    """Создаёт объект пользователя в БД и возвращает его user.id"""
    user = User(user_telegram_id=user_telegram_id, user_name=user_name, registration_date=registration_date)
    try:
        db.add(user)
        db.commit()
        return user.id
    except:
        print(traceback.format_exc())
        return False
    
async def get_module_by_id(module_id: int) -> Module:
    """Возвращает модуль по id"""
    module = db.query(Module).filter(Module.id == module_id).first()
    return module

async def get_lesson_by_id(lesson_id: int) -> Lesson:
    """Возвращает урок по id"""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    return lesson

async def get_lessons_by_module_id(module_id: int) -> list[Lesson]:
    lessons = db.query(Lesson).filter(Lesson.module_id == module_id).order_by(Lesson.id).all()
    return lessons

async def get_date_added_course_to_user(user_id: int, course_id: int) -> datetime:
    course = db.query(UserCourse).filter(UserCourse.course_id == course_id, UserCourse.user_id == user_id).first()
    return course.date_added if course else False

async def add_course_to_user(user_id: int, course_id: int, date_added: datetime) -> bool:
    """Добавляет курс к доступным для ученика и возвращает булево значение"""
    course = UserCourse(user_id=user_id, course_id=course_id, date_added=date_added)
    try:
        db.add(course)
        db.commit()
        return True
    except:
        print(traceback.format_exc())
        return False
    
async def add_media_to_lesson(media_id: str, lesson_id: int, media_name: str) -> bool:
    """Добавляет id медиа-файла к уроку. Возвращает успешность операции."""
    lesson_media = LessonMedia(media_id=media_id, lesson_id=lesson_id, media_name=media_name)
    try:
        db.add(lesson_media)
        db.commit()
        return True
    except:
        print(traceback.format_exc())
        return False
    
async def get_lesson_media(lesson_id: int) -> list[str]:
    """Возвращает все найденные в БД file_id медиа для заданного урока"""
    lesson_media = db.query(LessonMedia).filter(LessonMedia.lesson_id == lesson_id).order_by(LessonMedia.id).all()
    return lesson_media

async def add_resources_link_to_lesson(lesson_id: int, resources_link: str) -> bool:
    """Добавляет ссылку на облако с доп. материалами к уроку. Возвращает успешность операции."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    lesson.resources = resources_link
    
    try:
        db.commit()
        return True
    except:
        print(traceback.format_exc())
        return False

async def add_description_for_lesson(lesson_id: int, description: str) -> bool:
    """Добавляет описание к уроку. Возвращает успешность операции."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    lesson.description = description
    
    try:
        db.commit()
        return True
    except:
        print(traceback.format_exc())
        return False
    
async def delete_media_from_lesson(id: int) -> bool:
    """Удаляет медиа по его id из урока"""
    media = db.query(LessonMedia).filter(LessonMedia.id == id).first()
    try:
        db.delete(media)
        db.commit()
        return True
    except:
        print(traceback.format_exc())
        return False
    
async def add_description_for_module(module_id: int, description: str) -> bool:
    """Добавляет описание к модулю. Возвращает успешность операции."""
    module = db.query(Module).filter(Module.id == module_id).first()
    module.description = description
    
    try:
        db.commit()
        return True
    except:
        print(traceback.format_exc())
        return False

async def add_description_for_course(course_id: int, description: str) -> bool:
    """Добавляет описание к курсу. Возвращает успешность операции."""
    course = db.query(Course).filter(Course.id == course_id).first()
    course.description = description
    
    try:
        db.commit()
        return True
    except:
        print(traceback.format_exc())
        return False

async def edit_course_name(course_id: int, new_name: str) -> bool:
    """Изменяет название курса. Возвращает успешность операции."""
    course = db.query(Course).filter(Course.id == course_id).first()
    course.title = new_name
    try:
        db.commit()
        return True
    except:
        print(traceback.format_exc())
        return False
    
async def edit_module_name(module_id: int, new_name: str) -> bool:
    """Изменяет название модуля. Возвращает успешность операции."""
    module = db.query(Module).filter(Module.id == module_id).first()
    module.title = new_name
    try:
        db.commit()
        return True
    except:
        print(traceback.format_exc())
        return False
    
async def edit_lesson_name(lesson_id: int, new_name: str) -> bool:
    """Изменяет название урока. Возвращает успешность операции."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    lesson.title = new_name
    try:
        db.commit()
        return True
    except:
        print(traceback.format_exc())
        return False
    
    
async def add_price_for_course(course_id: int, price: int) -> bool:
    """Добавляет стоимость к курсу. Возвращает успешность операции."""
    course = db.query(Course).filter(Course.id == course_id).first()
    course.price = price
    
    try:
        db.commit()
        return True
    except:
        print(traceback.format_exc())
        return False
    
async def change_course_availability(course_id: int) -> bool:
    """Изменяет доступность (отображение) курса. Возвращает успешность операции."""
    course = db.query(Course).filter(Course.id == course_id).first()
    
    if course.available:
        course.available = False
    else:
        course.available = True
    
    try:
        db.commit()
        return True
    except:
        print(traceback.format_exc())
        return False
    
async def set_course_chat_link(course_id: int, chat_link: str, chat_id: int) -> bool:
    """Изменяет (устанавливает) ссылку на чат курса. Возвращает успешность операции."""
    course = db.query(Course).filter(Course.id == course_id).first()
    course.chat_link = chat_link
    course.chat_id = chat_id
    try:
        db.commit()
        return True
    except:
        print(traceback.format_exc())
        return False

async def set_module_duration(module_id: int, duration: int) -> bool:
    """Изменяет (устанавливает) продолжительность модуля. Возвращает успешность операции."""
    module = db.query(Module).filter(Module.id == module_id).first()
    module.duration = duration
    try:
        db.commit()
        return True
    except:
        print(traceback.format_exc())
        return False
    
async def delete_lesson(lesson_id: int) -> bool:
    """Удаляет урок и все домашние задания к нему. Возвращает успешность операции."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    try:
        db.delete(lesson)
        db.commit()
        return True
    except:
        print(traceback.format_exc())
        return False
    
async def delete_module(module_id: int) -> bool:
    """Удаляет модуль и все уроки и домашние задания к нему. Возвращает успешность операции."""
    module = db.query(Module).filter(Module.id == module_id).first()
    lessons = db.query(Lesson).filter(Lesson.module_id == module.id).all()
    try:
        for lesson in lessons:
            await delete_lesson(lesson.id)
        db.delete(module)
        db.commit()
        return True
    except:
        print(traceback.format_exc())
        return False
    
async def delete_course(course_id: int) -> bool:
    """Удаляет курс, все его модули и все уроки и домашние задания к нему. Возвращает успешность операции."""
    course = db.query(Course).filter(Course.id == course_id).first()
    modules = db.query(Module).filter(Module.course_id == course_id).all()
    
    try:
        for module in modules:
            await delete_module(module.id)
        db.delete(course)
        db.commit()
        return True
    except:
        print(traceback.format_exc())
        return False
    
async def create_order(course_id: int, user_id: int) -> int:
    """Создаёт заказ и возвращает его order.id"""
    order_date = datetime.datetime.utcnow()
    order = Order(order_date=order_date, user_id=user_id, course_id=course_id)
    try:
        db.add(order)
        db.commit()
        return order.id
    except:
        print(traceback.format_exc())
        return False
    
async def add_phonenumber_for_user(user_id: int, phonenumber: str) -> bool:
    """Добавляет (или изменяет) номер телефона клиента. Возвращает успешность операции."""
    user = db.query(User).filter(User.id == user_id).first()
    user.phone_number = phonenumber
    try:
        db.commit()
        return True
    except:
        print(traceback.format_exc())
        return False
    
async def get_order_by_id(order_id: int) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    return order

async def change_order_payment_status(order_id: int, payment_status: bool) -> None:
    order = db.query(Order).filter(Order.id == order_id).first()
    order.paid = payment_status
    try:
        db.commit()
        return True
    except:
        print(traceback.format_exc())
        return False
    
async def get_user_by_id(user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    return user

async def get_lesson_homework(lesson_id: int) -> Homework:
    """Возвращает объект домашнего задания по lesson.id"""
    homework = db.query(Homework).filter(Homework.lesson_id == lesson_id).first()
    return homework

async def add_homework_content(lesson_id: int, content: str) -> bool:
    """Создаёт объект домашнего задания в БД (или изменяет текст при его наличии) и возвращает результат работы"""
    homework = db.query(Homework).filter(Homework.lesson_id == lesson_id).first()
    if not homework:
        homework = Homework(content=content, lesson_id=lesson_id)
        try:
            db.add(homework)
            db.commit()
            return True
        except:
            print(traceback.format_exc())
            return False
    else:
        homework.content = content
        try:
            db.commit()
            return True
        except:
            print(traceback.format_exc())
            return False
        
async def add_user_homework(user_id: int, lesson_id: int) -> UserHomework:
    """Создаёт объект домашнего задания в БД и возвращает homework.id"""
    user_homework = UserHomework(lesson_id=lesson_id, user_id=user_id)
    try:
        db.add(user_homework)
        db.commit()
        return user_homework
    except:
        print(traceback.format_exc())
        return False
    
async def get_user_homework(user_id: int, lesson_id: int) -> UserHomework:
    user_homework = db.query(UserHomework).filter(UserHomework.user_id == user_id, UserHomework.lesson_id == lesson_id).first()
    return user_homework

async def add_user_homework_media(user_homework_id: int, video_id: str = None, photo_id: str = None, text: str = None) -> bool:
    """Добавляет в домашнее задание ученика медиа (идентификатор внутри ТГ) или текстовое сообщение. Возвращает user_homework_media.id или False"""
    user_homework_media = UserHomeworkMedia(user_homework_id=user_homework_id, video_id=video_id, photo_id=photo_id, text=text)
    try:
        db.add(user_homework_media)
        db.commit()
        return user_homework_media.id
    except:
        print(traceback.format_exc())
        return False
    
async def add_additional_materials(lesson_id: int, video_id: str = None, photo_id: str = None, text: str = None) -> bool:
    """Добавляет в урок дополнительные медиа (идентификатор внутри ТГ) или текстовое сообщение. Возвращает True если добавление успешно или False"""
    lesson_additional_materials = LessonAdditionalMaterials(lesson_id=lesson_id, video_id=video_id, photo_id=photo_id, text=text)
    try:
        db.add(lesson_additional_materials)
        db.commit()
        return True
    except:
        print(traceback.format_exc())
        return False
        
async def get_homework_by_id(homework_id: int) -> Homework:
    homework = db.query(Homework).filter(Homework.id == homework_id).first()
    return homework

async def get_user_homework_by_id(user_homework_id: int) -> UserHomework:
    homework = db.query(UserHomework).filter(UserHomework.id == user_homework_id).first()
    return homework

async def rate_user_homework(homework_id: int, rate: int) -> None:
    user_homework = db.query(UserHomework).filter(UserHomework.id == homework_id).first()
    user_homework.grade = rate
    try:
        db.commit()
        return True
    except:
        print(traceback.format_exc())
        return False
    
async def add_teachers_comment(homework_id: int, comment: str) -> None:
    user_homework = db.query(UserHomework).filter(UserHomework.id == homework_id).first()
    user_homework.teachers_comment = comment
    try:
        db.commit()
        return True
    except:
        print(traceback.format_exc())
        return False
    
async def delete_additional_materials(id: int) -> bool:
    """Удаляет доп. материал по его id из урока"""
    media = db.query(LessonAdditionalMaterials).filter(LessonAdditionalMaterials.id == id).first()
    try:
        db.delete(media)
        db.commit()
        return True
    except:
        print(traceback.format_exc())
        return False
    
async def get_course_by_chat_id(chat_id: int) -> Course:
    course = db.query(Course).filter(Course.chat_id == chat_id).first()
    return course

async def get_purchased_courses(user_id: int) -> list[Course]:
    """Получает купленные пользователем курсы"""
    courses = db.query(UserCourse).filter(UserCourse.user_id == user_id).all()
    return courses

async def get_all_users() -> list[User]:
    users = db.query(User).all()
    return users

async def get_all_orders() -> list[Order]:
    orders = db.query(Order).all()
    return orders

async def edit_homework_content(homework_id: int, new_content: str) -> Homework:
    homework = db.query(Homework).filter(Homework.id == homework_id).first()
    homework.content = new_content
    db.commit()
    return homework

async def edit_user_homework_required(homework_id: int) -> None:
    homework = db.query(Homework).filter(Homework.id == homework_id).first()
    if homework.user_homework_required:
        homework.user_homework_required = False
    else:
        homework.user_homework_required = True    
    db.commit()
    return homework

async def init_bot_settings(user_telegram_id, user_name):
    all_settings = db.query(BotSettings).all()
    if not all_settings:
        bot_settings = BotSettings(welcome_message=config.WELCOME_MESSAGE_EXAMPLE)
        admin = Admins(user_telegram_id=user_telegram_id, user_name=user_name)
    db.add_all([bot_settings, admin])
    db.commit()
    
async def get_bot_settings() -> BotSettings:
    bot_settings = db.query(BotSettings).first()
    return bot_settings

async def add_admin(user_telegram_id: int, user_name: str):
    admin = Admins(user_telegram_id=user_telegram_id, user_name=user_name)
    db.add(admin)
    db.commit()

async def get_admins() -> list[Admins]:
    admins = db.query(Admins).all()
    return admins

async def delete_admins():
    admins = db.query(Admins).all()
    for admin in admins:
        db.delete(admin)
    db.commit()

async def set_welcome_message(welcome_message: str) -> None:
    bot_settings = db.query(BotSettings).first()
    bot_settings.welcome_message = welcome_message
    db.commit()

async def set_welcome_video(welcome_video_id: str) -> None:
    bot_settings = db.query(BotSettings).first()
    bot_settings.welcome_video_id = welcome_video_id
    db.commit()

async def edit_social_media(social_media_type: str, new_value: str):
    bot_settings = db.query(BotSettings).first()

    if social_media_type == 'phonenumber':
        bot_settings.author_phone_number = new_value
    elif social_media_type == 'telegram':
        bot_settings.author_telegram = new_value
    elif social_media_type == 'telegram_group':
        bot_settings.author_telegram_public = new_value
    elif social_media_type == 'instagram':
        bot_settings.author_instagram = new_value
    elif social_media_type == 'vk':
        bot_settings.author_vk = new_value
    elif social_media_type == 'vk_group':
        bot_settings.author_vk_public = new_value
    
    db.commit()