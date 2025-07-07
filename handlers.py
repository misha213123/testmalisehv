from aiogram import Router, types, F, Bot
from aiogram.filters.command import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardRemove

from keyboards import MODULES, modules_keyboard, module_options_keyboard
from config import ADMIN_ID

router = Router()

class Form(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Привет! 👋\nТы на старте своего пути в Авито-продажах 🚀\n\n"
        "Здесь ты найдёшь пошаговые уроки, которые помогут начать и прокачать свой бизнес.\n"
        "Выбери модуль ниже, чтобы начать обучение и быстро получить результат!",
        reply_markup=modules_keyboard()
    )

@router.message(lambda message: message.text in MODULES)
async def show_module_info(message: types.Message, state: FSMContext):
    module_name = message.text
    desc = MODULES[module_name]

    data = await state.get_data()
    done_modules = data.get("done_modules", [])
    done = module_name in done_modules

    await state.update_data(current_module=module_name)
    keyboard = module_options_keyboard(done)

    status_text = "✅ Пройден" if done else "❌ Не пройден"
    await message.answer(
        f"<b>{module_name}</b>\n\n{desc}\n\nСтатус: {status_text}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.message(lambda message: message.text == "✅ Отметить как пройдено")
async def mark_done_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    module_name = data.get("current_module")
    if not module_name:
        await message.answer("Пожалуйста, сначала выбери модуль из списка.")
        return

    done_modules = data.get("done_modules", [])
    if module_name not in done_modules:
        done_modules.append(module_name)
        await state.update_data(done_modules=done_modules)

    await message.answer(
        f"Модуль <b>{module_name}</b> отмечен как пройденный ✅",
        reply_markup=modules_keyboard(),
        parse_mode="HTML"
    )
    await state.update_data(current_module=None)

@router.message(lambda message: message.text == "⬅ Назад")
async def back_to_menu_handler(message: types.Message, state: FSMContext):
    await state.update_data(current_module=None)
    await message.answer(
        "Выбери модуль для начала обучения:",
        reply_markup=modules_keyboard()
    )

@router.message(F.text == "📩 Оставить заявку")
async def ask_name(message: types.Message, state: FSMContext):
    await state.set_state(Form.waiting_for_name)
    await message.answer("Отлично! Напиши, пожалуйста, своё имя.", reply_markup=ReplyKeyboardRemove())

@router.message(Form.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Form.waiting_for_phone)
    await message.answer("Спасибо! Теперь напиши свой контактный номер телефона.")

@router.message(Form.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext, bot: Bot):
    phone = message.text.strip()
    clean_phone = phone[1:] if phone.startswith("+") else phone

    if not clean_phone.isdigit():
        await message.answer("Номер телефона должен содержать только цифры (возможно, с плюсом в начале). Попробуй ещё раз.")
        return

    await state.update_data(phone=phone)
    data = await state.get_data()
    name = data.get("name")
    username = message.from_user.username or "нет ника"

    await bot.send_message(
        ADMIN_ID,
        f"📩 Новая заявка!\n\nИмя: {name}\nТелефон: {phone}\nTelegram: @{username}\n\nСвяжитесь с этим человеком как можно скорее."
    )

    await message.answer(
        f"Спасибо, {name}! Мы получили твою заявку с номером: {phone}.\n"
        "Скоро с тобой свяжется наш менеджер.",
        reply_markup=modules_keyboard()
    )
    await state.clear()

@router.message(F.text == "❓ Помощь")
async def help_command(message: types.Message):
    await message.answer(
        "Если есть вопросы, пиши напрямую @first025 или в поддержку курса Aviclub."
    )

@router.message(F.text == "ℹ️ О боте")
async def info_command(message: types.Message):
    await message.answer(
        "Этот бот помогает освоить Авито-продажи по шагам.\n"
        "Здесь ты найдёшь уроки, советы и поддержку на пути к успешным продажам.\n"
        "Проходи модули, отмечай успехи и задавай вопросы!"
    )

@router.message(Command(commands=["help"]))
async def help_cmd(message: types.Message):
    await help_command(message)

@router.message(Command(commands=["info"]))
async def info_cmd(message: types.Message):
    await info_command(message)

@router.message()
async def unknown_message(message: types.Message):
    await message.answer("Пожалуйста, выбери одну из кнопок ниже 👇", reply_markup=modules_keyboard())
