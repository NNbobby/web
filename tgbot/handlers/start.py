from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.user_kbs import main_kb
from keyboards.inline_kbs import ease_link_kb
from keyboards.adm_kbs import adm_main_kb, select_role_kb
from create_bot import admins
from db_handler.db_class import add_user
from datetime import datetime
import uuid

class Form(StatesGroup): 
    tele_id = State()
    username = State()
    role = State()

start_router = Router()

status_store = {}

@start_router.callback_query(F.data.startswith("confirm"))
async def callback_confirm(callback: CallbackQuery):
    """Обрабатываем подтверждение входа"""
    # Получаем токен из callback_data
    token = callback.data.split(":")[1]

    # Сохраняем статус во временное хранилище
    status_store[token] = "confirmed"

    # Уведомляем пользователя
    await callback.message.edit_text("✅ Вы успешно подтвердили вход. Вернитесь на сайт.")

@start_router.callback_query(F.data.startswith("block"))
async def callback_block(callback: CallbackQuery):
    """Обрабатываем блокировку IP"""
    token = callback.data.split(":")[1]

    # Сохраняем статус во временное хранилище
    status_store[token] = "blocked"

    # Уведомляем пользователя
    await callback.message.edit_text("❌ Вы успешно заблокировали IP. Действие отменено.")

@start_router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer('Запуск сообщения по команде /start используя фильтр CommandStart()', reply_markup=main_kb(message.from_user.id))

@start_router.message(Command('start_2'))
async def cmd_start_2(message: Message):
    await message.answer('Запуск сообщения по команде /start_2 используя фильтр Command()')

@start_router.message(F.text == '/start_3')
async def cmd_start_3(message: Message):
    await message.answer('Запуск сообщения по команде /start_3 используя магический фильтр F.text!')

@start_router.message(F.text == 'Давай инлайн!')
async def get_inline_btn_link(message: Message):
    await message.answer('Вот тебе инлайн клавиатура со ссылками!', reply_markup=ease_link_kb())

@start_router.message(F.text == '⚙️ Админ панель')
async def adm_panel(message: Message):
    tgid = message.from_user.id
    if tgid in admins:
        await message.answer('Админ панель запущена, чтобы вернуться в режим пользователя нажмите соотвтствующую кнопку', reply_markup=adm_main_kb(message.from_user.id))
    else:
        pass

@start_router.message(F.text == 'Выдать и привязать ключ')
async def new_key(message: Message, state: FSMContext):
    tgid = message.from_user.id
    if tgid in admins:
        await message.answer('Введите TGID нового пользователя')
        await state.set_state(Form.tele_id)

    else:
        pass

@start_router.message(F.text, Form.tele_id)
async def capture_id(message: Message, state: FSMContext):
    tgid = message.from_user.id
    if tgid in admins:
        await state.update_data(tele_id=message.text)
        await message.answer('Введите username нового пользователя, без @')
        await state.set_state(Form.username)
    else:
        pass

@start_router.message(F.text, Form.username)
async def capture_tag(message: Message, state: FSMContext):
    tgid = message.from_user.id
    if tgid in admins:
        await state.update_data(username=message.text)
        await message.answer('Выберите права доступа:', reply_markup=select_role_kb(message.from_user.id))
        await state.set_state(Form.role)
        await state.update_data(username=message.text)
    else:
        pass

@start_router.message(F.text, Form.role)
async def capture_role(message: Message, state: FSMContext):
    tgid = message.from_user.id  # ID текущего администратора
    if tgid in admins:
        # Определяем роль в зависимости от текста сообщения
        if message.text == 'Трейдер':
            role = 'trader'
        elif message.text == 'Администратор':
            role = 'admin'
        elif message.text == 'Клиент':
            role = 'client'
        elif message.text == 'Отмена':
            await state.finish()
            await message.answer('Действие отменено')
            return
        
        await state.update_data(role=role)
        
        # Получаем данные пользователя из состояния
        data = await state.get_data()
        tele_id = int(data.get("tele_id"))
        username = data.get("username")
        
        # Генерируем токен и текущую дату для записи в базу данных
        token = uuid.uuid4()
        date_reg = datetime.now()
        print(date_reg)

        # Вызываем функцию для записи данных в базу данных
        try:
            await add_user(
                added_by=tgid,
                tele_id=tele_id,
                username=username,
                role=role,
                date_reg=date_reg,
                token=token
            )
            # Если успешно, отправляем подтверждение
            msg_text = (f'Ключ успешно выдан в соответствии с введенными данными:\n'
                        f'TGID: <b>{tele_id}</b>\n'
                        f'UserName: <b>{username}</b>\n'
                        f'Роль: <b>{role}</b>\n'
                        f'Token: <b>{token}</b>')
            await message.answer(msg_text, parse_mode='HTML')
        except Exception as e:
            # В случае ошибки информируем администратора
            await message.answer('Произошла ошибка при добавлении пользователя в базу данных.')
            print(f"Ошибка: {e}")

        await state.clear()  # Очищаем состояние после обработки
    else:
        await message.answer('У вас нет прав для выполнения этой операции.')