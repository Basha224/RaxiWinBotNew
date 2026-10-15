import logging
import threading
import os
import asyncio
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# ==========================================
# CONFIGURATION
# ==========================================
TOKEN ="8740602277:AAEnKeFd4N_MNjVA3WsqzMKztCpFkmHRorY"
ADMIN_ID = "@pro_earner_0" 
REGISTER_LINK = "https://www.raxiwin.game/#/register?invitationCode=74158275546"
TODAY_GIFT_CODE = "4346F170B0051BD21B95EE9DECBAC10C"
ADMIN_NUMERIC_ID = 6081001025

# Logs will be sent directly to your DM (no channel needed)
LOG_CHANNEL_ID = ADMIN_NUMERIC_ID
# ==========================================

known_users = set()

ASK_GAME_ID, ASK_TEAM_STATUS, DEPOSIT_MENU, DEPOSIT_HELP, WITHDRAW_HELP, HUMAN_AGENT, BROADCAST_MSG = range(7)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

app = Flask(__name__)
@app.route('/')
def home():
    return "RaxiWin Support Bot is running 24/7!"
def run_web_server():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- LOG FUNCTION ---
async def log_to_channel(bot, message: str):
    try:
        await bot.send_message(chat_id=LOG_CHANNEL_ID, text=message, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Log error: {e}")

# --- KEYWORD AUTO-REPLY DATABASE ---
KEYWORD_REPLIES = {
    "otp": ("📩", "OTP Not Received?",
        "Please try these steps:\n\n"
        "1️⃣ Wait 60 seconds — sometimes it takes time.\n"
        "2️⃣ Check if your phone has network signal.\n"
        "3️⃣ Restart your phone and try again.\n"
        "4️⃣ Don't request OTP more than 3 times in a row.\n\n"
        "Still not received? Contact admin: @pro_earner_0"),
    "password": ("🔑", "Password Help",
        "Your password must contain:\n\n"
        "✅ Capital letters (A-Z)\n"
        "✅ Small letters (a-z)\n"
        "✅ Numbers (0-9)\n\n"
        "❌ NO symbols like @ # $ % & !\n\n"
        "Forgot password? Use the 'Forgot Password' option on the login page."),
    "withdraw": ("🏧", "Withdrawal Guide",
        "To withdraw funds:\n\n"
        "1️⃣ Login to your account\n"
        "2️⃣ Go to Wallet → Payout\n"
        "3️⃣ Enter your Bank Account or UPI ID\n"
        "4️⃣ Enter amount (Min ₹200)\n"
        "5️⃣ Click Submit\n\n"
        "⚡ Most withdrawals process in 10-30 minutes.\n\n"
        "Still pending? Contact: @pro_earner_0"),
    "deposit": ("💵", "Deposit Guide",
        "To deposit funds:\n\n"
        "1️⃣ Login to your account\n"
        "2️⃣ Go to Wallet → Deposit\n"
        "3️⃣ Choose UPI / Bank transfer\n"
        "4️⃣ Enter amount (Min ₹100)\n"
        "5️⃣ Complete the payment\n\n"
        "⏱️ Balance updates within 5-10 minutes.\n\n"
        "Not credited? Contact: @pro_earner_0"),
    "login": ("🔓", "Login Help",
        "To login:\n\n"
        "1️⃣ Open RaxiWin app\n"
        "2️⃣ Click Login\n"
        "3️⃣ Enter your phone number or email\n"
        "4️⃣ Enter your password\n"
        "5️⃣ Complete OTP verification\n\n"
        "Can't login? Try resetting your password."),
    "register": ("📝", "Registration Help",
        "To register:\n\n"
        f"1️⃣ Click this link: {REGISTER_LINK}\n"
        "2️⃣ Enter your phone number\n"
        "3️⃣ Set password (letters + numbers only)\n"
        "4️⃣ Enter invitation code: 74158275546\n"
        "5️⃣ Complete registration"),
    "bonus": ("🎁", "Today's Bonus",
        f"Your gift code:\n\n`{TODAY_GIFT_CODE}`\n\n"
        "Copy it and redeem in the game's Bonus section.\n\n"
        "⚠️ Valid for 24 hours only."),
    "gift": ("🎁", "Today's Gift Code",
        f"`{TODAY_GIFT_CODE}`\n\n"
        "Copy this code and paste it in the game to claim your reward!"),
    "help": ("🆘", "Need Help?",
        "I can help you with:\n\n"
        "• Login / Register\n"
        "• Deposit / Withdraw\n"
        "• OTP issues\n"
        "• Password reset\n"
        "• Gift codes & bonuses\n\n"
        "Just type any of these words or click the menu button."),
}

async def keyword_auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    text = update.message.text.lower()
    user = update.effective_user
    known_users.add(user.id)
    for keyword, (emoji, title, reply) in KEYWORD_REPLIES.items():
        if keyword in text:
            keyboard = [
                [InlineKeyboardButton("💬 Contact Admin", url=f"https://t.me/{ADMIN_ID.replace('@', '')}")],
                [InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]
            ]
            await update.message.reply_text(f"{emoji} *{title}*\n\n{reply}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
            await log_to_channel(context.bot, f"🔍 *Keyword:* `{keyword}`\n👤 {user.first_name}\n🆔 `{user.id}`")
            return
    keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]]
    await update.message.reply_text(
        "🤔 I didn't understand that. Try keywords:\n\n"
        "• *otp*\n• *password*\n• *withdraw*\n• *deposit*\n• *login*\n• *register*\n• *bonus*\n\n"
        "Or use the menu button.",
        reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("🎁 Daily Gift Code", callback_data='gift')],
        [InlineKeyboardButton("🔗 My Referral Link", callback_data='referral')],
        [InlineKeyboardButton("💳 Deposit / Withdraw Help", callback_data='deposit')],
        [InlineKeyboardButton("❓ FAQ", callback_data='faq')],
        [InlineKeyboardButton("💬 Talk to Human Agent", callback_data='human')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_text = "👋 Welcome to RaxiWin Support! How can we help you today?"
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    is_new = user.id not in known_users
    known_users.add(user.id)
    if is_new:
        await log_to_channel(context.bot,
            f"🆕 *NEW USER*\n\n"
            f"👤 Name: {user.first_name}\n"
            f"📛 Username: @{user.username if user.username else 'N/A'}\n"
            f"🆔 ID: `{user.id}`\n"
            f"👥 Total: `{len(known_users)}`")
    await main_menu(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "📖 *RaxiWin Help Center*\n\n"
        "Commands:\n"
        "🏠 /start - Main menu\n"
        "🎁 /gift - Today's gift code\n"
        "💬 /contact - Contact admin\n"
        "❓ /help - This message\n\n"
        "💡 *Pro Tip:* Type keywords like *otp*, *withdraw*, *password* for instant help!"
    )
    keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def gift_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (f"🎁 *Today's Free Gift Code*\n\n`{TODAY_GIFT_CODE}`\n\n"
            f"📋 *How to use:*\n1. Copy the code above\n2. Open RaxiWin game\n"
            f"3. Go to Bonus/Redeem section\n4. Paste and claim!\n\n⚠️ Valid 24 hours only.")
    keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (f"💬 *Contact Our Support Team*\n\n👤 *Admin:* {ADMIN_ID}\n\n"
            f"📩 For:\n• Login/Registration\n• Deposit/Withdrawal\n• Account verification\n• Any other queries\n\n"
            f"⏱️ Response: Usually within 30 minutes")
    keyboard = [[InlineKeyboardButton("💬 Message Admin", url=f"https://t.me/{ADMIN_ID.replace('@', '')}")],
                [InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != ADMIN_NUMERIC_ID:
        await update.message.reply_text("❌ Not authorized.")
        return ConversationHandler.END
    await update.message.reply_text(
        f"📢 *Broadcast Mode*\n\n👥 Total users: `{len(known_users)}`\n\nSend me the message to broadcast.\n\n⚠️ /cancel to abort.",
        parse_mode='Markdown')
    return BROADCAST_MSG

async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != ADMIN_NUMERIC_ID:
        return ConversationHandler.END
    message = update.message
    total = len(known_users)
    if total == 0:
        await message.reply_text("❌ No users yet.")
        return ConversationHandler.END
    status_msg = await message.reply_text(f"📡 Broadcasting to {total} users...")
    success, failed = 0, 0
    for uid in list(known_users):
        try:
            await context.bot.copy_message(chat_id=uid, from_chat_id=message.chat_id, message_id=message.message_id)
            success += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            failed += 1
            if "blocked" in str(e).lower() or "chat not found" in str(e).lower():
                known_users.discard(uid)
    await status_msg.edit_text(f"✅ *Broadcast Complete!*\n\n📤 Sent: `{success}`\n❌ Failed: `{failed}`\n👥 Total: `{total}`", parse_mode='Markdown')
    return ConversationHandler.END

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_NUMERIC_ID:
        await update.message.reply_text("❌ Not authorized.")
        return
    text = (f"📊 *Bot Statistics*\n\n👥 Users: `{len(known_users)}`\n"
            f"🎁 Gift Code: `{TODAY_GIFT_CODE}`\n👤 Admin: {ADMIN_ID}\n⚡ Status: Online 24/7")
    await update.message.reply_text(text, parse_mode='Markdown')

async def gift_code_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🎁 *Daily Gift Code*\n\nSend me your *Game ID* to get started.\n\nType it or send a screenshot.", parse_mode='Markdown')
    return ASK_GAME_ID

async def receive_game_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = "Screenshot received" if update.message.photo else update.message.text
    context.user_data['game_id'] = user_data
    keyboard = [
        [InlineKeyboardButton("✅ Yes, I'm registered", callback_data='team_yes')],
        [InlineKeyboardButton("❌ No, I'm new", callback_data='team_no')],
        [InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]
    ]
    await update.message.reply_text(f"Thank you! I received: `{user_data}`\n\nIs this ID registered under our team?", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return ASK_TEAM_STATUS

async def receive_team_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user = query.from_user
    game_id = context.user_data.get('game_id', 'Unknown')
    if query.data == 'team_yes':
        text = f"✅ *Verified Team Member!*\n\nContact admin:\n\n👤 {ADMIN_ID}\n🆔 `{game_id}`\n\nSend your ID to claim your gift code."
        await log_to_channel(context.bot, f"✅ *Gift Claim*\n\n👤 {user.first_name}\n🆔 `{game_id}`")
    else:
        text = f"❌ *Not Registered*\n\nRegister first:\n\n🔗 {REGISTER_LINK}\n\nThen click /start again."
        await log_to_channel(context.bot, f"❌ *Unregistered*\n\n👤 {user.first_name}\n🆔 `{game_id}`")
    keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return ConversationHandler.END

async def deposit_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("💵 Deposit Issue", callback_data='dep_issue')],
        [InlineKeyboardButton("🏧 Withdrawal Issue", callback_data='with_issue')],
        [InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]
    ]
    await query.edit_message_text("💳 *Deposit / Withdraw Help*\n\nDeposit or Withdrawal issue?", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return DEPOSIT_MENU

async def deposit_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user = query.from_user
    if query.data == 'dep_issue':
        text = "💵 *Deposit Issue:*\n\n1. Wallet\n2. UPI/Bank\n3. Min ₹100\n4. Wait 5-10 mins\n\nSolved?"
        state = DEPOSIT_HELP
        await log_to_channel(context.bot, f"💵 *Deposit Help*\n👤 {user.first_name}\n🆔 `{user.id}`")
    else:
        text = "🏧 *Withdrawal Issue:*\n\n1. Wallet > Payout\n2. Bind Bank/UPI\n3. Min ₹200\n4. Wait 30 mins\n\nSolved?"
        state = WITHDRAW_HELP
        await log_to_channel(context.bot, f"🏧 *Withdraw Help*\n👤 {user.first_name}\n🆔 `{user.id}`")
    keyboard = [
        [InlineKeyboardButton("✅ Yes, solved", callback_data='solved')],
        [InlineKeyboardButton("❌ No, contact Human", callback_data='human_contact')],
        [InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]
    ]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return state

async def issue_resolution(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user = query.from_user
    if query.data == 'solved':
        text = "🎉 Great! Click /start for anything else."
    else:
        text = f"💬 *Human Support*\n\nContact admin:\n\n👤 {ADMIN_ID}\n\nSend a screenshot of your issue."
        await log_to_channel(context.bot, f"🆘 *ESCALATED*\n👤 {user.first_name}\n🆔 `{user.id}`")
    keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return ConversationHandler.END

async def human_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("💬 *Talk to Human Agent*\n\nDescribe your issue below. You can also send a screenshot.", parse_mode='Markdown')
    return HUMAN_AGENT

async def receive_human_issue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = "Screenshot received" if update.message.photo else update.message.text
    user = update.effective_user
    text = f"✅ *Issue Received*\n\n`{user_data}`\n\nContact admin:\n\n👤 {ADMIN_ID}"
    keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]]
    await update.message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    await log_to_channel(context.bot, f"💬 *HUMAN REQUEST*\n\n👤 {user.first_name}\n📛 @{user.username if user.username else 'N/A'}\n🆔 `{user.id}`\n\n📝 {user_data}")
    return ConversationHandler.END

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.data == 'referral':
        text = f"🔗 *Your Referral Link:*\n\n{REGISTER_LINK}\n\nShare to earn bonuses!"
    elif query.data == 'faq':
        text = "❓ *FAQ:*\n\n1. Login? - Phone/email\n2. Password? - Letters & numbers only\n3. Withdraw? - Wallet > Payout"
    elif query.data == 'back':
        await main_menu(update, context)
        return
    keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await main_menu(update, context)
    return ConversationHandler.END

if __name__ == '__main__':
    threading.Thread(target=run_web_server, daemon=True).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    broadcast_conv = ConversationHandler(
        entry_points=[CommandHandler('broadcast', broadcast_command)],
        states={BROADCAST_MSG: [MessageHandler(filters.ALL & ~filters.COMMAND, send_broadcast)]},
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    main_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(gift_code_start, pattern='^gift$'),
            CallbackQueryHandler(deposit_start, pattern='^deposit$'),
            CallbackQueryHandler(human_start, pattern='^human$')
        ],
        states={
            ASK_GAME_ID: [MessageHandler(filters.TEXT | filters.PHOTO, receive_game_id)],
            ASK_TEAM_STATUS: [CallbackQueryHandler(receive_team_status, pattern='^(team_yes|team_no)$')],
            DEPOSIT_MENU: [CallbackQueryHandler(deposit_choice, pattern='^(dep_issue|with_issue)$')],
            DEPOSIT_HELP: [CallbackQueryHandler(issue_resolution, pattern='^(solved|human_contact)$')],
            WITHDRAW_HELP: [CallbackQueryHandler(issue_resolution, pattern='^(solved|human_contact)$')],
            HUMAN_AGENT: [MessageHandler(filters.TEXT | filters.PHOTO, receive_human_issue)],
        },
        fallbacks=[CommandHandler('start', start), CallbackQueryHandler(cancel, pattern='^back$')],
    )
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("help", help_command))
    app_bot.add_handler(CommandHandler("gift", gift_command))
    app_bot.add_handler(CommandHandler("contact", contact_command))
    app_bot.add_handler(CommandHandler("stats", stats_command))
    app_bot.add_handler(broadcast_conv)
    app_bot.add_handler(main_conv)
    app_bot.add_handler(CallbackQueryHandler(button_click))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, keyword_auto_reply))
    print("Bot is running perfectly...")
    app_bot.run_polling()
