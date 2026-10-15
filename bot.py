import logging
import threading
import os
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

# Today's gift code (change this daily)
TODAY_GIFT_CODE = "4346F170B0051BD21B95EE9DECBAC10C"
# ==========================================

ASK_GAME_ID, ASK_TEAM_STATUS, DEPOSIT_MENU, DEPOSIT_HELP, WITHDRAW_HELP, HUMAN_AGENT = range(6)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- Dummy Web Server for Render ---
app = Flask(__name__)
@app.route('/')
def home():
    return "RaxiWin Support Bot is running 24/7!"
def run_web_server():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

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

# --- /start Command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await main_menu(update, context)

# --- /help Command (NEW) ---
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "📖 *RaxiWin Help Center*\n\n"
        "Here are the commands you can use:\n\n"
        "🏠 /start - Open the main menu\n"
        "🎁 /gift - Get today's free gift code\n"
        "💬 /contact - Contact our admin\n"
        "❓ /help - Show this help message\n\n"
        "💡 *Tip:* You can also use the buttons in the main menu for Deposit/Withdraw help and FAQs."
    )
    keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# --- /gift Command (NEW) ---
async def gift_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        f"🎁 *Today's Free Gift Code*\n\n"
        f"`{TODAY_GIFT_CODE}`\n\n"
        f"📋 *How to use:*\n"
        f"1. Copy the code above\n"
        f"2. Open RaxiWin game\n"
        f"3. Go to Bonus/Redeem section\n"
        f"4. Paste and claim your reward!\n\n"
        f"⚠️ *Note:* Gift codes are valid for 24 hours only."
    )
    keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# --- /contact Command (NEW) ---
async def contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        f"💬 *Contact Our Support Team*\n\n"
        f"👤 *Admin:* {ADMIN_ID}\n\n"
        f"📩 Send a message directly to our admin for:\n"
        f"• Login/Registration issues\n"
        f"• Deposit/Withdrawal problems\n"
        f"• Account verification\n"
        f"• Any other queries\n\n"
        f"⏱️ *Response Time:* Usually within 30 minutes"
    )
    keyboard = [[InlineKeyboardButton("💬 Message Admin", url=f"https://t.me/{ADMIN_ID.replace('@', '')}")],
                [InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# --- Gift Code Flow ---
async def gift_code_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🎁 *Daily Gift Code*\n\nPlease send me your *Game ID* to get started.\n\nYou can type it or send a screenshot.", parse_mode='Markdown')
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
        text = f"❌ *Not Registered Yet*\n\nYou need to register first.\n\n🔗 *Register using this link ONLY (not Login Register):*\n{REGISTER_LINK}\n\nAfter registering, click /start and try again."
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
    await query.edit_message_text("💳 *Deposit / Withdraw Help*\n\nAre you facing an issue with Deposit or Withdrawal?", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return DEPOSIT_MENU

async def deposit_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == 'dep_issue':
        text = "💵 *Deposit Issue Troubleshooting:*\n\n1. Go to Wallet.\n2. Select UPI/Bank.\n3. Min ₹100.\n4. Wait 5-10 mins.\n\nDid this solve your issue?"
        state = DEPOSIT_HELP
    else:
        text = "🏧 *Withdrawal Issue Troubleshooting:*\n\n1. Go to Wallet > Payout.\n2. Bind Bank/UPI correctly.\n3. Min ₹200.\n4. Wait 30 mins.\n\nDid this solve your issue?"
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
        text = f"💬 *Human Support Required*\n\nPlease contact our admin:\n\n👤 Admin: {ADMIN_ID}\n\nSend a screenshot of your issue to the admin."
    keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return ConversationHandler.END

# --- Human Agent Flow ---
async def human_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("💬 *Talk to Human Agent*\n\nPlease describe your issue below. You can also send a screenshot.", parse_mode='Markdown')
    return HUMAN_AGENT

async def receive_human_issue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = "Screenshot received" if update.message.photo else update.message.text
    text = f"✅ *Issue Received*\n\nThank you! Your message: `{user_data}`\n\nPlease contact our admin directly:\n\n👤 Admin: {ADMIN_ID}\n\nSend them your issue details."
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
    
    conv_handler = ConversationHandler(
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
    
    # Add all handlers
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("help", help_command))     # NEW
    app_bot.add_handler(CommandHandler("gift", gift_command))     # NEW
    app_bot.add_handler(CommandHandler("contact", contact_command)) # NEW
    app_bot.add_handler(conv_handler)
    app_bot.add_handler(CallbackQueryHandler(button_click))
    
    print("Bot is running perfectly... Press Ctrl+C to stop.")
    app_bot.run_polling()
