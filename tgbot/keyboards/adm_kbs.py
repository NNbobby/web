from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from create_bot import admins

def adm_main_kb(user_telegram_id: int):
    if user_telegram_id in admins:
        kb_list = [
            [KeyboardButton(text="Выдать и привязать ключ"), KeyboardButton(text="👤 Профиль")],
            [KeyboardButton(text="📝 Заполнить анкету"), KeyboardButton(text="📚 Каталог"), KeyboardButton(text="Давай инлайн!")]
        ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb_list,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Воспользуйтесь меню:"
    )
    return keyboard

def select_role_kb(user_telegram_id: int):
    if user_telegram_id in admins:
        kb_list = [
            [KeyboardButton(text="Трейдер"), KeyboardButton(text="Клиент")],
            [KeyboardButton(text="Администратор"), KeyboardButton(text="Отмена")]
            ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb_list,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Выберите роль:"
    )
    return keyboard