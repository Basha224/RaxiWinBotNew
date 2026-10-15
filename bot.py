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
TOKEN = "PASTE_YOUR_TOKEN_HERE"
ADMIN_ID = "@pro_earner_0"
REGISTER_LINK = "https://www.raxiwin.game/#/register?invitationCode=74158275546"
TODAY_GIFT_CODE = "4346F170B0051BD21B95EE9DECBAC10C"
ADMIN_NUMERIC_ID = 6081001025
LOG_CHANNEL_ID = ADMIN_NUMERIC_ID
# ==========================================

known_users = set()
user_langs = {}

CHOOSE_LANG, ASK_GAME_ID, ASK_TEAM_STATUS, DEPOSIT_MENU, DEPOSIT_HELP, WITHDRAW_HELP, HUMAN_AGENT, BROADCAST_MSG = range(8)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

app = Flask(__name__)
@app.route('/')
def home():
    return "RaxiWin Support Bot is running 24/7!"
def run_web_server():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# ==========================================
# TRANSLATIONS
# ==========================================
TEXTS = {
    "choose_lang": {
        "en": "🌐 *Please choose your language:*\n\n🇬🇧 English\n🇮🇳 हिंदी\n🇮🇳 తెలుగు",
        "hi": "🌐 *कृपया अपनी भाषा चुनें:*\n\n🇬🇧 English\n🇮🇳 हिंदी\n🇮🇳 తెలుగు",
        "te": "🌐 *దయచేసి మీ భాషను ఎంచుకోండి:*\n\n🇬🇧 English\n🇮🇳 हिंदी\n🇮🇳 తెలుగు"
    },
    "lang_set": {
        "en": "✅ Language set to English!",
        "hi": "✅ भाषा हिंदी में सेट हो गई!",
        "te": "✅ భాష తెలుగులో సెట్ చేయబడింది!"
    },
    "welcome": {
        "en": "👋 Welcome to RaxiWin Support! How can we help you today?",
        "hi": "👋 RaxiWin सपोर्ट में आपका स्वागत है! हम आपकी कैसे मदद कर सकते हैं?",
        "te": "👋 RaxiWin సపోర్ట్‌కు స్వాగతం! మేము మీకు ఎలా సహాయం చేయగలము?"
    },
    "btn_gift": {"en": "🎁 Daily Gift Code", "hi": "🎁 डेली गिफ्ट कोड", "te": "🎁 డైలీ గిఫ్ట్ కోడ్"},
    "btn_referral": {"en": "🔗 My Referral Link", "hi": "🔗 मेरा रेफरल लिंक", "te": "🔗 నా రెఫరల్ లింక్"},
    "btn_deposit": {"en": "💳 Deposit / Withdraw Help", "hi": "💳 डिपॉजिट / विड्रॉ हेल्प", "te": "💳 డిపాజిట్ / విత్‌డ్రా సహాయం"},
    "btn_faq": {"en": "❓ FAQ", "hi": "❓ सामान्य प्रश्न", "te": "❓ తరచుగా అడిగే ప్రశ్నలు"},
    "btn_human": {"en": "💬 Talk to Human Agent", "hi": "💬 ह्यूमन एजेंट से बात करें", "te": "💬 మానవ ఏజెంట్‌తో మాట్లాడండి"},
    "btn_changelang": {"en": "🌐 Change Language", "hi": "🌐 भाषा बदलें", "te": "🌐 భాష మార్చండి"},
    "btn_back": {"en": "⬅️ Back to Menu", "hi": "⬅️ मेनू पर वापस", "te": "⬅️ మెనూకు తిరిగి"},
    "btn_contact": {"en": "💬 Contact Admin", "hi": "💬 एडमिन से संपर्क करें", "te": "💬 అడ్మిన్‌ను సంప్రదించండి"},
    "btn_yes_reg": {"en": "✅ Yes, I'm registered", "hi": "✅ हाँ, मैं रजिस्टर्ड हूँ", "te": "✅ అవును, నేను రిజిస్టర్ అయ్యాను"},
    "btn_no_new": {"en": "❌ No, I'm new", "hi": "❌ नहीं, मैं नया हूँ", "te": "❌ కాదు, నేను కొత్తవాడిని"},
    "btn_dep_issue": {"en": "💵 Deposit Issue", "hi": "💵 डिपॉजिट समस्या", "te": "💵 డిపాజిట్ సమస్య"},
    "btn_with_issue": {"en": "🏧 Withdrawal Issue", "hi": "🏧 विड्रॉ समस्या", "te": "🏧 విత్‌డ్రా సమస్య"},
    "btn_solved": {"en": "✅ Yes, solved", "hi": "✅ हाँ, हल हो गया", "te": "✅ అవును, పరిష్కరించబడింది"},
    "btn_human_contact": {"en": "❌ No, contact Human", "hi": "❌ नहीं, ह्यूमन से संपर्क करें", "te": "❌ కాదు, మానవుడిని సంప్రదించండి"},
    "gift_prompt": {
        "en": "🎁 *Daily Gift Code*\n\nSend me your *Game ID*.\n\nType it or send a screenshot.",
        "hi": "🎁 *डेली गिफ्ट कोड*\n\nमुझे अपनी *गेम आईडी* भेजें।\n\nटाइप करें या स्क्रीनशॉट भेजें।",
        "te": "🎁 *డైలీ గిఫ్ట్ కోడ్*\n\nమీ *గేమ్ ID* పంపండి.\n\nటైప్ చేయండి లేదా స్క్రీన్‌షాట్ పంపండి."
    },
    "gift_received": {
        "en": "Thank you! Received: `{data}`\n\nIs this ID registered under our team?",
        "hi": "धन्यवाद! मिला: `{data}`\n\nक्या यह आईडी हमारी टीम में है?",
        "te": "ధన్యవాదాలు! అందింది: `{data}`\n\nఈ ID మా టీమ్‌లో ఉందా?"
    },
    "gift_verified": {
        "en": "✅ *Verified Team Member!*\n\nContact admin:\n\n👤 {admin}\n🆔 `{id}`\n\nSend your ID to claim gift code.",
        "hi": "✅ *सत्यापित टीम सदस्य!*\n\nएडमिन से संपर्क करें:\n\n👤 {admin}\n🆔 `{id}`\n\nगिफ्ट कोड के लिए ID भेजें।",
        "te": "✅ *ధృవీకరించబడిన సభ్యుడు!*\n\nఅడ్మిన్‌ను సంప్రదించండి:\n\n👤 {admin}\n🆔 `{id}`\n\nగిఫ్ట్ కోడ్ కోసం ID పంపండి."
    },
    "gift_not_reg": {
        "en": "❌ *Not Registered*\n\nRegister first:\n\n🔗 {link}\n\nThen click /start.",
        "hi": "❌ *रजिस्टर्ड नहीं*\n\nपहले रजिस्टर करें:\n\n🔗 {link}\n\nफिर /start क्लिक करें।",
        "te": "❌ *రిజిస్టర్ కాలేదు*\n\nమొదట రిజిస్టర్ చేయండి:\n\n🔗 {link}\n\nతర్వాత /start క్లిక్ చేయండి."
    },
    "referral": {
        "en": "🔗 *Your Referral Link:*\n\n{link}\n\nShare to earn bonuses!",
        "hi": "🔗 *आपका रेफरल लिंक:*\n\n{link}\n\nबोनस कमाने के लिए शेयर करें!",
        "te": "🔗 *మీ రెఫరల్ లింక్:*\n\n{link}\n\nబోనస్ కోసం షేర్ చేయండి!"
    },
    "faq": {
        "en": "❓ *FAQ:*\n\n1. *Login?* - Phone/email\n2. *Password?* - Letters & numbers only\n3. *Withdraw?* - Wallet > Payout",
        "hi": "❓ *सामान्य प्रश्न:*\n\n1. *लॉगिन?* - फ़ोन/ईमेल\n2. *पासवर्ड?* - अक्षर और नंबर\n3. *विड्रॉ?* - वॉलेट > पेआउट",
        "te": "❓ *FAQ:*\n\n1. *లాగిన్?* - ఫోన్/ఇమెయిల్\n2. *పాస్‌వర్డ్?* - అక్షరాలు & నంబర్లు\n3. *విత్‌డ్రా?* - వాలెట్ > పేఅవుట్"
    },
    "dep_menu": {
        "en": "💳 *Deposit / Withdraw Help*\n\nChoose issue:",
        "hi": "💳 *डिपॉजिट / विड्रॉ हेल्प*\n\nसमस्या चुनें:",
        "te": "💳 *డిపాజిట్ / విత్‌డ్రా సహాయం*\n\nసమస్య ఎంచుకోండి:"
    },
    "dep_trouble": {
        "en": "💵 *Deposit Issue:*\n\n1. Wallet\n2. UPI/Bank\n3. Min ₹100\n4. Wait 5-10 mins\n\nSolved?",
        "hi": "💵 *डिपॉजिट समस्या:*\n\n1. वॉलेट\n2. UPI/बैंक\n3. न्यूनतम ₹100\n4. 5-10 मिनट\n\nहल हुई?",
        "te": "💵 *డిపాజిట్ సమస్య:*\n\n1. వాలెట్\n2. UPI/బ్యాంక్\n3. కనీసం ₹100\n4. 5-10 నిమిషాలు\n\nపరిష్కారమైందా?"
    },
    "with_trouble": {
        "en": "🏧 *Withdrawal Issue:*\n\n1. Wallet > Payout\n2. Bind Bank/UPI\n3. Min ₹200\n4. Wait 30 mins\n\nSolved?",
        "hi": "🏧 *विड्रॉ समस्या:*\n\n1. वॉलेट > पेआउट\n2. बैंक/UPI बांधें\n3. न्यूनतम ₹200\n4. 30 मिनट\n\nहल हुई?",
        "te": "🏧 *విత్‌డ్రా సమస్య:*\n\n1. వాలెట్ > పేఅవుట్\n2. బ్యాంక్/UPI బైండ్\n3. కనీసం ₹200\n4. 30 నిమిషాలు\n\nపరిష్కారమైందా?"
    },
    "solved": {
        "en": "🎉 Great! /start for anything else.",
        "hi": "🎉 बहुत बढ़िया! /start करें।",
        "te": "🎉 అద్భుతం! /start చేయండి."
    },
    "human_required": {
        "en": "💬 *Human Support*\n\nContact admin:\n\n👤 {admin}\n\nSend a screenshot of your issue.",
        "hi": "💬 *ह्यूमन सपोर्ट*\n\nएडमिन से संपर्क करें:\n\n👤 {admin}\n\nसमस्या का स्क्रीनशॉट भेजें।",
        "te": "💬 *మానవ సహాయం*\n\nఅడ్మిన్‌ను సంప్రదించండి:\n\n👤 {admin}\n\nసమస్య స్క్రీన్‌షాట్ పంపండి."
    },
    "human_prompt": {
        "en": "💬 *Talk to Human Agent*\n\nDescribe your issue below. You can also send a screenshot.",
        "hi": "💬 *ह्यूमन एजेंट से बात करें*\n\nसमस्या बताएं। स्क्रीनशॉट भी भेज सकते हैं।",
        "te": "💬 *మానవ ఏజెంట్‌తో మాట్లాడండి*\n\nమీ సమస్యను వివరించండి. స్క్రీన్‌షాట్ కూడా పంపవచ్చు."
    },
    "human_received": {
        "en": "✅ *Issue Received*\n\n`{data}`\n\nContact admin:\n\n👤 {admin}",
        "hi": "✅ *समस्या मिली*\n\n`{data}`\n\nएडमिन से संपर्क करें:\n\n👤 {admin}",
        "te": "✅ *సమస్య అందింది*\n\n`{data}`\n\nఅడ్మిన్‌ను సంప్రదించండి:\n\n👤 {admin}"
    },
    "kw_unknown": {
        "en": "🤔 I didn't understand. Try keywords:\n\n• otp\n• password\n• withdraw\n• deposit\n• login\n• register\n• bonus\n\nOr use the menu.",
        "hi": "🤔 समझ नहीं आया। कीवर्ड आज़माएं:\n\n• otp\n• password\n• withdraw\n• deposit\n• login\n• register\n• bonus\n\nया मेनू उपयोग करें।",
        "te": "🤔 అర్థం కాలేదు. కీవర్డ్‌లు ప్రయత్నించండి:\n\n• otp\n• password\n• withdraw\n• deposit\n• login\n• register\n• bonus\n\nలేదా మెనూ వాడండి."
    },
    "kw_otp_title": {"en": "📩 OTP Not Received?", "hi": "📩 OTP नहीं आया?", "te": "📩 OTP రాలేదా?"},
    "kw_otp_body": {
        "en": "Try:\n\n1️⃣ Wait 60 seconds\n2️⃣ Check network\n3️⃣ Restart phone\n4️⃣ Don't request 3+ times\n\nStill not received? {admin}",
        "hi": "यह करें:\n\n1️⃣ 60 सेकंड प्रतीक्षा\n2️⃣ नेटवर्क जांचें\n3️⃣ फ़ोन रीस्टार्ट\n4️⃣ 3+ बार न मांगें\n\nफिर भी नहीं आया? {admin}",
        "te": "ఇది చేయండి:\n\n1️⃣ 60 సెకన్లు వేచి ఉండండి\n2️⃣ నెట్‌వర్క్ చూడండి\n3️⃣ ఫోన్ రీస్టార్ట్\n4️⃣ 3+ సార్లు అడగవద్దు\n\nఇంకా రాలేదా? {admin}"
    },
    "kw_pwd_title": {"en": "🔑 Password Help", "hi": "🔑 पासवर्ड मदद", "te": "🔑 పాస్‌వర్డ్ సహాయం"},
    "kw_pwd_body": {
        "en": "Password must contain:\n\n✅ Capital (A-Z)\n✅ Small (a-z)\n✅ Numbers (0-9)\n\n❌ NO symbols @ # $ % & !",
        "hi": "पासवर्ड में होना चाहिए:\n\n✅ बड़े (A-Z)\n✅ छोटे (a-z)\n✅ नंबर (0-9)\n\n❌ चिन्ह @ # $ % & ! नहीं",
        "te": "పాస్‌వర్డ్‌లో ఉండాలి:\n\n✅ పెద్ద (A-Z)\n✅ చిన్న (a-z)\n✅ నంబర్లు (0-9)\n\n❌ చిహ్నాలు @ # $ % & ! వద్దు"
    },
    "kw_with_title": {"en": "🏧 Withdrawal Guide", "hi": "🏧 विड्रॉ गाइड", "te": "🏧 విత్‌డ్రా గైడ్"},
    "kw_with_body": {
        "en": "1️⃣ Login\n2️⃣ Wallet → Payout\n3️⃣ Bank/UPI ID\n4️⃣ Amount (Min ₹200)\n5️⃣ Submit\n\n⚡ 10-30 mins.\n\nPending? {admin}",
        "hi": "1️⃣ लॉगिन\n2️⃣ वॉलेट → पेआउट\n3️⃣ बैंक/UPI\n4️⃣ राशि (न्यूनतम ₹200)\n5️⃣ सबमिट\n\n⚡ 10-30 मिनट।\n\nपेंडिंग? {admin}",
        "te": "1️⃣ లాగిన్\n2️⃣ వాలెట్ → పేఅవుట్\n3️⃣ బ్యాంక్/UPI\n4️⃣ మొత్తం (కనీసం ₹200)\n5️⃣ సబ్మిట్\n\n⚡ 10-30 నిమిషాలు.\n\nపెండింగ్? {admin}"
    },
    "kw_dep_title": {"en": "💵 Deposit Guide", "hi": "💵 डिपॉजिट गाइड", "te": "💵 డిపాజిట్ గైడ్"},
    "kw_dep_body": {
        "en": "1️⃣ Login\n2️⃣ Wallet → Deposit\n3️⃣ UPI/Bank\n4️⃣ Amount (Min ₹100)\n5️⃣ Pay\n\n⏱️ 5-10 mins.\n\nNot credited? {admin}",
        "hi": "1️⃣ लॉगिन\n2️⃣ वॉलेट → डिपॉजिट\n3️⃣ UPI/बैंक\n4️⃣ राशि (न्यूनतम ₹100)\n5️⃣ भुगतान\n\n⏱️ 5-10 मिनट।\n\nक्रेडिट नहीं? {admin}",
        "te": "1️⃣ లాగిన్\n2️⃣ వాలెట్ → డిపాజిట్\n3️⃣ UPI/బ్యాంక్\n4️⃣ మొత్తం (కనీసం ₹100)\n5️⃣ పే\n\n⏱️ 5-10 నిమిషాలు.\n\nక్రెడిట్ కాలేదా? {admin}"
    },
    "kw_login_title": {"en": "🔓 Login Help", "hi": "🔓 लॉगिन मदद", "te": "🔓 లాగిన్ సహాయం"},
    "kw_login_body": {
        "en": "1️⃣ Open app\n2️⃣ Login\n3️⃣ Phone/email\n4️⃣ Password\n5️⃣ OTP\n\nCan't login? Reset password.",
        "hi": "1️⃣ ऐप खोलें\n2️⃣ लॉगिन\n3️⃣ फ़ोन/ईमेल\n4️⃣ पासवर्ड\n5️⃣ OTP\n\nलॉगिन नहीं? पासवर्ड रीसेट करें।",
        "te": "1️⃣ యాప్ తెరవండి\n2️⃣ లాగిన్\n3️⃣ ఫోన్/ఇమెయిల్\n4️⃣ పాస్‌వర్డ్\n5️⃣ OTP\n\nలాగిన్ కాదా? పాస్‌వర్డ్ రీసెట్."
    },
    "kw_reg_title": {"en": "📝 Registration Help", "hi": "📝 रजिस्ट्रेशन मदद", "te": "📝 రిజిస్ట్రేషన్ సహాయం"},
    "kw_reg_body": {
        "en": "1️⃣ {link}\n2️⃣ Phone number\n3️⃣ Password\n4️⃣ Code: 74158275546\n5️⃣ Done",
        "hi": "1️⃣ {link}\n2️⃣ फ़ोन नंबर\n3️⃣ पासवर्ड\n4️⃣ कोड: 74158275546\n5️⃣ पूरा",
        "te": "1️⃣ {link}\n2️⃣ ఫోన్ నంబర్\n3️⃣ పాస్‌వర్డ్\n4️⃣ కోడ్: 74158275546\n5️⃣ పూర్తి"
    },
    "kw_bonus_title": {"en": "🎁 Today's Bonus", "hi": "🎁 आज का बोनस", "te": "🎁 ఈరోజు బోనస్"},
    "kw_bonus_body": {
        "en": "Code:\n\n`{code}`\n\nRedeem in game's Bonus section.\n\n⚠️ 24 hours only.",
        "hi": "कोड:\n\n`{code}`\n\nगेम के Bonus सेक्शन में रिडीम करें।\n\n⚠️ 24 घंटे मान्य।",
        "te": "కోడ్:\n\n`{code}`\n\nగేమ్ Bonus సెక్షన్‌లో రీడీమ్.\n\n⚠️ 24 గంటలు మాత్రమే."
    },
    "kw_help_title": {"en": "🆘 Need Help?", "hi": "🆘 मदद चाहिए?", "te": "🆘 సహాయం కావాలా?"},
    "kw_help_body": {
        "en": "I help with:\n\n• Login/Register\n• Deposit/Withdraw\n• OTP\n• Password\n• Gift codes\n\nType a keyword or use menu.",
        "hi": "मैं मदद करता हूँ:\n\n• लॉगिन/रजिस्टर\n• डिपॉजिट/विड्रॉ\n• OTP\n• पासवर्ड\n• गिफ्ट कोड\n\nकीवर्ड टाइप करें या मेनू।",
        "te": "నేను సహాయం చేస్తాను:\n\n• లాగిన్/రిజిస్టర్\n• డిపాజిట్/విత్‌డ్రా\n• OTP\n• పాస్‌వర్డ్\n• గిఫ్ట్ కోడ్‌లు\n\nకీవర్డ్ టైప్ లేదా మెనూ."
    },
}


