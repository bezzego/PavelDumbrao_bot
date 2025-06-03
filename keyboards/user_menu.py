from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Уроки")],
        [KeyboardButton(text="Баланс"), KeyboardButton(text="Магазин")],
        [KeyboardButton(text="Пригласить"), KeyboardButton(text="Друзья")],
        [KeyboardButton(text="Подарок"), KeyboardButton(text="Топ")],
        [KeyboardButton(text="Закрытый"), KeyboardButton(text="Сотрудничество")],
        [KeyboardButton(text="Вход"), KeyboardButton(text="Поддержка")],
    ],
    resize_keyboard=True,
)
