import logging
from aiogram import Bot, Dispatcher
import config
from aiogram.enums.parse_mode import ParseMode


logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.API_TOKEN, parse_mode=ParseMode.HTML)

