import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# إعداد التسجيل (Logging)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ----------------- الإعدادات -----------------
TOKEN = "YOUR_BOT_TOKEN_HERE" 8423755070:AAEBIor_aPhnosUcSj1L8GM3Zr6Wx7sVBfI
ADMIN_ID = 123456789  8849146045
# بيانات وهمية (Demo Data)
users_db = {
    1001: {"name": "أحمد", "balance": 50, "blocked": False},
    1002: {"name": "سارة", "balance": 120, "blocked": False},
    1003: {"name": "خالد", "balance": 0, "blocked": False},
}
promo_codes = {}

# حالات التفاعل (States for ConversationHandler)
(
    WAITING_EDIT_BALANCE_ID,
    WAITING_EDIT_BALANCE_AMOUNT,
    WAITING_BAN_ID,
    WAITING_PROMO_NAME,
    WAITING_PROMO_AMOUNT,
    WAITING_OFFERS_TEXT,
    WAITING_GEMS_TEXT
) = range(7)


# ----------------- القائمة الرئيسية للوحة التحكم -----------------
def get_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("💰 تعديل رصيد", callback_data="admin_edit_balance")],
        [InlineKeyboardButton("👥 عرض عدد المستخدمين", callback_data="admin_count_users")],
        [InlineKeyboardButton("🎁 توزيع الإحالات للمستخدمين", callback_data="admin_distribute_referrals")],
        [InlineKeyboardButton("🚫 حظر مستخدم", callback_data="admin_ban_user")],
        [InlineKeyboardButton("🎉 تعديل قسم العروض والبونصات", callback_data="admin_edit_offers")],
        [InlineKeyboardButton("💎 تعديل استبدال الجواهر", callback_data="admin_edit_gems")],
        [InlineKeyboardButton("🎫 إنشاء كود هدية", callback_data="admin_create_code")]
    ]
    return InlineKeyboardMarkup(keyboard)


# ----------------- الأمر الرئيسي /admin -----------------
async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ عذراً، هذه اللوحة مخصصة للآدمين فقط.")
        return

    await update.message.reply_text(
        "🛠 **أهلاً بك في لوحة تحكم الآدمين (Demo Panel)**\nاختر العملية التي تريد إجراؤها:",
        parse_mode="Markdown",
        reply_markup=get_admin_keyboard()
    )


# ----------------- معالجة الضغط على الأزرار -----------------
async def handle_admin_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    # 1. عرض عدد المستخدمين
    if data == "admin_count_users":
        count = len(users_db)
        await query.message.reply_text(f"📊 **عدد مستخدمي البوت الحالي:** `{count}` مستخدم.", parse_mode="Markdown")

    # 2. توزيع الإحالات
    elif data == "admin_distribute_referrals":
        await query.message.reply_text("✅ **تم بدء عملية توزيع مكافآت الإحالات على جميع المستخدمين بنجاح!**")

    # 3. إلغاء أو العودة
    elif data == "cancel_action":
        await query.edit_message_text("❌ تم إلغاء العملية.")

    # 4. تأكيد حظر المستخدم (نعم)
    elif data.startswith("confirm_ban_"):
        user_to_ban = int(data.split("_")[2])
        if user_to_ban in users_db:
            users_db[user_to_ban]["blocked"] = True
        await query.edit_message_text(f"✅ **تم حظر المستخدم صاحب الـ ID (`{user_to_ban}`) بنجاح.**", parse_mode="Markdown")

    # 5. إلغاء حظر المستخدم (لا)
    elif data == "cancel_ban":
        await query.edit_message_text("❌ **تم إلغاء عملية الحظر.**")


# ----------------- 1. مسار تعديل الرصيد -----------------
async def start_edit_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🔢 أدخل ID المستخدم الذي تريد تعديل رصيده:")
    return WAITING_EDIT_BALANCE_ID

async def get_balance_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text.isdigit():
        await update.message.reply_text("⚠️ يرجى إدخال ID صحيح (أرقام فقط):")
        return WAITING_EDIT_BALANCE_ID

    context.user_data['target_user_id'] = int(text)
    await update.message.reply_text(f"💵 أدخل المبلغ/الرصيد الجديد لـ ID (`{text}`):", parse_mode="Markdown")
    return WAITING_EDIT_BALANCE_AMOUNT

async def save_new_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amount_text = update.message.text
    try:
        amount = float(amount_text)
    except ValueError:
        await update.message.reply_text("⚠️ يرجى إدخال قيمة مالية صحيحة:")
        return WAITING_EDIT_BALANCE_AMOUNT

    target_id = context.user_data['target_user_id']
    if target_id not in users_db:
        users_db[target_id] = {"name": "مستخدم جديد", "balance": 0, "blocked": False}
    
    users_db[target_id]["balance"] = amount
    await update.message.reply_text(
        f"✅ **تم تعديل رصيد المستخدم (`{target_id}`) بنجاح.**\nالرصيد الجديد: `{amount}`",
        parse_mode="Markdown"
    )
    return ConversationHandler.END


