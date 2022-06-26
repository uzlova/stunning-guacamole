import asyncio
import datetime
import logging
from asyncio import sleep, get_event_loop
import requests
from PIL import Image, ImageFont, ImageDraw
from aiogram import Bot, Dispatcher, executor, types, utils
from aiogram.types import InputFile
from fake_useragent import UserAgent

# -------------------------------------------------------------------------------------- #
API_TOKEN = 'token from @BotFather'
API_KEY = 'key from openweathermap.org'
user_data = {}
loop = asyncio.get_event_loop()
delay = 5.0
# -------------------------------------------------------------------------------------- #

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN, parse_mode="html")
dp = Dispatcher(bot)


def start_keyboard():
    button = types.KeyboardButton("📍 Определить город", request_location=True)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add(button)
    return keyboard


def keyboard():
    buttons = [
        '📊 Прогноз на 5 дней',
        '📆 Погода сейчас'
    ]
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True).add(*buttons)
    return keyboard


def get_weather(lat, lon):
    link = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=ru'
    response = requests.get(link, headers={'User-Agent': UserAgent().chrome})
    q = response.json()
    weather = {

        'main': q['weather'][0]['main'],
        'city': q['name'],
        'description': q['weather'][0]['description'],
        'temp': q['main']['temp'],
        'feels_like': q['main']['feels_like'],
        'humidity': q['main']['humidity'],
        'pressure': int(q['main']['pressure'] * 0.750064),
        'wind_speed': q['wind']['speed'],

    }
    return weather


def get_weather_forecast(lat, lon, n: int):
    link = f'http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=ru'
    response = requests.get(link, headers={'User-Agent': UserAgent().chrome})
    q = response.json()
    weather = {

        'main': q['list'][n]['weather'][0]['main'],
        'description': q['list'][n]['weather'][0]['description'],
        'temp': q['list'][n]['main']['temp'],
        'feels_like': q['list'][n]['main']['feels_like'],
        'humidity': q['list'][n]['main']['humidity'],
        'pressure': int(q['list'][n]['main']['pressure'] * 0.750064),
        'wind_speed': q['list'][n]['wind']['speed'],
        'chance_rain': int(q['list'][n]['pop']) * 100,

    }
    return weather


def get_img(main: str, temp, feels_like):
    im = Image.open('img/{}.jpg'.format(main.lower()))
    font = ImageFont.truetype("fonts/Montserrat-Bold.ttf", size=88)
    font2 = ImageFont.truetype("fonts/Montserrat-Bold.ttf", size=14)
    draw_text = ImageDraw.Draw(im)
    draw_text.text(
        (7, 55),
        '{}°'.format(temp),
        font=font,
        fill=('white')
    )
    draw_text.text(
        (285, 121),
        '{}°'.format(feels_like),
        font=font2,
        fill=('#BDBDBD')
    )
    #    im.show()
    im.save('img/del/1.jpg')
    return 0


@dp.message_handler(lambda message: message.text == "📆 Погода сейчас")
@dp.message_handler(content_types=['location'])
async def handle_location(message: types.Message):
    weather_to_emoji = {
        'clear': '☀️',
        'clouds': '⛅️',
        'rain': '🌧',
        'drizzle': '🌧'

    }

    month_list = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
    try:
        lat = message.location.latitude
        lon = message.location.longitude
        user_data[message.from_user.id] = (lat, lon)
    except AttributeError:
        lat, lon = user_data[message.from_user.id]

    d = get_weather(lat, lon)
    today = datetime.date.today()

    temp = '+' + str(int(d['temp'])) if d['temp'] > 0 else d['temp']
    feels_like = '+' + str(int(d['feels_like'])) if d['feels_like'] > 0 else d['feels_like']

    get_img(d['main'], temp, feels_like)

    forecast = "<b>🏘 {} \nСегодня, {}</b>\n" \
               "\n<i>{} {}, <b>{}°</b>, ощущается как {}°\n" \
               "💨 Ветер {} м/с\n" \
               "💧 Влажность воздуха: {}%\n" \
               "🌫Атмосферное давление {} мм рт. ст.</i>".format(d['city'],
                                                                 f"{today.day} {month_list[today.month - 1]}",
                                                                 weather_to_emoji[d['main'].lower()],
                                                                 d['description'].capitalize(), temp, feels_like,
                                                                 d['wind_speed'], d['humidity'],
                                                                 d['pressure'])

    await bot.send_photo(chat_id=message.chat.id, photo=InputFile('img/del/1.jpg'), caption=forecast,
                         reply_markup=keyboard())


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    reply = "Для начала необходимо определить ваше местоположение"
    await message.answer(reply, reply_markup=start_keyboard())


