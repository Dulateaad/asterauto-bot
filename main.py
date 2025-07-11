import os
import datetime
import openai
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)
from config import TELEGRAM_BOT_TOKEN, OPENAI_API_KEY

client = openai.OpenAI(api_key=OPENAI_API_KEY)
user_states = {}
user_results = {}

THEMES = {
    "Гарантия 365": {
        "presentation": "files/presentation.pdf",
        "video_url": "https://youtu.be/fdVDF42lehU",
        "quiz": [
            {
                "q": "1. Что входит в гарантийный ремонт по программе \"Гарантия 365\"?",
                "options": [
                    "A) Только работа", "B) Только запчасти", "C) Только расходные материалы",
                    "D) Работа, запчасти и расходные материалы"
                ],
                "answer": 3
            },
            {
                "q": "2. Есть ли ограничение по количеству обращений?",
                "options": [
                    "A) Да, не более трёх", "B) Да, не более пяти",
                    "C) Нет ограничений по количеству обращений", "D) Только одно обращение"
                ],
                "answer": 2
            },
            {
                "q": "3. Какой возраст и пробег допускается?",
                "options": [
                    "A) До 5 лет / 100 000 км", "B) До 10 лет / 150 000 км",
                    "C) До 7 лет / 200 000 км", "D) Без ограничений"
                ],
                "answer": 1
            },
            {
                "q": "4. Какая максимальная сумма лимита покрытия гарантии?",
                "options": [
                    "A) 900 000 тенге", "B) 1 000 000 тенге",
                    "C) 1 310 000 тенге", "D) 1 500 000 тенге"
                ],
                "answer": 2
            },
            {
                "q": "5. Можно ли передать право на гарантию при продаже авто?",
                "options": [
                    "A) Нет", "B) Только за плату",
                    "C) Да, при соблюдении условий", "D) Только при продаже в этом же салоне"
                ],
                "answer": 2
            },
            {
                "q": "6. Какие есть способы оплаты гарантии?",
                "options": [
                    "A) Только наличными", "B) Только в рассрочку",
                    "C) Кредит или наличными", "D) Только безналично"
                ],
                "answer": 2
            },
            {
                "q": "7. Входит ли бесплатное первое ТО?",
                "options": [
                    "A) Нет", "B) Да", "C) Только за доплату", "D) Только при 2 пакетах"
                ],
                "answer": 1
            },
            {
                "q": "8. Можно ли оформить гарантию на отдельный агрегат?",
                "options": [
                    "A) Нет", "B) Да", "C) Только на двигатель", "D) Только при кредите"
                ],
                "answer": 1
            },
            {
                "q": "9. Что делает сервис после продажи гарантии?",
                "options": [
                    "A) Ничего", "B) ТО, маркировка, фото",
                    "C) Проверка кредитоспособности", "D) Подписание договора"
                ],
                "answer": 1
            },
            {
                "q": "10. Какая максимальная выгода при покупке пакетов?",
                "options": [
                    "A) 50 тыс", "B) 70 тыс", "C) 80 тыс", "D) 100 тыс"
                ],
                "answer": 2
            }
        ]
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup(
        [["📌 Гарантия 365"], ["📂 Мои результаты", "❓ Задать вопрос"]],
        resize_keyboard=True
    )
    await update.message.reply_text("👋 Добро пожаловать! Выберите тему:", reply_markup=keyboard)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if text == "📌 Гарантия 365":
        user_states[user_id] = {"mode": "theme", "theme": "Гарантия 365", "current": 0, "score": 0}
        await update.message.reply_text("📄 Презентация:")
        await update.message.reply_document(open(THEMES["Гарантия 365"]["presentation"], "rb"))
        await update.message.reply_text(f"🎬 Видео: {THEMES['Гарантия 365']['video_url']}")
        await update.message.reply_text(
            "🧪 Когда будете готовы, нажмите кнопку ниже для начала квиза.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🧪 Пройти квиз", callback_data="start_quiz")]
            ])
        )
        return

    if text == "📂 Мои результаты":
        results = user_results.get(user_id, [])
        if not results:
            await update.message.reply_text("📭 Вы ещё не проходили квизы.")
        else:
            text = "🗂 Ваши результаты:\n" + "\n".join(
                [f"• {r['theme']} — {r['score']}/{r['total']} ({r['date']})" for r in results]
            )
            await update.message.reply_text(text)
        return

    if text == "❓ Задать вопрос":
        user_states[user_id] = {"mode": "chat"}
        await update.message.reply_text("✍️ Введите свой вопрос:")
        return

    if user_states.get(user_id, {}).get("mode") == "chat":
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты — помощник AsterAuto. Отвечай кратко и по делу."},
                    {"role": "user", "content": text}
                ]
            )
            await update.message.reply_text(response.choices[0].message.content.strip())
        except Exception as e:
            await update.message.reply_text(f"⚠ Ошибка OpenAI: {str(e)}")
        return

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    data = query.data

    if data == "start_quiz":
        user_states[user_id]["mode"] = "quiz"
        user_states[user_id]["current"] = 0
        user_states[user_id]["score"] = 0
        await send_question(update, context, user_id)
        return

    if ":" in data:
        q_index, selected = map(int, data.split(":"))
        theme = user_states[user_id]["theme"]
        quiz = THEMES[theme]["quiz"]
        correct = quiz[q_index]["answer"]
        if selected == correct:
            user_states[user_id]["score"] += 1
        user_states[user_id]["current"] += 1
        await send_question(update, context, user_id)

async def send_question(update_or_query, context, user_id):
    state = user_states[user_id]
    theme = state["theme"]
    quiz = THEMES[theme]["quiz"]
    index = state["current"]

    if index >= len(quiz):
        score = state["score"]
        total = len(quiz)
        user_results.setdefault(user_id, []).append({
            "theme": theme,
            "score": score,
            "total": total,
            "date": datetime.datetime.now().strftime("%Y-%m-%d")
        })
        user_states[user_id]["mode"] = "theme"
        await context.bot.send_message(
            chat_id=user_id,
            text=f"✅ Квиз завершён!\nВы ответили правильно на {score} из {total}."
        )
        return

    q = quiz[index]
    buttons = [[InlineKeyboardButton(opt, callback_data=f"{index}:{i}")] for i, opt in enumerate(q["options"])]
    await context.bot.send_message(chat_id=user_id, text=f"🧪 {q['q']}", reply_markup=InlineKeyboardMarkup(buttons))

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    print("🚀 Бот AsterAuto запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
