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
ADMIN_ID = "@proearner0" 
REGISTER_LINK = "https://www.raxiwin.game/#/register?invitationCode=74158275546"
TODAY_GIFT_CODE = "4346F170B0051BD21B95EE9DECBAC10C"
ADMIN_NUMERIC_ID = 6081001025
# ==========================================

known_users = set()

ASK_GAME_ID, ASK_TEAM_STATUS, DEPOSIT_MENU, DEPOSIT_HELP, WITHDRAW_HELP, HUMAN_AGENT, BROADCAST_MSG = range(7)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- Dummy Web Server for Render ---
app = Flask(__name__)
@app.route('/')
def home():
    return "RaxiWin Support Bot is running 24/7!"
def run_web_server():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- KEYWORD AUTO-REPLY DATABASE ---
# Format: keyword -> (emoji, title, reply_text)
KEYWORD_REPLIES = {
    "otp": (
        "📩", "OTP Not Received?",
        "Please try these steps:\n\n"
        "1️⃣ Wait 60 seconds — sometimes it takes time.\n"
        "2️⃣ Check if your phone has network signal.\n"
        "3️⃣ Restart your phone and try again.\n"
        "4️⃣ Don't request OTP more than 3 times in a row.\n\n"
        "Still not received? Contact admin: @pro_earner_0"
    ),
    "password": (
        "🔑", "Password Help",
        "Your password must contain:\n\n"
        "✅ Capital letters (A-Z)\n"
        "✅ Small letters (a-z)\n"
        "✅ Numbers (0-9)\n\n"
        "❌ NO symbols like @ # $ % & !\n\n"
        "Forgot password? Use the 'Forgot Password' option on the login page."
    ),
    "withdraw": (
        "🏧", "Withdrawal Guide",
        "To withdraw funds:\n\n"
        "1️⃣ Login to your account\n"
        "2️⃣ Go to Wallet → Payout\n"
        "3️⃣ Enter your Bank Account or UPI ID\n"
        "4️⃣ Enter amount (Min ₹200)\n"
        "5️⃣ Click Submit\n\n"
        "⚡ Most withdrawals process in 10-30 minutes.\n\n"
        "Still pending? Contact: @pro_earner_0"
    ),
    "deposit": (
        "💵", "Deposit Guide",
        "To deposit funds:\n\n"
        "1️⃣ Login to your account\n"
        "2️⃣ Go to Wallet → Deposit\n"
        "3️⃣ Choose UPI / Bank transfer\n"
        "4️⃣ Enter amount (Min ₹100)\n"
        "5️⃣ Complete the payment\n\n"
        "⏱️ Balance updates within 5-10 minutes.\n\n"
        "Not credited? Contact: @pro_earner_0"
    ),
    "login": (
        "🔓", "Login Help",
        "To login:\n\n"
        "1️⃣ Open RaxiWin app\n"
        "2️⃣ Click Login\n"
        "3️⃣ Enter your phone number or email\n"
        "4️⃣ Enter your password\n"
        "5️⃣ Complete OTP verification\n\n"
        "Can't login? Try resetting your password."
    ),
    "register": (
        "📝", "Registration Help",
        "To register:\n\n"
        f"1️⃣ Click this link: {REGISTER_LINK}\n"
        "2️⃣ Enter your phone number\n"
        "3️⃣ Set password (letters + numbers only)\n"
        "4️⃣ Enter invitation code: 74158275546\n"
        "5️⃣ Complete registration"
    ),
    "bonus": (
        "🎁", "Today's Bonus",
        f"Your gift code:\n\n`{TODAY_GIFT_CODE}`\n\n"
        "Copy it and redeem in the game's Bonus section.\n\n"
        "⚠️ Valid for 24 hours only."
    ),
    "gift": (
        "🎁", "Today's Gift Code",
        f"`{TODAY_GIFT_CODE}`\n\n"
        "Copy this code and paste it in the game to claim your reward!"
    ),
    "help": (
        "🆘", "Need Help?",
        "I can help you with:\n\n"
        "• Login / Register\n"
        "• Deposit / Withdraw\n"
        "• OTP issues\n"
        "• Password reset\n"
        "• Gift codes & bonuses\n\n"
        "Just type any of these words or click the menu button."
    ),
}

