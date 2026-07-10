import asyncio
import time
import random
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton, 
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)

TOKEN = "8947092834:AAECJfqA6e7SZgWNzzyv7PTexRbGQs4LJwk"

bot = Bot(token=TOKEN)
dp = Dispatcher()

users_db = {}

class SupportStates(StatesGroup):
    waiting_for_suggestion = State()
    waiting_for_question = State()

HOUSES = {
    "tree": {"name": "🏠 Дом на дереве", "price": 10, "boost_text": "+1 алмаз к клику", "boost_type": "add", "value": 1},
    "villa": {"name": "🏡 Хай-тек Вилла", "price": 100, "boost_text": "x2 алмазов за клик", "boost_type": "mult", "value": 2},
    "castle": {"name": "🏰 Гравитационный Замок", "price": 1000, "boost_text": "x5 алмазов за клик", "boost_type": "mult", "value": 5}
}

CARS = {
    "pickup": {"name": "🛻 Ржавый пикап", "price": 15},
    "sport": {"name": "🏎 Кубический Спорткар", "price": 250},
    "cybertruck": {"name": "📐 Кибертрак (RTX Edition)", "price": 2000}
}

BUSINESSES = {
    "store247": {"name": "🏪 Магазин 24/7", "price": 5000, "income": 1000, "interval": 1800},
    "landstore": {"name": "🚜 Магазин за землю", "price": 10000, "income": 5000, "interval": 3600}
}

IMAGES = {
    "profile": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=600",
    "mine": "https://images.unsplash.com/photo-1518364538800-6bcb3f25da49?q=80&w=600",
    "shop": "https://images.unsplash.com/photo-1604719312566-8912e9227c6a?q=80&w=600",
    "exchange": "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=600",
    "top": "https://images.unsplash.com/photo-1531538606174-0f90ff5dce83?q=80&w=600",
    "support": "https://images.unsplash.com/photo-1521791136368-1a46827d0fa1?q=80&w=600"
}

