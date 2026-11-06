"""Portfolio-friendly adaptation of a course Telegram bot.

No customer intellectual property, tokens, live users, proprietary URLs or media.
PAYMENT_MODE=demo is the default: it never charges a user.
"""
import logging
import random
from datetime import datetime, timezone

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputFile,
    LabeledPrice,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)

from config import BASE_DIR, Config, load_config
from content import COURSE_TITLE, COURSE_DESCRIPTION, LESSONS, DAILY_MESSAGES, TIPS
from services import daily_available, valid_checkout
from storage import Storage

LOG = logging.getLogger(__name__)
MAIN, COURSE, READY, BUY, DAILY, TIPS_STATE, CONSULT = range(7)
BACK = "На главную"


def keyboard(rows):
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def current_user(update: Update):
    user = update.effective_user
    return user.id, user.username or user.first_name or "User"


def resources(context: ContextTypes.DEFAULT_TYPE):
    return context.application.bot_data["storage"], context.application.bot_data["config"]


async def notify_admin(context: ContextTypes.DEFAULT_TYPE, message: str):
    _, config = resources(context)
    if config.admin_id is None:
        return
    try:
        await context.bot.send_message(chat_id=config.admin_id, text=message)
    except Exception:
        LOG.warning("Admin notification failed")


async def show_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage, _ = resources(context)
    uid, username = current_user(update)
    storage.touch_user(uid, username)
    await update.effective_message.reply_text(
        "Привет! Это демонстрационный обучающий бот. Выбери раздел:",
        reply_markup=keyboard([
            ["Курс", "Консультация"],
            ["Советы", "Шутка дня"],
        ]),
    )
    return MAIN


async def show_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage, _ = resources(context)
    uid, _ = current_user(update)
    user = storage.get_user(uid)
    if not user or not user["has_access"]:
        await update.effective_message.reply_text(
            COURSE_DESCRIPTION + "\n\nДля доступа нажми «Продолжить».",
            reply_markup=keyboard([["Продолжить"], [BACK]]),
        )
        return READY

    await update.effective_message.reply_text(
        "Выбери урок:",
        reply_markup=keyboard([["Урок 1", "Урок 2", "Урок 3"], [BACK]]),
    )
    return COURSE


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.effective_message.text
    if choice == "Курс":
        return await show_course(update, context)
    if choice == "Консультация":
        await update.effective_message.reply_text(
            "Опиши вопрос одним сообщением. Он будет сохранён в локальной демо-базе.",
            reply_markup=keyboard([[BACK]]),
        )
        return CONSULT
    if choice == "Советы":
        return await show_tips(update, context)
    if choice == "Шутка дня":
        return await show_daily(update, context)

    await update.effective_message.reply_text("Выбери вариант с клавиатуры.")
    return MAIN


