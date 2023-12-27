from datetime import timedelta
from sqlalchemy import BigInteger, Column, Date, ForeignKey, Integer, Float, String, Boolean, Table, create_engine, DateTime
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.orm import relationship
import config

engine = create_engine(f"postgresql://{config.DB_USER}:{config.DB_PASSWORD}@localhost/{config.DB_NAME}", connect_args={"sslmode": "disable"})

class Base(DeclarativeBase): 
    pass

with Session(autoflush=False, bind=engine) as db: 
    pass


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user_telegram_id = Column(BigInteger)
    phone_number = Column(String)
    user_name = Column(String, nullable=False)
    registration_date = Column(DateTime, nullable=False)
    courses = relationship('UserCourse', back_populates='user')
    orders = relationship('Order', back_populates='user')

class Course(Base):
    __tablename__ = 'courses'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    price = Column(Integer)
    available = Column(Boolean)
    chat_link = Column(String)
    chat_id = Column(BigInteger)
    modules = relationship('Module', back_populates='course')
    users = relationship('UserCourse', back_populates='course')
    orders = relationship('Order', back_populates='course')

class Module(Base):
    __tablename__ = 'modules'
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(String)
    duration = Column(Integer, default=0) # hours
    course_id = Column(Integer, ForeignKey('courses.id')) 
    course = relationship('Course', back_populates='modules')  
    lessons = relationship('Lesson', back_populates='module')  

class UserCourse(Base):
    __tablename__ = 'user_courses'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    course_id = Column(Integer, ForeignKey('courses.id'))
    date_added = Column(DateTime)
    user = relationship('User', back_populates='courses')
    course = relationship('Course', back_populates='users')

class Lesson(Base):
    __tablename__ = 'lessons'
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(String)
    resources = Column(String)
    course_id = Column(Integer, ForeignKey('courses.id'))  
    module_id = Column(Integer, ForeignKey('modules.id'))
    module = relationship('Module', back_populates='lessons')
    homework = relationship('Homework', back_populates='lesson')
    media = relationship('LessonMedia', back_populates='lesson')
    additional_materials = relationship('LessonAdditionalMaterials', back_populates='lesson')
    
class LessonMedia(Base):
    __tablename__ = 'lesson_media'
    id = Column(Integer, primary_key=True)
    media_id = Column(String, nullable=False)
    media_name = Column(String)
    lesson_id = Column(Integer, ForeignKey('lessons.id')) 
    lesson = relationship('Lesson', back_populates='media')

class LessonAdditionalMaterials(Base):
    __tablename__ = 'lesson_additional_materials'
    id = Column(Integer, primary_key=True)
    text = Column(String)
    video_id = Column(String)
    photo_id = Column(String)
    lesson_id = Column(Integer, ForeignKey('lessons.id'))
    lesson = relationship('Lesson', back_populates='additional_materials')

class Homework(Base):
    __tablename__ = 'homeworks'
    id = Column(Integer, primary_key=True)
    content = Column(String, nullable=False)
    lesson_id = Column(Integer, ForeignKey('lessons.id'))
    user_homework_required = Column(Boolean, default=False)
    lesson = relationship('Lesson', back_populates='homework')
    media = relationship('HomeworkMedia', back_populates='homework')

class HomeworkMedia(Base):
    __tablename__ = 'homework_media'
    id = Column(Integer, primary_key=True)
    media_id = Column(String, nullable=False)
    homework_id = Column(Integer, ForeignKey('homeworks.id'))
    homework = relationship('Homework', back_populates='media') 

class UserHomework(Base):
    __tablename__ = 'user_homeworks'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    lesson_id = Column(Integer)
    grade = Column(Integer)
    teachers_comment = Column(String)
    media = relationship('UserHomeworkMedia', back_populates='user_homework')

class UserHomeworkMedia(Base):
    __tablename__ = 'user_homework_media'
    id = Column(Integer, primary_key=True)
    text = Column(String)
    video_id = Column(String)
    photo_id = Column(String)
    user_homework_id = Column(Integer, ForeignKey('user_homeworks.id'))
    user_homework = relationship('UserHomework', back_populates='media')

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    order_date = Column(DateTime)
    user_id = Column(Integer, ForeignKey('users.id'))
    paid = Column(Boolean, default=False)
    course_id = Column(Integer, ForeignKey('courses.id'))
    course = relationship('Course', back_populates='orders')
    user = relationship('User', back_populates='orders')

class BotSettings(Base):
    __tablename__ = 'bot_settings'
    id = Column(Integer, primary_key=True)
    welcome_message = Column(String)
    welcome_video_id = Column(String)
    author_phone_number = Column(String)
    author_telegram = Column(String)
    author_telegram_public = Column(String)
    author_instagram = Column(String)
    author_instagram_public = Column(String)
    author_vk = Column(String)
    author_vk_public = Column(String)

class Admins(Base):
    __tablename__ = 'admins'
    id = Column(Integer, primary_key=True)
    user_telegram_id = Column(BigInteger)
    user_name = Column(String)
    

Base.metadata.create_all(bind=engine)
