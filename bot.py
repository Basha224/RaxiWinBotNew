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
TOKEN =8740602277:AAEnKeFd4N_MNjVA3WsqzMKztCpFkmHRorY""
ADMIN_ID = "@pro_earner_0"
REGISTER_LINK = "https://www.raxiwin.game/#/register?invitationCode=74158275546"
TODAY_GIFT_CODE = "4346F170B0051BD21B95EE9DECBAC10C"
ADMIN_NUMERIC_ID = 6081001025
LOG_CHANNEL_ID = ADMIN_NUMERIC_ID
# ==========================================

known_users = set()
user_langs = {}   # user_id -> 'en' / 'hi' / 'te'

# Conversation States
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
# TRANSLATIONS (English / Hindi / Telugu)
# ==========================================
TEXTS = {
    "choose_lang": {
        "en": "🌐 *Please choose your language:*",
        "hi": "🌐 *कृपया अपनी भाषा चुनें:*",
        "te": "🌐 *దయచేసి మీ భాషను ఎంచుకోండి:*"
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
    "btn_gift": {
        "en": "🎁 Daily Gift Code",
        "hi": "🎁 डेली गिफ्ट कोड",
        "te": "🎁 డైలీ గిఫ్ట్ కోడ్"
    },
    "btn_referral": {
        "en": "🔗 My Referral Link",
        "hi": "🔗 मेरा रेफरल लिंक",
        "te": "🔗 నా రెఫరల్ లింక్"
    },
    "btn_deposit": {
        "en": "💳 Deposit / Withdraw Help",
        "hi": "💳 डिपॉजिट / विड्रॉ हेल्प",
        "te": "💳 డిపాజిట్ / విత్‌డ్రా సహాయం"
    },
    "btn_faq": {
        "en": "❓ FAQ",
        "hi": "❓ सामान्य प्रश्न",
        "te": "❓ తరచుగా అడిగే ప్రశ్నలు"
    },
    "btn_human": {
        "en": "💬 Talk to Human Agent",
        "hi": "💬 ह्यूमन एजेंट से बात करें",
        "te": "💬 మానవ ఏజెంట్‌తో మాట్లాడండి"
    },
    "btn_back": {
        "en": "⬅️ Back to Menu",
        "hi": "⬅️ मेनू पर वापस",
        "te": "⬅️ మెనూకు తిరిగి"
    },
    "btn_contact": {
        "en": "💬 Contact Admin",
        "hi": "💬 एडमिन से संपर्क करें",
        "te": "💬 అడ్మిన్‌ను సంప్రదించండి"
    },
    "btn_yes_reg": {
        "en": "✅ Yes, I'm registered",
        "hi": "✅ हाँ, मैं रजिस्टर्ड हूँ",
        "te": "✅ అవును, నేను రిజిస్టర్ అయ్యాను"
    },
    "btn_no_new": {
        "en": "❌ No, I'm new",
        "hi": "❌ नहीं, मैं नया हूँ",
        "te": "❌ కాదు, నేను కొత్తవాడిని"
    },
    "btn_dep_issue": {
        "en": "💵 Deposit Issue",
        "hi": "💵 डिपॉजिट समस्या",
        "te": "💵 డిపాజిట్ సమస్య"
    },
    "btn_with_issue": {
        "en": "🏧 Withdrawal Issue",
        "hi": "🏧 विड्रॉ समस्या",
        "te": "🏧 విత్‌డ్రా సమస్య"
    },
    "btn_solved": {
        "en": "✅ Yes, solved",
        "hi": "✅ हाँ, हल हो गया",
        "te": "✅ అవును, పరిష్కరించబడింది"
    },
    "btn_human_contact": {
        "en": "❌ No, contact Human",
        "hi": "❌ नहीं, ह्यूमन से संपर्क करें",
        "te": "❌ కాదు, మానవుడిని సంప్రదించండి"
    },
    # Gift flow
    "gift_prompt": {
        "en": "🎁 *Daily Gift Code*\n\nSend me your *Game ID* to get started.\n\nType it or send a screenshot.",
        "hi": "🎁 *डेली गिफ्ट कोड*\n\nशुरू करने के लिए मुझे अपनी *गेम आईडी* भेजें।\n\nटाइप करें या स्क्रीनशॉट भेजें।",
        "te": "🎁 *డైలీ గిఫ్ట్ కోడ్*\n\nప్రారంభించడానికి మీ *గేమ్ ID* పంపండి.\n\nటైప్ చేయండి లేదా స్క్రీన్‌షాట్ పంపండి."
    },
    "gift_received": {
        "en": "Thank you! I received: `{data}`\n\nIs this ID registered under our team?",
        "hi": "धन्यवाद! मुझे मिला: `{data}`\n\nक्या यह आईडी हमारी टीम के अंतर्गत रजिस्टर्ड है?",
        "te": "ధన్యవాదాలు! నాకు అందింది: `{data}`\n\nఈ ID మా టీమ్ కింద రిజిస్టర్ అయ్యిందా?"
    },
    "gift_verified": {
        "en": "✅ *Verified Team Member!*\n\nPlease contact our admin:\n\n👤 Admin: {admin}\n🆔 Your ID: `{id}`\n\nSend your ID to the admin to claim your gift code.",
        "hi": "✅ *सत्यापित टीम सदस्य!*\n\nकृपया हमारे एडमिन से संपर्क करें:\n\n👤 एडमिन: {admin}\n🆔 आपकी आईडी: `{id}`\n\nगिफ्ट कोड प्राप्त करने के लिए अपनी आईडी एडमिन को भेजें।",
        "te": "✅ *ధృవీకరించబడిన టీమ్ సభ్యుడు!*\n\nదయచేసి మా అడ్మిన్‌ను సంప్రదించండి:\n\n👤 అడ్మిన్: {admin}\n🆔 మీ ID: `{id}`\n\nమీ గిఫ్ట్ కోడ్ పొందడానికి మీ IDని అడ్మిన్‌కు పంపండి."
    },
    "gift_not_reg": {
        "en": "❌ *Not Registered Yet*\n\nYou need to register first.\n\n🔗 Register using this link ONLY:\n{link}\n\nAfter registering, click /start and try again.",
        "hi": "❌ *अभी रजिस्टर्ड नहीं है*\n\nपहले रजिस्टर करें।\n\n🔗 केवल इस लिंक से रजिस्टर करें:\n{link}\n\nरजिस्टर के बाद /start क्लिक करें।",
        "te": "❌ *ఇంకా రిజిస్టర్ కాలేదు*\n\nమొదట రిజిస్టర్ చేయండి.\n\n🔗 ఈ లింక్ ద్వారా మాత్రమే రిజిస్టర్ చేయండి:\n{link}\n\nరిజిస్టర్ చేసిన తర్వాత /start క్లిక్ చేయండి."
    },
    # Referral
    "referral": {
        "en": "🔗 *Your Referral Link:*\n\n{link}\n\nShare this to earn bonuses!",
        "hi": "🔗 *आपका रेफरल लिंक:*\n\n{link}\n\nबोनस कमाने के लिए इसे शेयर करें!",
        "te": "🔗 *మీ రెఫరల్ లింక్:*\n\n{link}\n\nబోనస్ సంపాదించడానికి షేర్ చేయండి!"
    },
    # FAQ
    "faq": {
        "en": "❓ *FAQ:*\n\n1. *Login?* - Use phone/email\n2. *Password?* - Letters & numbers only\n3. *Withdraw?* - Wallet > Payout",
        "hi": "❓ *सामान्य प्रश्न:*\n\n1. *लॉगिन?* - फ़ोन/ईमेल उपयोग करें\n2. *पासवर्ड?* - केवल अक्षर और नंबर\n3. *विड्रॉ?* - वॉलेट > पेआउट",
        "te": "❓ *తరచుగా అడిగే ప్రశ్నలు:*\n\n1. *లాగిన్?* - ఫోన్/ఇమెయిల్ వాడండి\n2. *పాస్‌వర్డ్?* - అక్షరాలు & నంబర్లు మాత్రమే\n3. *విత్‌డ్రా?* - వాలెట్ > పేఅవుట్"
    },
    # Deposit/Withdraw
    "dep_menu": {
        "en": "💳 *Deposit / Withdraw Help*\n\nDeposit or Withdrawal issue?",
        "hi": "💳 *डिपॉजिट / विड्रॉ हेल्प*\n\nडिपॉजिट या विड्रॉ समस्या?",
        "te": "💳 *డిపాజిట్ / విత్‌డ్రా సహాయం*\n\nడిపాజిట్ లేదా విత్‌డ్రా సమస్య?"
    },
    "dep_trouble": {
        "en": "💵 *Deposit Issue:*\n\n1. Go to Wallet\n2. Select UPI/Bank\n3. Min ₹100\n4. Wait 5-10 mins\n\nDid this solve your issue?",
        "hi": "💵 *डिपॉजिट समस्या:*\n\n1. वॉलेट पर जाएं\n2. UPI/बैंक चुनें\n3. न्यूनतम ₹100\n4. 5-10 मिनट प्रतीक्षा करें\n\nक्या समस्या हल हो गई?",
        "te": "💵 *డిపాజిట్ సమస్య:*\n\n1. వాలెట్‌కు వెళ్లండి\n2. UPI/బ్యాంక్ ఎంచుకోండి\n3. కనీసం ₹100\n4. 5-10 నిమిషాలు వేచి ఉండండి\n\nసమస్య పరిష్కారమైందా?"
    },
    "with_trouble": {
        "en": "🏧 *Withdrawal Issue:*\n\n1. Go to Wallet > Payout\n2. Bind Bank/UPI correctly\n3. Min ₹200\n4. Wait 30 mins\n\nDid this solve your issue?",
        "hi": "🏧 *विड्रॉ समस्या:*\n\n1. वॉलेट > पेआउट पर जाएं\n2. बैंक/UPI सही से बांधें\n3. न्यूनतम ₹200\n4. 30 मिनट प्रतीक्षा करें\n\nक्या समस्या हल हो गई?",
        "te": "🏧 *విత్‌డ్రా సమస్య:*\n\n1. వాలెట్ > పేఅవుట్‌కు వెళ్లండి\n2. బ్యాంక్/UPI సరిగ్గా బైండ్ చేయండి\n3. కనీసం ₹200\n4. 30 నిమిషాలు వేచి ఉండండి\n\nసమస్య పరిష్కారమైందా?"
    },
    "solved": {
        "en": "🎉 Great! Click /start for anything else.",
        "hi": "🎉 बहुत बढ़िया! किसी और चीज़ के लिए /start क्लिक करें।",
        "te": "🎉 అద్భుతం! మరేదైనా కోసం /start క్లిక్ చేయండి."
    },
    "human_required": {
        "en": "💬 *Human Support Required*\n\nPlease contact our admin:\n\n👤 {admin}\n\nSend a screenshot of your issue.",
        "hi": "💬 *ह्यूमन सपोर्ट चाहिए*\n\nकृपया हमारे एडमिन से संपर्क करें:\n\n👤 {admin}\n\nअपनी समस्या का स्क्रीनशॉट भेजें।",
        "te": "💬 *మానవ సహాయం అవసరం*\n\nదయచేసి మా అడ్మిన్‌ను సంప్రదించండి:\n\n👤 {admin}\n\nమీ సమస్య స్క్రీన్‌షాట్ పంపండి."
    },
    # Human agent
    "human_prompt": {
        "en": "💬 *Talk to Human Agent*\n\nDescribe your issue below. You can also send a screenshot.",
        "hi": "💬 *ह्यूमन एजेंट से बात करें*\n\nनीचे अपनी समस्या बताएं। स्क्रीनशॉट भी भेज सकते हैं।",
        "te": "💬 *మానవ ఏజెంట్‌తో మాట్లాడండి*\n\nమీ సమస్యను క్రింద వివరించండి. స్క్రీన్‌షాట్ కూడా పంపవచ్చు."
    },
    "human_received": {
        "en": "✅ *Issue Received*\n\n`{data}`\n\nContact admin:\n\n👤 {admin}",
        "hi": "✅ *समस्या प्राप्त हुई*\n\n`{data}`\n\nएडमिन से संपर्क करें:\n\n👤 {admin}",
        "te": "✅ *సమస్య అందింది*\n\n`{data}`\n\nఅడ్మిన్‌ను సంప్రదించండి:\n\n👤 {admin}"
    },
    # Keywords
    "kw_unknown": {
        "en": "🤔 I didn't understand that. Try keywords:\n\n• *otp*\n• *password*\n• *withdraw*\n• *deposit*\n• *login*\n• *register*\n• *bonus*\n\nOr use the menu.",
        "hi": "🤔 मुझे समझ नहीं आया। कीवर्ड आज़माएं:\n\n• *otp*\n• *password*\n• *withdraw*\n• *deposit*\n• *login*\n• *register*\n• *bonus*\n\nया मेनू का उपयोग करें।",
        "te": "🤔 నాకు అర్థం కాలేదు. కీవర్డ్‌లు ప్రయత్నించండి:\n\n• *otp*\n• *password*\n• *withdraw*\n• *deposit*\n• *login*\n• *register*\n• *bonus*\n\nలేదా మెనూ వాడండి."
    },
    "kw_otp_title": {
        "en": "📩 OTP Not Received?",
        "hi": "📩 OTP नहीं आया?",
        "te": "📩 OTP రాలేదా?"
    },
    "kw_otp_body": {
        "en": "Try these:\n\n1️⃣ Wait 60 seconds\n2️⃣ Check network signal\n3️⃣ Restart your phone\n4️⃣ Don't request more than 3 times\n\nStill not received? Contact: {admin}",
        "hi": "यह आज़माएं:\n\n1️⃣ 60 सेकंड प्रतीक्षा करें\n2️⃣ नेटवर्क सिग्नल जांचें\n3️⃣ फ़ोन रीस्टार्ट करें\n4️⃣ 3 बार से ज़्यादा OTP न मांगें\n\nफिर भी नहीं आया? संपर्क: {admin}",
        "te": "ఇవి ప్రయత్నించండి:\n\n1️⃣ 60 సెకన్లు వేచి ఉండండి\n2️⃣ నెట్‌వర్క్ సిగ్నల్ చూడండి\n3️⃣ ఫోన్ రీస్టార్ట్ చేయండి\n4️⃣ 3 సార్లకు మించి అడగవద్దు\n\nఇంకా రాలేదా? సంప్రదించండి: {admin}"
    },
    "kw_pwd_title": {
        "en": "🔑 Password Help",
        "hi": "🔑 पासवर्ड मदद",
        "te": "🔑 పాస్‌వర్డ్ సహాయం"
    },
    "kw_pwd_body": {
        "en": "Password must contain:\n\n✅ Capital letters (A-Z)\n✅ Small letters (a-z)\n✅ Numbers (0-9)\n\n❌ NO symbols like @ # $ % & !\n\nForgot password? Use 'Forgot Password' on login page.",
        "hi": "पासवर्ड में होना चाहिए:\n\n✅ बड़े अक्षर (A-Z)\n✅ छोटे अक्षर (a-z)\n✅ नंबर (0-9)\n\n❌ @ # $ % & ! जैसे चिन्ह नहीं\n\nपासवर्ड भूल गए? लॉगिन पेज पर 'Forgot Password' उपयोग करें।",
        "te": "పాస్‌వర్డ్‌లో ఉండాలి:\n\n✅ పెద్ద అక్షరాలు (A-Z)\n✅ చిన్న అక్షరాలు (a-z)\n✅ నంబర్లు (0-9)\n\n❌ @ # $ % & ! వంటి చిహ్నాలు వద్దు\n\nపాస్‌వర్డ్ మర్చిపోయారా? లాగిన్ పేజీలో 'Forgot Password' వాడండి."
    },
    "kw_with_title": {
        "en": "🏧 Withdrawal Guide",
        "hi": "🏧 विड्रॉ गाइड",
        "te": "🏧 విత్‌డ్రా గైడ్"
    },
    "kw_with_body": {
        "en": "To withdraw:\n\n1️⃣ Login\n2️⃣ Wallet → Payout\n3️⃣ Enter Bank/UPI ID\n4️⃣ Amount (Min ₹200)\n5️⃣ Submit\n\n⚡ Process in 10-30 mins.\n\nPending? Contact: {admin}",
        "hi": "विड्रॉ करने के लिए:\n\n1️⃣ लॉगिन करें\n2️⃣ वॉलेट → पेआउट\n3️⃣ बैंक/UPI आईडी दर्ज करें\n4️⃣ राशि (न्यूनतम ₹200)\n5️⃣ सबमिट करें\n\n⚡ 10-30 मिनट में प्रोसेस।\n\nपेंडिंग? संपर्क: {admin}",
        "te": "విత్‌డ్రా చేయడానికి:\n\n1️⃣ లాగిన్\n2️⃣ వాలెట్ → పేఅవుట్\n3️⃣ బ్యాంక్/UPI ID నమోదు చేయండి\n4️⃣ మొత్తం (కనీసం ₹200)\n5️⃣ సబ్మిట్\n\n⚡ 10-30 నిమిషాల్లో ప్రాసెస్.\n\nపెండింగ్? సంప్రదించండి: {admin}"
    },
    "kw_dep_title": {
        "en": "💵 Deposit Guide",
        "hi": "💵 डिपॉजिट गाइड",
        "te": "💵 డిపాజిట్ గైడ్"
    },
    "kw_dep_body": {
        "en": "To deposit:\n\n1️⃣ Login\n2️⃣ Wallet → Deposit\n3️⃣ UPI/Bank\n4️⃣ Amount (Min ₹100)\n5️⃣ Complete payment\n\n⏱️ Balance in 5-10 mins.\n\nNot credited? Contact: {admin}",
        "hi": "डिपॉजिट करने के लिए:\n\n1️⃣ लॉगिन करें\n2️⃣ वॉलेट → डिपॉजिट\n3️⃣ UPI/बैंक\n4️⃣ राशि (न्यूनतम ₹100)\n5️⃣ भुगतान पूरा करें\n\n⏱️ 5-10 मिनट में बैलेंस।\n\nक्रेडिट नहीं हुआ? संपर्क: {admin}",
        "te": "డిపాజిట్ చేయడానికి:\n\n1️⃣ లాగిన్\n2️⃣ వాలెట్ → డిపాజిట్\n3️⃣ UPI/బ్యాంక్\n4️⃣ మొత్తం (కనీసం ₹100)\n5️⃣ పేమెంట్ పూర్తి చేయండి\n\n⏱️ 5-10 నిమిషాల్లో బ్యాలెన్స్.\n\nక్రెడిట్ కాలేదా? సంప్రదించండి: {admin}"
    },
    "kw_login_title": {
        "en": "🔓 Login Help",
        "hi": "🔓 लॉगिन मदद",
        "te": "🔓 లాగిన్ సహాయం"
    },
    "kw_login_body": {
        "en": "To login:\n\n1️⃣ Open RaxiWin app\n2️⃣ Click Login\n3️⃣ Enter phone/email\n4️⃣ Enter password\n5️⃣ OTP verify\n\nCan't login? Reset password.",
        "hi": "लॉगिन करने के लिए:\n\n1️⃣ RaxiWin ऐप खोलें\n2️⃣ लॉगिन क्लिक करें\n3️⃣ फ़ोन/ईमेल दर्ज करें\n4️⃣ पासवर्ड दर्ज करें\n5️⃣ OTP सत्यापित करें\n\nलॉगिन नहीं हो रहा? पासवर्ड रीसेट करें।",
        "te": "లాగిన్ చేయడానికి:\n\n1️⃣ RaxiWin యాప్ తెరవండి\n2️⃣ లాగిన్ క్లిక్ చేయండి\n3️⃣ ఫోన్/ఇమెయిల్ నమోదు చేయండి\n4️⃣ పాస్‌వర్డ్ నమోదు చేయండి\n5️⃣ OTP ధృవీకరించండి\n\nలాగిన్ కావడం లేదా? పాస్‌వర్డ్ రీసెట్ చేయండి."
    },
    "kw_reg_title": {
        "en": "📝 Registration Help",
        "hi": "📝 रजिस्ट्रेशन मदद",
        "te": "📝 రిజిస్ట్రేషన్ సహాయం"
    },
    "kw_reg_body": {
        "en": "To register:\n\n1️⃣ Click: {link}\n2️⃣ Enter phone number\n3️⃣ Set password (letters + numbers)\n4️⃣ Invitation code: 74158275546\n5️⃣ Complete registration",
        "hi": "रजिस्टर करने के लिए:\n\n1️⃣ क्लिक करें: {link}\n2️⃣ फ़ोन नंबर दर्ज करें\n3️⃣ पासवर्ड सेट करें (अक्षर + नंबर)\n4️⃣ इनविटेशन कोड: 74158275546\n5️⃣ रजिस्ट्रेशन पूरा करें",
        "te": "రిజిస్టర్ చేయడానికి:\n\n1️⃣ క్లిక్ చేయండి: {link}\n2️⃣ ఫోన్ నంబర్ నమోదు చేయండి\n3️⃣ పాస్‌వర్డ్ సెట్ చేయండి (అక్షరాలు + నంబర్లు)\n4️⃣ ఇన్విటేషన్ కోడ్: 74158275546\n5️⃣ రిజిస్ట్రేషన్ పూర్తి చేయండి"
    },
    "kw_bonus_title": {
        "en": "🎁 Today's Bonus",
        "hi": "🎁 आज का बोनस",
        "te": "🎁 ఈరోజు బోనస్"
    },
    "kw_bonus_body": {
        "en": "Gift code:\n\n`{code}`\n\nRedeem in game's Bonus section.\n\n⚠️ Valid 24 hours only.",
        "hi": "गिफ्ट कोड:\n\n`{code}`\n\nगेम के Bonus सेक्शन में रिडीम करें।\n\n⚠️ केवल 24 घंटे मान्य।",
        "te": "గిఫ్ట్ కోడ్:\n\n`{code}`\n\nగేమ్ Bonus సెక్షన్‌లో రీడీమ్ చేయండి.\n\n⚠️ 24 గంటలు మాత్రమే చెల్లుతుంది."
    },
    "kw_help_title": {
        "en": "🆘 Need Help?",
        "hi": "🆘 मदद चाहिए?",
        "te": "🆘 సహాయం కావాలా?"
    },
    "kw_help_body": {
        "en": "I can help with:\n\n• Login / Register\n• Deposit / Withdraw\n• OTP issues\n• Password reset\n• Gift codes\n\nType a keyword or use menu.",
        "hi": "मैं इनमें मदद कर सकता हूँ:\n\n• लॉगिन / रजिस्टर\n• डिपॉजिट / विड्रॉ\n• OTP समस्या\n• पासवर्ड रीसेट\n• गिफ्ट कोड\n\nकीवर्ड टाइप करें या मेनू उपयोग करें।",
        "te": "నేను సహాయం చేయగలను:\n\n• లాగిన్ / రిజిస్టర్\n• డిపాజిట్ / విత్‌డ్రా\n• OTP సమస్యలు\n• పాస్‌వర్డ్ రీసెట్\n• గిఫ్ట్ కోడ్‌లు\n\nకీవర్డ్ టైప్ చేయండి లేదా మెనూ వాడండి."
    },
}


def t(key, lang, **kwargs):
    """Get translated text for a key"""
    text = TEXTS.get(key, {}).get(lang, TEXTS.get(key, {}).get("en", ""))
    if kwargs:
        try:
            return text.format(**kwargs)
        except:
            return text
    return text


def get_lang(user_id):
    """Get saved language for a user, default English"""
    return user_langs.get(user_id, "en")


# --- LOG ---
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
    user_id = query.from_user.id
    user_langs[user_id] = lang
    
    # Show confirmation + main menu
    await query.edit_message_text(t("lang_set", lang), parse_mode='Markdown')
    await main_menu(update, context)
    return ASK_GAME_ID  # goes back to main flow


# --- MAIN MENU ---
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id if update.effective_user else update.callback_query.from_user.id
    lang = get_lang(user_id)
    
    keyboard = [
        [InlineKeyboardButton(t("btn_gift", lang), callback_data='gift')],
        [InlineKeyboardButton(t("btn_referral", lang), callback_data='referral')],
        [InlineKeyboardButton(t("btn_deposit", lang), callback_data='deposit')],
        [InlineKeyboardButton(t("btn_faq", lang), callback_data='faq')],
        [InlineKeyboardButton(t("btn_human", lang), callback_data='human')]
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
            f"🆕 *NEW USER*\n\n"
            f"👤 {user.first_name}\n"
            f"📛 @{user.username if user.username else 'N/A'}\n"
            f"🆔 `{user.id}`\n"
            f"👥 Total: `{len(known_users)}`")
    
    # If user has a saved language, go straight to menu
    if user.id in user_langs:
        await main_menu(update, context)
        return ASK_GAME_ID
    
    # Otherwise ask for language
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


# --- ADMIN COMMANDS ---
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != ADMIN_NUMERIC_ID:
        return ConversationHandler.END
    await update.message.reply_text(f"📢 Broadcast Mode\n👥 Total: `{len(known_users)}`\n\nSend the message. /cancel to abort.", parse_mode='Markdown')
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
    await status_msg.edit_text(f"✅ Broadcast done!\n📤 Sent: {success}\n❌ Failed: {failed}", parse_mode='Markdown')
    return ConversationHandler.END


# --- FLOWS ---
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
        await log_to_channel(context.bot, f"❌ Unregistered\n👤 {user.first_name}\n🆔 `{game_id}`")
    
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
    user = query.from_user
    
    if query.data == 'dep_issue':
        text = t("dep_trouble", lang)
        state = DEPOSIT_HELP
        await log_to_channel(context.bot, f"💵 Deposit Help\n👤 {user.first_name}")
    else:
        text = t("with_trouble", lang)
        state = WITHDRAW_HELP
        await log_to_channel(context.bot, f"🏧 Withdraw Help\n👤 {user.first_name}")
    
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
    await log_to_channel(context.bot, f"💬 HUMAN REQUEST\n👤 {user.first_name}\n📛 @{user.username if user.username else 'N/A'}\n📝 {user_data}")
    return ConversationHandler.END


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    lang = get_lang(query.from_user.id)
    
    if query.data == 'referral':
        text = t("referral", lang, link=REGISTER_LINK)
    elif query.data == 'faq':
        text = t("faq", lang)
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


# --- MAIN ---
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
            CallbackQueryHandler(set_language, pattern='^lang_(en|hi|te)$')
        ],
        states={
            CHOOSE_LANG: [
                CallbackQueryHandler(set_language, pattern='^lang_(en|hi|te)$'),
                CallbackQueryHandler(button_click)
            ],
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
    
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("language", language_command))
    app_bot.add_handler(broadcast_conv)
    app_bot.add_handler(main_conv)
    app_bot.add_handler(CallbackQueryHandler(button_click))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, keyword_auto_reply))
    
    print("Bot running with 3 languages!")
    app_bot.run_polling()