async def ready(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.effective_message.text
    if choice == BACK:
        return await show_main(update, context)
    if choice != "Продолжить":
        await update.effective_message.reply_text("Нажми «Продолжить» или «На главную».")
        return READY

    storage, config = resources(context)
    uid, username = current_user(update)
    storage.touch_user(uid, username)

    if config.payment_mode == "demo":
        storage.set_access(uid)
        await update.effective_message.reply_text(
            "Демо-доступ открыт бесплатно. Настоящих платежей здесь нет."
        )
        return await show_course(update, context)

    # Optional real invoice integration. Disabled unless PAYMENT_MODE=telegram.
    await context.bot.send_invoice(
        chat_id=update.effective_chat.id,
        title=COURSE_TITLE,
        description="Доступ к демонстрационному учебному курсу",
        payload=f"demo_course_{uid}",
        provider_token=config.provider_token,
        currency=config.currency,
        prices=[LabeledPrice("Доступ к курсу", config.price_minor)],
    )
    await update.effective_message.reply_text(
        "Счёт отправлен. После успешной оплаты выбери «К урокам».",
        reply_markup=keyboard([["К урокам"], [BACK]]),
    )
    return BUY


async def buy_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_message.text == BACK:
        return await show_main(update, context)
    return await show_course(update, context)


async def pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _, config = resources(context)
    query = update.pre_checkout_query
    allowed = (config.payment_mode == "telegram" and valid_checkout(
        query.invoice_payload, query.from_user.id,
        query.total_amount, query.currency,
        config.price_minor, config.currency,
    ))
    await query.answer(
        ok=allowed,
        error_message=None if allowed else "Некорректные параметры заказа",
    )


async def payment_success(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage, config = resources(context)
    payment = update.effective_message.successful_payment
    uid, username = current_user(update)
    if config.payment_mode != "telegram" or not valid_checkout(
        payment.invoice_payload, uid, payment.total_amount,
        payment.currency, config.price_minor, config.currency,
    ):
        LOG.warning("Rejected unexpected payment event")
        return

    charge_id = payment.provider_payment_charge_id
    if not charge_id:
        LOG.warning("Payment without provider charge id not recorded")
        return

    storage.touch_user(uid, username)
    if storage.record_payment(uid, payment.total_amount, payment.currency, charge_id):
        await notify_admin(context, "Новый платёж в демонстрационном боте")
    await update.effective_message.reply_text(
        "Оплата подтверждена. Теперь доступ открыт. Нажми «К урокам».",
        reply_markup=keyboard([["К урокам"], [BACK]]),
    )


async def course_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text
    if text == BACK:
        return await show_main(update, context)

    storage, _ = resources(context)
    uid, _ = current_user(update)
    if not (storage.get_user(uid) or {}).get("has_access", False):
        return await show_course(update, context)

    if not text.startswith("Урок ") or not text[-1:].isdigit():
        await update.effective_message.reply_text("Выбери урок из меню.")
        return COURSE
    number = int(text.removeprefix("Урок "))
    lesson = LESSONS.get(number)
    if lesson is None:
        await update.effective_message.reply_text("Такого урока нет.")
        return COURSE

    response = f"{lesson['title']}\n\n{lesson['content']}\n\nДЗ: {lesson['homework']}"
    if lesson["video_url"]:
        response += f"\n\nВидео: {lesson['video_url']}"
    await update.effective_message.reply_text(response)
    storage.set_lesson(uid, number)
    if number == max(LESSONS):
        # Only a text placeholder, no client-owned mind maps or private links.
        await update.effective_message.reply_text(
            "Курс завершён! Составь собственную шпаргалку по пройденному."
        )
    return COURSE


async def show_daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage, _ = resources(context)
    uid, username = current_user(update)
    storage.touch_user(uid, username)
    user = storage.get_user(uid)
    allowed, remaining = daily_available(user["last_daily_message_at"])
    if allowed:
        storage.set_last_daily(uid, datetime.now(timezone.utc).isoformat())
        message = random.choice(DAILY_MESSAGES)
    else:
        hours, minutes = divmod(int(remaining.total_seconds() // 60), 60)
        message = f"Следующее сообщение можно получить через {hours} ч {minutes} мин."

    await update.effective_message.reply_text(message,
        reply_markup=keyboard([[BACK]]))
    return DAILY


async def daily_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_message.text == BACK:
        return await show_main(update, context)
    return await show_daily(update, context)


async def show_tips(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [[InlineKeyboardButton(item["title"], callback_data=key)]
               for key, item in TIPS.items()]
    await update.effective_message.reply_text(
        "Демонстрационные советы (видео не включены в репозиторий):",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    await update.effective_message.reply_text(
        "Для выхода используй кнопку ниже:",
        reply_markup=keyboard([[BACK]]),
    )
    return TIPS_STATE


async def tip_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tip = TIPS.get(query.data)
    if not tip:
        await query.message.reply_text("Совет не найден.")
        return TIPS_STATE

    media = BASE_DIR / "assets" / tip["media_name"]
    if media.is_file():
        try:
            with media.open("rb") as stream:
                await query.message.reply_video(
                    video=InputFile(stream, filename=media.name),
                    caption=tip["title"],
                )
        except Exception:
            LOG.warning("Media sending failed")
            await query.message.reply_text("Не удалось отправить демо-видео.")
    else:
        await query.message.reply_text(
            tip["title"] + " — пример видео не приложен."
        )
    return TIPS_STATE


async def tips_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_message.text == BACK:
        return await show_main(update, context)
    await update.effective_message.reply_text("Выбери совет выше или вернись на главную.")
    return TIPS_STATE


async def consultation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message.text
    if message == BACK:
        return await show_main(update, context)
    if len(message.strip()) < 3 or len(message) > 2000:
        await update.effective_message.reply_text("Напиши запрос длиной от 3 до 2000 символов.")
        return CONSULT

    storage, _ = resources(context)
    uid, username = current_user(update)
    storage.touch_user(uid, username)
    storage.save_request(uid, message)
    await notify_admin(context, "Новая заявка в демонстрационном боте. Проверь локальную БД.")
    await update.effective_message.reply_text("Заявка сохранена в демо-базе.")
    return await show_main(update, context)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    # Avoid logging entire updates, usernames, message content or payment payloads.
    LOG.error("Unhandled bot error of type: %s", type(context.error).__name__)


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    config: Config = load_config()
    storage = Storage(config.database_path)
    storage.init_db()

    application = Application.builder().token(config.bot_token).build()
    application.bot_data["storage"] = storage
    application.bot_data["config"] = config

    # Payment callbacks can arrive while user is in the BUY conversation state.
    application.add_handler(PreCheckoutQueryHandler(pre_checkout))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, payment_success))

    conversation = ConversationHandler(
        entry_points=[CommandHandler("start", show_main)],
        states={
            MAIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu)],
            COURSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, course_menu)],
            READY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ready)],
            BUY: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_state)],
            DAILY: [MessageHandler(filters.TEXT & ~filters.COMMAND, daily_state)],
            TIPS_STATE: [
                CallbackQueryHandler(tip_callback),
                MessageHandler(filters.TEXT & ~filters.COMMAND, tips_state),
            ],
            CONSULT: [MessageHandler(filters.TEXT & ~filters.COMMAND, consultation)],
        },
        fallbacks=[CommandHandler("cancel", show_main)],
        allow_reentry=True,
    )
    application.add_handler(conversation)
    application.add_error_handler(error_handler)
    application.run_polling()


if __name__ == "__main__":
    main()