def get_main_keyboard():
    kb = [
        [KeyboardButton(text="🎒 Мой Профиль"), KeyboardButton(text="⛏ Пойти в шахту")],
        [KeyboardButton(text="🏪 Магазин"), KeyboardButton(text="💱 Обменник")],
        [KeyboardButton(text="🏆 Топ игроков"), KeyboardButton(text="📃 Поддержка")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def init_user(user_id: int, name: str):
    if user_id not in users_db:
        users_db[user_id] = {
            "name": name, "diamonds": 0, "dollars": 0,
            "house": None, "car": None, "business": None,
            "last_business_payout": 0, "last_mine_time": 0
        }

def update_passive_income(user_id: int):
    user = users_db[user_id]
    if not user["business"]: return 0
    biz_info = BUSINESSES[user["business"]]
    now = time.time()
    if user["last_business_payout"] == 0:
        user["last_business_payout"] = now
        return 0
    elapsed = now - user["last_business_payout"]
    intervals = int(elapsed // biz_info["interval"])
    if intervals > 0:
        earned = intervals * biz_info["income"]
        user["dollars"] += earned
        user["last_business_payout"] += intervals * biz_info["interval"]
        return earned
    return 0

def get_user_net_worth(user_id: int):
    user = users_db[user_id]
    worth = user["dollars"] + (user["diamonds"] / 50)
    if user["house"]: worth += HOUSES[user["house"]]["price"]
    if user["car"]: worth += CARS[user["car"]]["price"]
    if user["business"]: worth += BUSINESSES[user["business"]]["price"]
    return worth

@dp.message(CommandStart())
async def cmd_start(message: Message):
    init_user(message.from_user.id, message.from_user.first_name)
    await message.answer("🤖 Добро пожаловать в CubicDrive!", reply_markup=get_main_keyboard())

@dp.message(F.text == "🎒 Мой Профиль")
async def show_profile(message: Message):
    user_id = message.from_user.id
    init_user(user_id, message.from_user.first_name)
    income = update_passive_income(user_id)
    user = users_db[user_id]
    house_text = f"{HOUSES[user['house']]['name']}" if user["house"] else "Отсутствует"
    car_text = CARS[user["car"]]["name"] if user["car"] else "Пешеход 🚶"
    biz_text = BUSINESSES[user["business"]]["name"] if user["business"] else "Нет бизнеса"
    income_notify = f"\n\n💰 *Доход:* +{income} $" if income > 0 else ""
    profile_text = (
        f"🪪 *Профиль: {user['name']}*\n\n💎 *Алмазы:* {user['diamonds']} шт.\n💵 *Баланс:* {user['dollars']} $\n\n"
        f"🏠 *Дом:* {house_text}\n🚗 *Транспорт:* {car_text}\n🏢 *Бизнес:* {biz_text}{income_notify}"
    )
    await message.answer_photo(photo=IMAGES["profile"], caption=profile_text, parse_mode="Markdown")

@dp.message(F.text == "⛏ Пойти в шахту")
async def go_mining(message: Message):
    user_id = message.from_user.id
    init_user(user_id, message.from_user.first_name)
    user = users_db[user_id]
    current_time = time.time()
    if current_time - user["last_mine_time"] < 3:
        await message.answer("❌ Не удалось добыть, попробуйте снова!")
        return
    user["last_mine_time"] = current_time
    base_diamonds = random.randint(1, 5)
    if user["house"]:
        boost = HOUSES[user["house"]]
        earned = base_diamonds + boost["value"] if boost["boost_type"] == "add" else base_diamonds * boost["value"]
    else: earned = base_diamonds
    user["diamonds"] += earned
    await message.answer_photo(photo=IMAGES["mine"], caption=f"⛏ Вы добыли: *{earned} 💎*", parse_mode="Markdown")

@dp.message(F.text == "💱 Обменник")
async def show_exchange(message: Message):
    user_id = message.from_user.id
    init_user(user_id, message.from_user.first_name)
    user = users_db[user_id]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Обменять 50 💎 на 1 $", callback_data="ex_50")],
        [InlineKeyboardButton(text="Обменять все алмазы", callback_data="ex_all")]
    ])
    await message.answer_photo(photo=IMAGES["exchange"], caption=f"💱 *Курс: 50 💎 = 1 $*\nУ вас: *{user['diamonds']} 💎*", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("ex_"))
async def process_exchange(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = users_db[user_id]
    action = callback.data.split("_")[1]
    if user["diamonds"] < 50:
        await callback.answer("❌ Маловато алмазов!", show_alert=True)
        return
    if action == "50":
        user["diamonds"] -= 50
        user["dollars"] += 1
    elif action == "all":
        amt = user["diamonds"] // 50
        user["diamonds"] -= (amt * 50)
        user["dollars"] += amt
    await callback.message.edit_caption(caption=f"💵 Баланс обновлен: *{user['dollars']} $*", parse_mode="Markdown")

@dp.message(F.text == "🏪 Магазин")
async def show_shop(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Дома", callback_data="shop_houses"), InlineKeyboardButton(text="🚗 Авто", callback_data="shop_cars")],
        [InlineKeyboardButton(text="💼 Бизнес", callback_data="shop_biz")]
    ])
    await message.answer_photo(photo=IMAGES["shop"], caption="🏪 *Магазин*", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("shop_"))
async def open_shop_category(callback: CallbackQuery):
    cat = callback.data.split("_")[1]
    buttons = []
    user = users_db[callback.from_user.id]
    if cat == "houses":
        text = "🏠 *Дома (Буст кликера):*\n\n"
        for k, v in HOUSES.items():
            text += f"▪️ *{v['name']}* — {v['price']} $ ({v['boost_text']})\n"
            buttons.append([InlineKeyboardButton(text=f"Купить {v['name']}", callback_data=f"buy_h_{k}")])
    elif cat == "cars":
        text = "🚗 *Автосалон:*\n\n"
        for k, v in CARS.items():
            text += f"▪️ *{v['name']}* — {v['price']} $\n"
            buttons.append([InlineKeyboardButton(text=f"Купить {v['name']}", callback_data=f"buy_c_{k}")])
    elif cat == "biz":
        text = "💼 *Бизнес (Пассивный доход):\nМожно иметь только 1. Старый продается за 100%.*\n\n"
        for k, v in BUSINESSES.items():
            text += f"▪️ *{v['name']}* — {v['price']} $ (Доход: {v['income']} $)\n"
            buttons.append([InlineKeyboardButton(text=f"Купить {v['name']}", callback_data=f"buy_b_{k}")])
        if user["business"]:
            buttons.append([InlineKeyboardButton(text="❌ Продать бизнес", callback_data="sell_current_biz")])
    buttons.append([InlineKeyboardButton(text="⬅️ В магазин", callback_data="back_to_shop")])
    await callback.message.edit_caption(caption=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@dp.callback_query(F.data == "back_to_shop")
async def return_to_main_shop(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Дома", callback_data="shop_houses"), InlineKeyboardButton(text="🚗 Авто", callback_data="shop_cars")],
        [InlineKeyboardButton(text="💼 Бизнес", callback_data="shop_biz")]
    ])
    await message.answer_photo(photo=IMAGES["shop"], caption="🏪 *Магазин*", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "sell_current_biz")
async def sell_business(callback: CallbackQuery):
    user = users_db[callback.from_user.id]
    if user["business"]:
        biz = BUSINESSES[user["business"]]
        user["dollars"] += biz["price"]
        user["business"] = None
        user["last_business_payout"] = 0
        await callback.message.edit_caption(caption=f"✅ Бизнес продан за {biz['price']} $", parse_mode="Markdown")

@dp.callback_query(F.data.startswith("buy_"))
async def process_purchase(callback: CallbackQuery):
    user = users_db[callback.from_user.id]
    _, itype, ikey = callback.data.split("_")
    if itype == "h":
        item = HOUSES[ikey]
        if user["dollars"] < item["price"]:
            await callback.answer("Недостаточно денег!", show_alert=True)
            return
        user["dollars"] -= item["price"]
        user["house"] = ikey
    elif itype == "c":
        item = CARS[ikey]
        if user["dollars"] < item["price"]:
            await callback.answer("Недостаточно денег!", show_alert=True)
            return
        user["dollars"] -= item["price"]
        user["car"] = ikey
    elif itype == "b":
        item = BUSINESSES[ikey]
        if user["business"]:
            user["dollars"] += BUSINESSES[user["business"]]["price"]
        if user["dollars"] < item["price"]:
            await callback.answer("Недостаточно денег!", show_alert=True)
            return
        user["dollars"] -= item["price"]
        user["business"] = ikey
        user["last_business_payout"] = time.time()
    await callback.message.edit_caption(caption=f"🎉 Куплено: *{item['name']}*!", parse_mode="Markdown")

@dp.message(F.text == "🏆 Топ игроков")
async def show_top(message: Message):
    if not users_db:
        await message.answer("🏆 Топ пуст.")
        return
    sorted_users = sorted(users_db.keys(), key=get_user_net_worth, reverse=True)[:10]
    text = "🏆 *ТОП-10 Игроков:*\n\n"
    for i, uid in enumerate(sorted_users, 1):
        text += f"{i}. *{users_db[uid]['name']}* — {users_db[uid]['dollars']} $ | {users_db[uid]['diamonds']} 💎\n"
    await message.answer_photo(photo=IMAGES["top"], caption=text, parse_mode="Markdown")

@dp.message(F.text == "📃 Поддержка")
async def support_menu(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💡 Идея", callback_data="sup_idea"), InlineKeyboardButton(text="❓ Вопрос", callback_data="sup_ask")]
    ])
    await message.answer_photo(photo=IMAGES["support"], caption="📃 *Поддержка*", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("sup_"))
async def init_support_state(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]
    if action == "idea":
        await state.set_state(SupportStates.waiting_for_suggestion)
        await callback.message.answer("📝 Напиши свою идею:")
    else:
        await state.set_state(SupportStates.waiting_for_question)
        await callback.message.answer("❓ Напиши свой вопрос:")
    await callback.answer()

@dp.message(SupportStates.waiting_for_suggestion)
async def handle_suggestion(message: Message, state: FSMContext):
    await message.answer("✅ Идея отправлена!", reply_markup=get_main_keyboard())
    await state.clear()

@dp.message(SupportStates.waiting_for_question)
async def handle_question(message: Message, state: FSMContext):
    await message.answer("✅ Вопрос передан!", reply_markup=get_main_keyboard())
    await state.clear()

async def handle(request):
    return web.Response(text="CubicDrivebot Active")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