# --- KEYWORD AUTO-REPLY HANDLER ---
async def keyword_auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.lower()
    
    # Track user
    known_users.add(update.effective_user.id)
    
    # Check each keyword
    for keyword, (emoji, title, reply) in KEYWORD_REPLIES.items():
        if keyword in text:
            keyboard = [
                [InlineKeyboardButton("💬 Contact Admin", url=f"https://t.me/{ADMIN_ID.replace('@', '')}")],
                [InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]
            ]
            await update.message.reply_text(
                f"{emoji} *{title}*\n\n{reply}",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
    
    # If no keyword matched, show a helpful default
    keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]]
    await update.message.reply_text(
        "🤔 I didn't understand that. Try typing keywords like:\n\n"
        "• *otp*\n• *password*\n• *withdraw*\n• *deposit*\n• *login*\n• *register*\n• *bonus*\n\n"
        "Or use the menu button for full options.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

# --- Main Menu ---
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
    known_users.add(update.effective_user.id)
    await main_menu(update, context)

# --- /help ---
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "📖 *RaxiWin Help Center*\n\n"
        "Commands:\n"
        "🏠 /start - Main menu\n"
        "🎁 /gift - Today's gift code\n"
        "💬 /contact - Contact admin\n"
        "❓ /help - This message\n\n"
        "💡 *Pro Tip:* Just type keywords like *otp*, *withdraw*, *password* — and I'll reply instantly!"
    )
    keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# --- /gift ---
async def gift_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        f"🎁 *Today's Free Gift Code*\n\n"
        f"`{TODAY_GIFT_CODE}`\n\n"
        f"📋 *How to use:*\n"
        f"1. Copy the code above\n"
        f"2. Open RaxiWin game\n"
        f"3. Go to Bonus/Redeem section\n"
        f"4. Paste and claim!\n\n"
        f"⚠️ Valid for 24 hours only."
    )
    keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# --- /contact ---
