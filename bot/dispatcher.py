from aiogram import Bot, Dispatcher

from db import Config

bot = Bot(token=Config.TOKEN)
dp = Dispatcher()