# ----------------- 2. مسار حظر مستخدم -----------------
async def start_ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🚫 أدخل ID المستخدم الذي تريد حظره:")
    return WAITING_BAN_ID

async def confirm_ban_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text.isdigit():
        await update.message.reply_text("⚠️ يرجى إدخال ID صحيح (أرقام فقط):")
        return WAITING_BAN_ID

    target_id = int(text)
    keyboard = [
        [
            InlineKeyboardButton("✅ نعم", callback_data=f"confirm_ban_{target_id}"),
            InlineKeyboardButton("❌ لا", callback_data="cancel_ban")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"❓ **هل أنت متأكد من أنك تريد حظر المستخدم صاحب الـ ID:** `{target_id}`؟",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )
    return ConversationHandler.END


# ----------------- 3. مسار إنشاء كود هدية -----------------
async def start_create_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🎫 **أنشئ كود هدية:**\nأدخل اسم/رمز الكود (مثال: `GIFT2026`):", parse_mode="Markdown")
    return WAITING_PROMO_NAME

async def get_promo_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code_name = update.message.text.strip()
    context.user_data['promo_name'] = code_name
    await update.message.reply_text(f"💰 أدخل مبلغ/قيمة الكود (`{code_name}`):", parse_mode="Markdown")
    return WAITING_PROMO_AMOUNT

async def save_promo_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amount_text = update.message.text
    try:
        amount = float(amount_text)
    except ValueError:
        await update.message.reply_text("⚠️ يرجى إدخال قيمة مادية صحيحة:")
        return WAITING_PROMO_AMOUNT

    code_name = context.user_data['promo_name']
    promo_codes[code_name] = amount

    # إظهار الكود بنمط Monospace ليُنسخ بضغطة واحدة
    msg = (
        "✅ **تم إنشاء كود الهدية بنجاح!**\n\n"
        f"🏷 **اسم الكود (اضغط للنسخ):**\n`{code_name}`\n\n"
        f"💵 **قيمة الكود:** `{amount}`"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")
    return ConversationHandler.END


# ----------------- 4. مسار تعديل العروض والبونصات -----------------
async def start_edit_offers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📝 أدخل نص العروض والبونصات الجديد:")
    return WAITING_OFFERS_TEXT

async def save_offers_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    offers_text = update.message.text
    await update.message.reply_text("✅ **تم تحديث قسم العروض والبونصات بنجاح!**")
    return ConversationHandler.END


# ----------------- 5. مسار تعديل استبدال الجواهر -----------------
async def start_edit_gems(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("💎 أدخل التعديلات والخيارات الجديدة لاستبدال الجواهر:")
    return WAITING_GEMS_TEXT

async def save_gems_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gems_text = update.message.text
    await update.message.reply_text("✅ **تم تحديث قائمة استبدال الجواهر بنجاح!**")
    return ConversationHandler.END


# ----------------- الإلغاء الشامل -----------------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ تم إلغاء العملية.")
    return ConversationHandler.END


# ----------------- تشغيل البوت -----------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # محاور المحادثات الفردية لكل أمر
    balance_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_edit_balance, pattern="^admin_edit_balance$")],
        states={
            WAITING_EDIT_BALANCE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_balance_user_id)],
            WAITING_EDIT_BALANCE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_balance)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    ban_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_ban_user, pattern="^admin_ban_user$")],
        states={
            WAITING_BAN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_ban_dialog)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    promo_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_create_code, pattern="^admin_create_code$")],
        states={
            WAITING_PROMO_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_promo_name)],
            WAITING_PROMO_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_promo_code)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    offers_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_edit_offers, pattern="^admin_edit_offers$")],
        states={
            WAITING_OFFERS_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_offers_text)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    gems_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_edit_gems, pattern="^admin_edit_gems$")],
        states={
            WAITING_GEMS_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_gems_text)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # إضافة الأوامر
    app.add_handler(CommandHandler("admin", admin_start))
    app.add_handler(balance_handler)
    app.add_handler(ban_handler)
    app.add_handler(promo_handler)
    app.add_handler(offers_handler)
    app.add_handler(gems_handler)
    app.add_handler(CallbackQueryHandler(handle_admin_callbacks))

    print("🤖 البوت يعمل الآن...")
    app.run_polling()


if __name__ == "__main__":
    main()