async def contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        f"💬 *Contact Our Support Team*\n\n"
        f"👤 *Admin:* {ADMIN_ID}\n\n"
        f"📩 For:\n"
        f"• Login/Registration issues\n"
        f"• Deposit/Withdrawal problems\n"
        f"• Account verification\n"
        f"• Any other queries\n\n"
        f"⏱️ Response: Usually within 30 minutes"
    )
    keyboard = [[InlineKeyboardButton("💬 Message Admin", url=f"https://t.me/{ADMIN_ID.replace('@', '')}")],
                [InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# --- /broadcast (ADMIN ONLY) ---
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != ADMIN_NUMERIC_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return ConversationHandler.END
    
    total = len(known_users)
    await update.message.reply_text(
        f"📢 *Broadcast Mode*\n\n"
        f"👥 Total users: `{total}`\n\n"
        f"Send me the message you want to broadcast.\n\n"
        f"⚠️ Send /cancel to abort.",
        parse_mode='Markdown'
    )
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
    
    success = 0
    failed = 0
    
    for uid in list(known_users):
        try:
            await context.bot.copy_message(
                chat_id=uid,
                from_chat_id=message.chat_id,
                message_id=message.message_id
            )
            success += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            failed += 1
            if "blocked" in str(e).lower() or "chat not found" in str(e).lower():
                known_users.discard(uid)
    
    await status_msg.edit_text(
        f"✅ *Broadcast Complete!*\n\n"
        f"📤 Sent: `{success}`\n"
        f"❌ Failed: `{failed}`\n"
        f"👥 Total: `{total}`",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

# --- /stats (ADMIN ONLY) ---
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_NUMERIC_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return
    
    text = (
        f"📊 *Bot Statistics*\n\n"
        f"👥 Total Users: `{len(known_users)}`\n"
        f"🎁 Gift Code: `{TODAY_GIFT_CODE}`\n"
        f"👤 Admin: {ADMIN_ID}\n"
        f"⚡ Status: Online 24/7"
    )
    await update.message.reply_text(text, parse_mode='Markdown')

# --- Gift Code Flow ---
async def gift_code_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🎁 *Daily Gift Code*\n\nSend me your *Game ID* to get started.\n\nYou can type it or send a screenshot.", parse_mode='Markdown')
    return ASK_GAME_ID

async def receive_game_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = "Screenshot received" if update.message.photo else update.message.text
    context.user_data['game_id'] = user_data
    keyboard = [
        [InlineKeyboardButton("✅ Yes, I'm registered", callback_data='team_yes')],
        [InlineKeyboardButton("❌ No, I'm new", callback_data='team_no')],
        [InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]
    ]
    await update.message.reply_text(f"Thank you! I received: `{user_data}`\n\nIs this ID already registered under our team?", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return ASK_TEAM_STATUS

async def receive_team_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    game_id = context.user_data.get('game_id', 'Unknown')
    if query.data == 'team_yes':
        text = f"✅ *Verified Team Member!*\n\nPlease contact our admin:\n\n👤 Admin: {ADMIN_ID}\n🆔 Your ID: `{game_id}`\n\nSend your ID to the admin to claim your gift code."
    else:
        text = f"❌ *Not Registered Yet*\n\nYou need to register first.\n\n🔗 *Register using this link ONLY:*\n{REGISTER_LINK}\n\nAfter registering, click /start and try again."
    keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return ConversationHandler.END

# --- Deposit / Withdraw Flow ---
async def deposit_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("💵 Deposit Issue", callback_data='dep_issue')],
        [InlineKeyboardButton("🏧 Withdrawal Issue", callback_data='with_issue')],
        [InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]
    ]
    await query.edit_message_text("💳 *Deposit / Withdraw Help*\n\nAre you facing a Deposit or Withdrawal issue?", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return DEPOSIT_MENU

async def deposit_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == 'dep_issue':
        text = "💵 *Deposit Issue:*\n\n1. Go to Wallet.\n2. Select UPI/Bank.\n3. Min ₹100.\n4. Wait 5-10 mins.\n\nDid this solve your issue?"
        state = DEPOSIT_HELP
    else:
        text = "🏧 *Withdrawal Issue:*\n\n1. Go to Wallet > Payout.\n2. Bind Bank/UPI correctly.\n3. Min ₹200.\n4. Wait 30 mins.\n\nDid this solve your issue?"
        state = WITHDRAW_HELP
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
    if query.data == 'solved':
        text = "🎉 Great! If you need anything else, click /start."
    else:
        text = f"💬 *Human Support Required*\n\nPlease contact our admin:\n\n👤 Admin: {ADMIN_ID}\n\nSend a screenshot of your issue."
    keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return ConversationHandler.END

# --- Human Agent Flow ---
async def human_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("💬 *Talk to Human Agent*\n\nDescribe your issue below. You can also send a screenshot.", parse_mode='Markdown')
    return HUMAN_AGENT

async def receive_human_issue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = "Screenshot received" if update.message.photo else update.message.text
    text = f"✅ *Issue Received*\n\nYour message: `{user_data}`\n\nPlease contact our admin:\n\n👤 {ADMIN_ID}"
    keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]]
    await update.message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return ConversationHandler.END

# --- Other Button Handlers ---
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.data == 'referral':
        text = f"🔗 *Your Referral Link:*\n\n{REGISTER_LINK}\n\nShare this to earn bonuses!"
    elif query.data == 'faq':
        text = "❓ *FAQ:*\n\n1. *Login?* - Use phone/email.\n2. *Password?* - Letters & numbers only.\n3. *Withdraw?* - Wallet > Payout."
    elif query.data == 'back':
        await main_menu(update, context)
        return
    keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await main_menu(update, context)
    return ConversationHandler.END

# --- Main Execution ---
if __name__ == '__main__':
    threading.Thread(target=run_web_server, daemon=True).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    
    broadcast_conv = ConversationHandler(
        entry_points=[CommandHandler('broadcast', broadcast_command)],
        states={
            BROADCAST_MSG: [MessageHandler(filters.ALL & ~filters.COMMAND, send_broadcast)],
        },
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
        fallbacks=[
            CommandHandler('start', start),
            CallbackQueryHandler(cancel, pattern='^back$')
        ],
    )
    
    # Register all handlers (ORDER MATTERS!)
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("help", help_command))
    app_bot.add_handler(CommandHandler("gift", gift_command))
    app_bot.add_handler(CommandHandler("contact", contact_command))
    app_bot.add_handler(CommandHandler("stats", stats_command))
    app_bot.add_handler(broadcast_conv)
    app_bot.add_handler(main_conv)
    app_bot.add_handler(CallbackQueryHandler(button_click))
    # Keyword auto-reply LAST (catches all other text messages)
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, keyword_auto_reply))
    
    print("Bot is running perfectly... Press Ctrl+C to stop.")
    app_bot.run_polling()
