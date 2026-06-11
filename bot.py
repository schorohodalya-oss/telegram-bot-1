from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import json
import os

import os
TOKEN = os.getenv("TOKEN")
ADMIN_ID = 7055964964

DATA_FILE = "orders.json"

ORDER_ID = 0
active_orders = {}

# -------------------------
# загрузка данных
# -------------------------
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        active_orders = json.load(f)
        ORDER_ID = len(active_orders)

# -------------------------
# сохранение данных
# -------------------------
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(active_orders, f, ensure_ascii=False, indent=2)


keyboard = [
    ["🔮 Услуги и цены"],
    ["📝 Оформить заявку"],
    ["💳 Оплата", "⭐ Отзывы"],
    ["🎁 Бонусы"]
]

reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ Добро пожаловать!\nЯ бот-помощник.",
        reply_markup=reply_markup
    )


# TEXT HANDLER
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global ORDER_ID

    text = update.message.text
    user_id = str(update.message.chat_id)
    step = context.user_data.get("step")

    # защита от повторной заявки
    if text == "📝 Оформить заявку":
        if user_id in active_orders:
            await update.message.reply_text("⚠️ У вас уже есть активная заявка.")
            return

        context.user_data["step"] = "age"
        await update.message.reply_text("Введите возраст:")
        return

    # анкета
    if step == "age":
        context.user_data["age"] = text
        context.user_data["step"] = "nick"
        await update.message.reply_text("Введите ник:")
        return

    elif step == "nick":
        context.user_data["nick"] = text
        context.user_data["step"] = "service"
        await update.message.reply_text("Услуга:")
        return

    elif step == "service":
        context.user_data["service"] = text
        context.user_data["step"] = "details"
        await update.message.reply_text("Опишите ситуацию:")
        return

    elif step == "details":

        context.user_data["details"] = text

        ORDER_ID += 1

        order = {
            "id": ORDER_ID,
            "user_id": user_id,
            "status": "pending",
            **context.user_data
        }

        active_orders[user_id] = order
        save_data()

        await update.message.reply_text("✨ Заявка принята. Мы свяжемся с вами.")

        keyboard_admin = [
            [InlineKeyboardButton("📌 В работу", callback_data=f"work_{ORDER_ID}")],
            [InlineKeyboardButton("❌ Завершить", callback_data=f"done_{ORDER_ID}")]
        ]

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=
            f"🆕 Заявка #{ORDER_ID}\n\n"
            f"Возраст: {order['age']}\n"
            f"Ник: {order['nick']}\n"
            f"Услуга: {order['service']}\n"
            f"Описание: {order['details']}",
            reply_markup=InlineKeyboardMarkup(keyboard_admin)
        )

        context.user_data.clear()
        return

    # меню
    if text == "🔮 Услуги и цены":
        await update.message.reply_text("Список услуг...")

    elif text == "💳 Оплата":
        await update.message.reply_text("Реквизиты...")

    elif text == "⭐ Отзывы":
        await update.message.reply_text("Отзывы...")

    elif text == "🎁 Бонусы":
        await update.message.reply_text("Бонусы...")

    else:
        await update.message.reply_text("Нажмите кнопку меню.")


# ADMIN CONTROL
async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    global active_orders

    if data.startswith("work_"):
        order_id = int(data.split("_")[1])

        for uid in active_orders:
            if active_orders[uid]["id"] == order_id:
                active_orders[uid]["status"] = "active"

        save_data()
        await query.edit_message_text(f"📌 Заявка #{order_id} в работе")

    elif data.startswith("done_"):
        order_id = int(data.split("_")[1])

        for uid in list(active_orders.keys()):
            if active_orders[uid]["id"] == order_id:
                del active_orders[uid]

        save_data()
        await query.edit_message_text(f"❌ Заявка #{order_id} завершена")


# RUN
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(CallbackQueryHandler(admin_buttons))

print("Бот запущен...")
app.run_polling()