def t(key, lang, **kwargs):
    text = TEXTS.get(key, {}).get(lang, TEXTS.get(key, {}).get("en", ""))
    if kwargs:
        try:
            return text.format(**kwargs)
        except:
            return text
    return text


def get_lang(user_id):
    return user_langs.get(user_id, "en")


async def log_to_channel(bot, message: str):
    try:
        await bot.send_message(chat_id=LOG_CHANNEL_ID, text=message, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Log error: {e}")


# --- LANGUAGE SELECTION ---
async def language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data='lang_en')],
        [InlineKeyboardButton("🇮🇳 हिंदी", callback_data='lang_hi')],
        [InlineKeyboardButton("🇮🇳 తెలుగు", callback_data='lang_te')]
    ]
    text = "🌐 *Please choose your language:*\n🌐 *कृपया अपनी भाषा चुनें:*\n🌐 *దయచేసి మీ భాషను ఎంచుకోండి:*"
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return CHOOSE_LANG


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = query.data.split('_')[1]
    user_langs[query.from_user.id] = lang
    await query.edit_message_text(t("lang_set", lang), parse_mode='Markdown')
    await main_menu(update, context)
    return ASK_GAME_ID


# --- MAIN MENU ---
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user:
        user_id = update.effective_user.id
    else:
        user_id = update.callback_query.from_user.id
    lang = get_lang(user_id)
    
    keyboard = [
        [InlineKeyboardButton(t("btn_gift", lang), callback_data='gift')],
        [InlineKeyboardButton(t("btn_referral", lang), callback_data='referral')],
        [InlineKeyboardButton(t("btn_deposit", lang), callback_data='deposit')],
        [InlineKeyboardButton(t("btn_faq", lang), callback_data='faq')],
        [InlineKeyboardButton(t("btn_human", lang), callback_data='human')],
        [InlineKeyboardButton(t("btn_changelang", lang), callback_data='changelang')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_text = t("welcome", lang)
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    is_new = user.id not in known_users
    known_users.add(user.id)
    if is_new:
        await log_to_channel(context.bot,
            f"🆕 *NEW USER*\n\n👤 {user.first_name}\n📛 @{user.username if user.username else 'N/A'}\n🆔 `{user.id}`\n👥 Total: `{len(known_users)}`")
    
    if user.id in user_langs:
        await main_menu(update, context)
        return ASK_GAME_ID
    return await language_selection(update, context)


async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await language_selection(update, context)


# --- KEYWORD AUTO-REPLY ---
async def keyword_auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    text = update.message.text.lower()
    user = update.effective_user
    lang = get_lang(user.id)
    known_users.add(user.id)
    admin = ADMIN_ID
    
    if "otp" in text:
        reply = f"📩 *{t('kw_otp_title', lang)}*\n\n{t('kw_otp_body', lang, admin=admin)}"
    elif "password" in text:
        reply = f"🔑 *{t('kw_pwd_title', lang)}*\n\n{t('kw_pwd_body', lang)}"
    elif "withdraw" in text:
        reply = f"🏧 *{t('kw_with_title', lang)}*\n\n{t('kw_with_body', lang, admin=admin)}"
    elif "deposit" in text:
        reply = f"💵 *{t('kw_dep_title', lang)}*\n\n{t('kw_dep_body', lang, admin=admin)}"
    elif "login" in text:
        reply = f"🔓 *{t('kw_login_title', lang)}*\n\n{t('kw_login_body', lang)}"
    elif "register" in text:
        reply = f"📝 *{t('kw_reg_title', lang)}*\n\n{t('kw_reg_body', lang, link=REGISTER_LINK)}"
    elif "bonus" in text or "gift" in text:
        reply = f"🎁 *{t('kw_bonus_title', lang)}*\n\n{t('kw_bonus_body', lang, code=TODAY_GIFT_CODE)}"
    elif "help" in text:
        reply = f"🆘 *{t('kw_help_title', lang)}*\n\n{t('kw_help_body', lang)}"
    else:
        keyboard = [[InlineKeyboardButton(t("btn_back", lang), callback_data='back')]]
        await update.message.reply_text(t("kw_unknown", lang), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return
    
    keyboard = [
        [InlineKeyboardButton(t("btn_contact", lang), url=f"https://t.me/{admin.replace('@', '')}")],
        [InlineKeyboardButton(t("btn_back", lang), callback_data='back')]
    ]
    await update.message.reply_text(reply, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != ADMIN_NUMERIC_ID:
        return ConversationHandler.END
    await update.message.reply_text(f"📢 Broadcast Mode\n👥 Total: `{len(known_users)}`\n\nSend the message.", parse_mode='Markdown')
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
        except Exception:
            failed += 1
    await status_msg.edit_text(f"✅ Broadcast done!\n📤 Sent: {success}\n❌ Failed: {failed}")
    return ConversationHandler.END


async def gift_code_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = get_lang(query.from_user.id)
    await query.edit_message_text(t("gift_prompt", lang), parse_mode='Markdown')
    return ASK_GAME_ID


async def receive_game_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = "Screenshot" if update.message.photo else update.message.text
    context.user_data['game_id'] = user_data
    lang = get_lang(update.effective_user.id)
    keyboard = [
        [InlineKeyboardButton(t("btn_yes_reg", lang), callback_data='team_yes')],
        [InlineKeyboardButton(t("btn_no_new", lang), callback_data='team_no')],
        [InlineKeyboardButton(t("btn_back", lang), callback_data='back')]
    ]
    await update.message.reply_text(t("gift_received", lang, data=user_data), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return ASK_TEAM_STATUS


async def receive_team_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user = query.from_user
    lang = get_lang(user.id)
    game_id = context.user_data.get('game_id', '?')
    
    if query.data == 'team_yes':
        text = t("gift_verified", lang, admin=ADMIN_ID, id=game_id)
        await log_to_channel(context.bot, f"✅ Gift Claim\n👤 {user.first_name}\n🆔 `{game_id}`")
    else:
        text = t("gift_not_reg", lang, link=REGISTER_LINK)
        await log_to_channel(context.bot, f"❌ Unregistered\n👤 {user.first_name}")
    
    keyboard = [[InlineKeyboardButton(t("btn_back", lang), callback_data='back')]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return ConversationHandler.END


async def deposit_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = get_lang(query.from_user.id)
    keyboard = [
        [InlineKeyboardButton(t("btn_dep_issue", lang), callback_data='dep_issue')],
        [InlineKeyboardButton(t("btn_with_issue", lang), callback_data='with_issue')],
        [InlineKeyboardButton(t("btn_back", lang), callback_data='back')]
    ]
    await query.edit_message_text(t("dep_menu", lang), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return DEPOSIT_MENU


async def deposit_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = get_lang(query.from_user.id)
    if query.data == 'dep_issue':
        text = t("dep_trouble", lang)
        state = DEPOSIT_HELP
    else:
        text = t("with_trouble", lang)
        state = WITHDRAW_HELP
    keyboard = [
        [InlineKeyboardButton(t("btn_solved", lang), callback_data='solved')],
        [InlineKeyboardButton(t("btn_human_contact", lang), callback_data='human_contact')],
        [InlineKeyboardButton(t("btn_back", lang), callback_data='back')]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return state


async def issue_resolution(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = get_lang(query.from_user.id)
    if query.data == 'solved':
        text = t("solved", lang)
    else:
        text = t("human_required", lang, admin=ADMIN_ID)
        await log_to_channel(context.bot, f"🆘 ESCALATED\n👤 {query.from_user.first_name}")
    keyboard = [[InlineKeyboardButton(t("btn_back", lang), callback_data='back')]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return ConversationHandler.END


async def human_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = get_lang(query.from_user.id)
    await query.edit_message_text(t("human_prompt", lang), parse_mode='Markdown')
    return HUMAN_AGENT


async def receive_human_issue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = "Screenshot" if update.message.photo else update.message.text
    user = update.effective_user
    lang = get_lang(user.id)
    text = t("human_received", lang, data=user_data, admin=ADMIN_ID)
    keyboard = [[InlineKeyboardButton(t("btn_back", lang), callback_data='back')]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    await log_to_channel(context.bot, f"💬 HUMAN REQUEST\n👤 {user.first_name}\n📝 {user_data}")
    return ConversationHandler.END


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    lang = get_lang(query.from_user.id)
    
    if query.data == 'referral':
        text = t("referral", lang, link=REGISTER_LINK)
    elif query.data == 'faq':
        text = t("faq", lang)
    elif query.data == 'changelang':
        return await language_selection(update, context)
    elif query.data == 'back':
        await main_menu(update, context)
        return
    else:
        return
    
    keyboard = [[InlineKeyboardButton(t("btn_back", lang), callback_data='back')]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await main_menu(update, context)
    return ASK_GAME_ID


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
            CommandHandler('start', start),
            CommandHandler('language', language_command),
            CallbackQueryHandler(gift_code_start, pattern='^gift$'),
            CallbackQueryHandler(deposit_start, pattern='^deposit$'),
            CallbackQueryHandler(human_start, pattern='^human$'),
            CallbackQueryHandler(set_language, pattern='^lang_(en|hi|te)$'),
            CallbackQueryHandler(button_click, pattern='^changelang$'),
        ],
        states={
            CHOOSE_LANG: [
                CallbackQueryHandler(set_language, pattern='^lang_(en|hi|te)$'),
            ],
            ASK_GAME_ID: [
                MessageHandler(filters.TEXT | filters.PHOTO, receive_game_id),
                CallbackQueryHandler(button_click),
            ],
            ASK_TEAM_STATUS: [CallbackQueryHandler(receive_team_status, pattern='^(team_yes|team_no)$')],
            DEPOSIT_MENU: [CallbackQueryHandler(deposit_choice, pattern='^(dep_issue|with_issue)$')],
            DEPOSIT_HELP: [CallbackQueryHandler(issue_resolution, pattern='^(solved|human_contact)$')],
            WITHDRAW_HELP: [CallbackQueryHandler(issue_resolution, pattern='^(solved|human_contact)$')],
            HUMAN_AGENT: [MessageHandler(filters.TEXT | filters.PHOTO, receive_human_issue)],
        },
        fallbacks=[
            CommandHandler('start', start),
            CommandHandler('language', language_command),
            CallbackQueryHandler(cancel, pattern='^back$'),
            CallbackQueryHandler(button_click),
        ],
    )
    
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("language", language_command))
    app_bot.add_handler(broadcast_conv)
    app_bot.add_handler(main_conv)
    app_bot.add_handler(CallbackQueryHandler(button_click))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, keyword_auto_reply))
    
    print("Bot running with 3 languages + language button!")
    app_bot.run_polling()
