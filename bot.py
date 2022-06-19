import datetime
import logging

import requests
from aiogram import Bot, Dispatcher, executor, types, utils

# -------------------------------------------------------------------------------------- #
from fake_useragent import UserAgent

API_TOKEN = 'token from @BotFather'
API_KEY = 'key from openweathermap.org'
# -------------------------------------------------------------------------------------- #

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN, parse_mode="html")
dp = Dispatcher(bot)


def get_keyboard():
    keyboard = types.ReplyKeyboardMarkup()
    button = types.KeyboardButton("Определить город", request_location=True)
    keyboard.add(button)
    return keyboard


def get_weather(lat, lon):
    link = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=ru'
    response = requests.get(link, headers={'User-Agent': UserAgent().chrome})
    q = response.json()
    weather = {

        'city': q['name'],
        'main': q['weather'][0]['description'],
        'temp': q['main']['temp'],
        'humidity': q['main']['humidity'],
        'wind_speed': q['wind']['speed'],

    }
    return weather


@dp.message_handler(content_types=['location'])
async def handle_location(message: types.Message):
    lat = message.location.latitude
    lon = message.location.longitude
    d = get_weather(lat, lon)
    temp = '+' + str(int(d['temp'])) if d['temp'] > 0 else d['temp']
    reply = "Ваш город - {}".format(d['city'])
    forecast = "<b>{} | СЕГОДНЯ, {}</b>\n" \
               "{}, {}°\n" \
               "💨 Ветер {} м/с\n" \
               "💧 Влажность: {}%".format(d['city'].upper(), datetime.date.today(), d['main'].capitalize(), temp,
                                          d['wind_speed'], d['humidity'])

    await message.answer(reply, reply_markup=types.ReplyKeyboardRemove())
    await message.answer(forecast, reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    reply = "Для начала необходимо определить ваше местоположение"
    await message.answer(reply, reply_markup=get_keyboard())


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