@dp.message_handler(lambda message: message.text == "📊 Прогноз на 5 дней")
async def forecast_for_5_days(message: types.Message):
    weather_to_emoji = {
        'clear': '☀️',
        'clouds': '⛅️',
        'rain': '🌧',
        'drizzle': '🌧'

    }

    lat, lon = user_data[message.from_user.id]
    link = f'http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}'

    response = requests.get(link, headers={'User-Agent': UserAgent().chrome})
    q = response.json()

    month_list = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']

    step = 8

    for i in range(9, int(q['cnt']), step):
        d = q['list'][i]['dt_txt']

        today = datetime.datetime.strptime(d, '%Y-%m-%d %H:%M:%S')
        dict_1 = get_weather_forecast(lat, lon, i)

        temp = '+' + str(int(dict_1['temp'])) if dict_1['temp'] > 0 else dict_1['temp']
        feels_like = '+' + str(int(dict_1['feels_like'])) if dict_1['feels_like'] > 0 else dict_1['feels_like']

        get_img(dict_1['main'], temp, feels_like)

        forecast = "<b>{}</b>\n" \
                   "\n<i>{} {}, <b>{}°</b>, ощущается как {}°\n" \
                   "💨 Ветер {} м/с\n" \
                   "💧 Влажность воздуха: {}%\n" \
                   "🌫Атмосферное давление {} мм рт. ст.</i>".format(f'{today.day} {month_list[today.month - 1]}',
                                                                     weather_to_emoji[dict_1['main'].lower()],
                                                                     dict_1['description'].capitalize(),
                                                                     temp, feels_like, dict_1['wind_speed'],
                                                                     dict_1['humidity'], dict_1['pressure'])
        await bot.send_photo(chat_id=message.chat.id, photo=InputFile('img/del/1.jpg'), caption=forecast,
                             reply_markup=keyboard())


async def forecast_today():
    for id, coordinates in user_data.items():
        lat, lon = coordinates


async def scheduled(wait: int):
    weather_to_emoji = {
        'clear': '☀️',
        'clouds': '⛅️',
        'rain': '🌧',
        'drizzle': '🌧'

    }

    while True:
        for id, values in user_data.items():
            lat, lon = values
            link = f'http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}'

            response = requests.get(link, headers={'User-Agent': UserAgent().chrome})
            q = response.json()

            month_list = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                          'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']

            d = q['list'][1]['dt_txt']

            today = datetime.datetime.strptime(d, '%Y-%m-%d %H:%M:%S')
            dict_1 = get_weather_forecast(lat, lon, 1)

            temp = '+' + str(int(dict_1['temp'])) if dict_1['temp'] > 0 else dict_1['temp']
            feels_like = '+' + str(int(dict_1['feels_like'])) if dict_1['feels_like'] > 0 else dict_1['feels_like']

            get_img(dict_1['main'], temp, feels_like)

            forecast = "<b>Сегодня, {}</b>\n" \
                       "\n<i>{} {}, <b>{}°</b>, ощущается как {}°\n" \
                       "💨 Ветер {} м/с\n" \
                       "💧 Влажность воздуха: {}%\n" \
                       "🌫Атмосферное давление {} мм рт. ст.</i>".format(f'{today.day} {month_list[today.month - 1]}',
                                                                         weather_to_emoji[dict_1['main'].lower()],
                                                                         dict_1['description'].capitalize(),
                                                                         temp, feels_like, dict_1['wind_speed'],
                                                                         dict_1['humidity'], dict_1['pressure'])
            await bot.send_photo(chat_id=id, photo=InputFile('img/del/1.jpg'), caption=forecast,
                                 reply_markup=keyboard())
        # ожидаем день
        await sleep(wait * 3600)


if __name__ == '__main__':
    get_event_loop().create_task(scheduled(24))
    executor.start_polling(dp, skip_updates=True)
