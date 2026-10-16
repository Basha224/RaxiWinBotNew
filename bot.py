import logging
import threading
import os
import asyncio
from datetime import datetime, timedelta
from flask import Flask
from supabase import create_client, Client
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, MessageHandler, filters,
)

# ═══════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════
TOKEN ="8740602277:AAHCyrrNtkUBg3Pn0-i5vqU_igl0Eec0Xm4"
ADMIN_ID = "@proearner0"
ADMIN_NUMERIC_ID = 6081001025
LOG_CHANNEL_ID = ADMIN_NUMERIC_ID

REGISTER_LINK = "https://bdg4.vip/#/register?invitationCode=x5Vcp861092"
INVITE_CODE = "x5Vcp861092"
TELEGRAM_CHANNEL = "https://t.me/+H8f_nP-zUCZhMzll"
PREDICTOR_BOT = "https://t.me/RaxiWinPredictor_bot"
TODAY_GIFT_CODE = "4346F170B0051BD21B95EE9DECBAC10C"
SUPPORT_BOT_NAME = "BDG Game Support"

SUPABASE_URL = "https://izxzdcvymipyvxcrgbee.supabase.co"
SUPABASE_KEY = "sb_publishable_KYwqH8JMDCk9utMYyP9Eyg_WFAjUuZS"
# ═══════════════════════════════════════════

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

(CHOOSE_LANG, MAIN_MENU, ASK_GAME_ID, ASK_TEAM_STATUS, DEPOSIT_MENU,
 DEPOSIT_HELP, WITHDRAW_HELP, HUMAN_AGENT, BROADCAST_MSG) = range(9)

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

app = Flask(__name__)
@app.route('/')
def home(): return "BDG Game Premium Bot is running 24/7!"
def run_web_server():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# ═══════════════════════════════════════════
#  DATABASE LAYER
# ═══════════════════════════════════════════
def save_user(user_id, username, first_name, referrer_id=None):
    try:
        r = supabase.table('users').select('user_id').eq('user_id', user_id).execute()
        if len(r.data) == 0:
            supabase.table('users').insert({
                "user_id": user_id, "username": username or "",
                "first_name": first_name or "", "language": "en",
                "referrer_id": referrer_id,
                "joined_at": datetime.now().isoformat(),
                "last_checkin": datetime.now().isoformat(),
                "streak": 1, "total_checkins": 1, "xp": 10, "level": 1,
            }).execute()
            return True
        return False
    except Exception as e:
        logging.error(f"save_user: {e}"); return False

def get_user(user_id):
    try:
        r = supabase.table('users').select('*').eq('user_id', user_id).execute()
        return r.data[0] if r.data else None
    except Exception as e:
        logging.error(f"get_user: {e}"); return None

def get_lang(user_id):
    u = get_user(user_id)
    return u.get('language', 'en') if u else 'en'

def set_lang(user_id, lang):
    try: supabase.table('users').update({"language": lang}).eq('user_id', user_id).execute()
    except Exception as e: logging.error(f"set_lang: {e}")

def update_checkin(user_id):
    try:
        u = get_user(user_id)
        if not u: return 0
        now = datetime.now()
        last = u.get('last_checkin')
        streak = u.get('streak', 0)
        if last:
            try:
                last_dt = datetime.fromisoformat(last.replace('Z','').split('+')[0])
                if now - last_dt < timedelta(hours=20):
                    return -1  # already checked in today
                elif now - last_dt < timedelta(hours=48):
                    streak += 1
                else:
                    streak = 1
            except: streak = 1
        else: streak = 1
        xp = u.get('xp', 0) + 10 + min(streak, 10)
        level = max(1, xp // 100 + 1)
        supabase.table('users').update({
            "last_checkin": now.isoformat(),
            "streak": streak,
            "total_checkins": u.get('total_checkins', 0) + 1,
            "xp": xp, "level": level,
        }).eq('user_id', user_id).execute()
        return streak
    except Exception as e:
        logging.error(f"checkin: {e}"); return 0

def get_referral_count(user_id):
    try:
        r = supabase.table('users').select('user_id').eq('referrer_id', user_id).execute()
        return len(r.data)
    except: return 0

def get_all_user_ids():
    try:
        r = supabase.table('users').select('user_id').execute()
        return [row['user_id'] for row in r.data]
    except: return []

def count_users():
    try:
        r = supabase.table('users').select('user_id').execute()
        return len(r.data)
    except: return 0

def log_to_channel(bot, msg):
    try: return bot.send_message(chat_id=LOG_CHANNEL_ID, text=msg, parse_mode='Markdown')
    except Exception as e: logging.error(f"log: {e}")

# ═══════════════════════════════════════════
#  TRANSLATIONS
# ═══════════════════════════════════════════
TEXTS = {
 "lang_set": {"en":"✅ Language set to English!","hi":"✅ भाषा हिंदी में सेट!","te":"✅ భాష తెలుగులో సెట్!"},
 "welcome": {"en":"👋 Welcome back, {name}!\n\n🎯 *BDG Game Support Bot*\nYour personal gaming assistant — 24/7 online.","hi":"👋 वापसी पर स्वागत, {name}!\n\n🎯 *BDG Game सपोर्ट बॉट*\nआपका 24/7 गेमिंग सहायक।","te":"👋 తిరిగి స్వాగతం, {name}!\n\n🎯 *BDG Game సపోర్ట్ బాట్*\nమీ 24/7 గేమింగ్ సహాయకుడు."},
 "b_gift":   {"en":"🎁 Daily Gift Code","hi":"🎁 डेली गिफ्ट कोड","te":"🎁 డైలీ గిఫ్ట్ కోడ్"},
 "b_ref":    {"en":"🔗 My Referral Link","hi":"🔗 मेरा रेफरल लिंक","te":"🔗 నా రెఫరల్ లింక్"},
 "b_pred":   {"en":"🎯 AI Predictor","hi":"🎯 AI प्रेडिक्टर","te":"🎯 AI ప్రిడిక్టర్"},
 "b_dep":    {"en":"💳 Deposit / Withdraw","hi":"💳 डिपॉजिट / विड्रॉ","te":"💳 డిపాజిట్ / విత్‌డ్రా"},
 "b_faq":    {"en":"❓ FAQ","hi":"❓ सामान्य प्रश्न","te":"❓ తరచుగా అడిగేవి"},
 "b_human":  {"en":"💬 Human Agent","hi":"💬 ह्यूमन एजेंट","te":"💬 మానవ ఏజెంట్"},
 "b_profile":{"en":"👤 My Profile","hi":"👤 मेरी प्रोफ़ाइल","te":"👤 నా ప్రొఫైల్"},
 "b_channel":{"en":"📢 Official Channel","hi":"📢 आधिकारिक चैनल","te":"📢 అధికారిక ఛానెల్"},
 "b_lang":   {"en":"🌐 Language","hi":"🌐 भाषा","te":"🌐 భాష"},
 "b_back":   {"en":"⬅️ Back to Menu","hi":"⬅️ मेनू पर वापस","te":"⬅️ మెనూకు తిరిగి"},
 "b_contact":{"en":"💬 Contact Admin","hi":"💬 एडमिन से संपर्क","te":"💬 అడ్మిన్‌ను సంప్రదించండి"},
 "b_yes_reg":{"en":"✅ I'm Registered","hi":"✅ मैं रजिस्टर्ड हूँ","te":"✅ నేను రిజిస్టర్ అయ్యాను"},
 "b_no_new": {"en":"❌ I'm New","hi":"❌ मैं नया हूँ","te":"❌ నేను కొత్తవాడిని"},
 "b_dep_iss":{"en":"💵 Deposit Issue","hi":"💵 डिपॉजिट समस्या","te":"💵 డిపాజిట్ సమస్య"},
 "b_wd_iss": {"en":"🏧 Withdrawal Issue","hi":"🏧 विड्रॉ समस्या","te":"🏧 విత్‌డ్రా సమస్య"},
 "b_solved": {"en":"✅ Solved","hi":"✅ हल हो गया","te":"✅ పరిష్కారమైంది"},
 "b_need_h": {"en":"❌ Contact Human","hi":"❌ ह्यूमन से संपर्क","te":"❌ మానవుడిని సంప్రదించండి"},
 "gift_prompt": {"en":"🎁 *Daily Gift Code*\n\nSend me your *BDG Game ID* to claim today's code.","hi":"🎁 *डेली गिफ्ट कोड*\n\nआज का कोड पाने के लिए अपनी *BDG Game ID* भेजें।","te":"🎁 *డైలీ గిఫ్ట్ కోడ్*\n\nఈరోజు కోడ్ పొందడానికి మీ *BDG Game ID* పంపండి."},
 "gift_received": {"en":"Received: `{data}`\n\n✅ Are you registered under our team?","hi":"मिला: `{data}`\n\n✅ क्या आप हमारी टीम में हैं?","te":"అందింది: `{data}`\n\n✅ మీరు మా టీమ్‌లో ఉన్నారా?"},
 "gift_verified": {"en":"✅ *Verified Team Member!*\n\n💬 Contact admin to claim code:\n👤 {admin}\n🆔 `{id}`\n\n📢 Join our channel for daily codes.","hi":"✅ *सत्यापित सदस्य!*\n\n💬 कोड पाने के लिए एडमिन से संपर्क:\n👤 {admin}\n🆔 `{id}`","te":"✅ *ధృవీకరించబడిన సభ్యుడు!*\n\n💬 కోడ్ కోసం అడ్మిన్:\n👤 {admin}\n🆔 `{id}`"},
 "gift_not_reg": {"en":"❌ *Not Registered*\n\nRegister now → {link}\n\nInvite Code: `{invite}`","hi":"❌ *रजिस्टर्ड नहीं*\n\nअभी रजिस्टर करें → {link}\n\nइनविटेशन कोड: `{invite}`","te":"❌ *రిజిస్టర్ కాలేదు*\n\nఇప్పుడే రిజిస్టర్ → {link}\n\nఇన్విటేషన్ కోడ్: `{invite}`"},
 "referral": {"en":"🔗 *Your Referral Link*\n\n{link}\n\n🎫 Invite Code: `{invite}`\n👥 Referrals: *{refs}*\n\n💰 Earn bonus for every friend!","hi":"🔗 *आपका रेफरल लिंक*\n\n{link}\n\n🎫 कोड: `{invite}`\n👥 रेफरल: *{refs}*\n\n💰 हर दोस्त पर बोनस!","te":"🔗 *మీ రెఫరల్ లింక్*\n\n{link}\n\n🎫 కోడ్: `{invite}`\n👥 రెఫరల్స్: *{refs}*"},
 "profile": {"en":"👤 *Your BDG Profile*\n━━━━━━━━━━━━━━━\n🆔 ID: `{id}`\n👤 Name: *{name}*\n💎 Level: *{level}*\n⚡ XP: *{xp}*\n🔥 Streak: *{streak} days*\n📆 Check-ins: *{checkins}*\n👥 Referrals: *{refs}*\n🌐 Language: *{lang}*\n🗓 Joined: *{joined}*\n━━━━━━━━━━━━━━━\n💡 Stay active to level up!","hi":"👤 *आपकी BDG प्रोफ़ाइल*\n━━━━━━━━━━━━━━━\n🆔 ID: `{id}`\n👤 नाम: *{name}*\n💎 लेवल: *{level}*\n⚡ XP: *{xp}*\n🔥 स्ट्रीक: *{streak} दिन*\n📆 चेक-इन: *{checkins}*\n👥 रेफरल: *{refs}*\n🌐 भाषा: *{lang}*","te":"👤 *మీ BDG ప్రొఫైల్*\n━━━━━━━━━━━━━━━\n🆔 ID: `{id}`\n👤 పేరు: *{name}*\n💎 లెవెల్: *{level}*\n⚡ XP: *{xp}*\n🔥 స్ట్రీక్: *{streak} రోజులు*\n📆 చెక్-ఇన్: *{checkins}*\n👥 రెఫరల్స్: *{refs}*"},
 "faq": {"en":"❓ *BDG FAQ*\n━━━━━━━━━━━━━━━\n1️⃣ *Login:* Phone/Email + Password\n2️⃣ *Password:* Letters & numbers only\n3️⃣ *Deposit:* Wallet → UPI/Bank, Min ₹100\n4️⃣ *Withdraw:* Wallet → Payout, Min ₹200\n5️⃣ *Invite Code:* `{invite}`\n6️⃣ *Withdrawal Time:* 10-30 mins\n━━━━━━━━━━━━━━━\n💬 Need more? Use Human Agent.","hi":"❓ *BDG सामान्य प्रश्न*\n━━━━━━━━━━━━━━━\n1️⃣ *लॉगिन:* फ़ोन/ईमेल\n2️⃣ *पासवर्ड:* अक्षर + नंबर\n3️⃣ *डिपॉजिट:* वॉलेट → ₹100\n4️⃣ *विड्रॉ:* वॉलेट → ₹200\n5️⃣ *कोड:* `{invite}`\n6️⃣ *टाइम:* 10-30 मिनट","te":"❓ *BDG FAQ*\n━━━━━━━━━━━━━━━\n1️⃣ *లాగిన్:* ఫోన్/ఇమెయిల్\n2️⃣ *పాస్‌వర్డ్:* అక్షరాలు+నంబర్లు\n3️⃣ *డిపాజిట్:* ₹100\n4️⃣ *విత్‌డ్రా:* ₹200\n5️⃣ *కోడ్:* `{invite}`"},
 "dep_menu": {"en":"💳 *Deposit / Withdraw Help*\n\nChoose your issue:","hi":"💳 *डिपॉजिट / विड्रॉ*\n\nसमस्या चुनें:","te":"💳 *డిపాజిట్ / విత్‌డ్రా*\n\nసమస్య ఎంచుకోండి:"},
 "dep_help": {"en":"💵 *Deposit Issue*\n━━━━━━━━━━━━━━━\n1️⃣ Open Wallet\n2️⃣ Select UPI / Bank\n3️⃣ Enter amount (Min ₹100)\n4️⃣ Complete payment\n5️⃣ Wait 5-10 mins\n━━━━━━━━━━━━━━━\n✅ Solved?","hi":"💵 *डिपॉजिट समस्या*\n1️⃣ वॉलेट खोलें\n2️⃣ UPI/बैंक\n3️⃣ ₹100 न्यूनतम\n4️⃣ भुगतान\n5️⃣ 5-10 मिनट","te":"💵 *డిపాజిట్ సమస్య*\n1️⃣ వాలెట్\n2️⃣ UPI/బ్యాంక్\n3️⃣ ₹100\n4️⃣ పేమెంట్\n5️⃣ 5-10 నిమిషాలు"},
 "wd_help": {"en":"🏧 *Withdrawal Issue*\n━━━━━━━━━━━━━━━\n1️⃣ Open Wallet → Payout\n2️⃣ Bind Bank / UPI correctly\n3️⃣ Min ₹200\n4️⃣ Submit\n5️⃣ Wait 10-30 mins\n━━━━━━━━━━━━━━━\n✅ Solved?","hi":"🏧 *विड्रॉ समस्या*\n1️⃣ वॉलेट → पेआउट\n2️⃣ बैंक/UPI बांधें\n3️⃣ ₹200\n4️⃣ सबमिट\n5️⃣ 10-30 मिनट","te":"🏧 *విత్‌డ్రా సమస్య*\n1️⃣ వాలెట్ → పేఅవుట్\n2️⃣ బ్యాంక్/UPI\n3️⃣ ₹200\n4️⃣ సబ్మిట్"},
 "solved": {"en":"🎉 Great! Click /start for more.","hi":"🎉 बढ़िया! /start करें।","te":"🎉 అద్భుతం! /start."},
 "human_req": {"en":"💬 *Human Support Required*\n\nContact: {admin}\n📢 Channel: below","hi":"💬 *ह्यूमन सपोर्ट*\n\nसंपर्क: {admin}","te":"💬 *మానవ సహాయం*\n\nసంప్రదించండి: {admin}"},
 "human_prompt": {"en":"💬 *Talk to Human Agent*\n\nDescribe your issue. Send text or screenshot.","hi":"💬 *ह्यूमन एजेंट*\n\nसमस्या बताएं। स्क्रीनशॉट भी भेज सकते हैं।","te":"💬 *మానవ ఏజెంట్*\n\nమీ సమస్య. స్క్రీన్‌షాట్ కూడా."},
 "human_received": {"en":"✅ *Received!*\n\n📝 `{data}`\n\n💬 Contact admin now: {admin}","hi":"✅ *मिला!*\n\n📝 `{data}`\n\n💬 एडमिन: {admin}","te":"✅ *అందింది!*\n\n📝 `{data}`\n\n💬 అడ్మిన్: {admin}"},
 "kw_unknown": {"en":"🤔 Try keywords:\n\n• otp • password • withdraw\n• deposit • login • register\n• bonus • gift","hi":"🤔 कीवर्ड:\n\n• otp • password\n• withdraw • deposit\n• login • register • bonus","te":"🤔 కీవర్డ్‌లు:\n\n• otp • password\n• withdraw • deposit\n• login • register • bonus"},
 "kw_otp_t": {"en":"📩 OTP Not Received?","hi":"📩 OTP नहीं आया?","te":"📩 OTP రాలేదా?"},
 "kw_otp_b": {"en":"1️⃣ Wait 60 sec\n2️⃣ Check network\n3️⃣ Restart phone\n4️⃣ Try again\n\nStill? {admin}","hi":"1️⃣ 60 सेकंड\n2️⃣ नेटवर्क\n3️⃣ रीस्टार्ट\n\nफिर भी? {admin}","te":"1️⃣ 60 సెకన్లు\n2️⃣ నెట్‌వర్క్\n3️⃣ రీస్టార్ట్\n\nఇంకా? {admin}"},
 "kw_pwd_t": {"en":"🔑 Password Help","hi":"🔑 पासवर्ड","te":"🔑 పాస్‌వర్డ్"},
 "kw_pwd_b": {"en":"✅ Capital (A-Z)\n✅ Small (a-z)\n✅ Numbers (0-9)\n❌ NO symbols\n\nForgot? Reset on login.","hi":"✅ बड़े (A-Z)\n✅ छोटे (a-z)\n✅ नंबर (0-9)\n❌ चिन्ह नहीं","te":"✅ A-Z a-z 0-9\n❌ చిహ్నాలు వద్దు"},
 "kw_wd_t": {"en":"🏧 Withdrawal Help","hi":"🏧 विड्रॉ सहायता","te":"🏧 విత్‌డ్రా సహాయం"},
 "kw_wd_b": {"en":"1. Login\n2. Wallet → Payout\n3. Bank/UPI\n4. Min ₹200\n5. Submit\n\n⏱ 10-30 min","hi":"1. लॉगिन\n2. वॉलेट → पेआउट\n3. बैंक/UPI\n4. ₹200\n5. सबमिट","te":"1. లాగిన్\n2. వాలెట్ → పేఅవుట్\n3. బ్యాంక్\n4. ₹200"},
 "kw_dep_t": {"en":"💵 Deposit Help","hi":"💵 डिपॉजिट","te":"💵 డిపాజిట్"},
 "kw_dep_b": {"en":"1. Login\n2. Wallet → Deposit\n3. UPI/Bank\n4. Min ₹100\n\n⏱ 5-10 min","hi":"1. लॉगिन\n2. वॉलेट → डिपॉजिट\n3. UPI/बैंक\n4. ₹100","te":"1. లాగిన్\n2. వాలెట్ → డిపాజిట్\n3. UPI\n4. ₹100"},
 "kw_lg_t": {"en":"🔓 Login Help","hi":"🔓 लॉगिन","te":"🔓 లాగిన్"},
 "kw_lg_b": {"en":"1. Open BDG app\n2. Login\n3. Phone/email\n4. Password\n5. OTP verify","hi":"1. ऐप खोलें\n2. लॉगिन\n3. फ़ोन/ईमेल\n4. पासवर्ड\n5. OTP","te":"1. యాప్\n2. లాగిన్\n3. ఫోన్\n4. పాస్‌వర్డ్\n5. OTP"},
 "kw_rg_t": {"en":"📝 Register on BDG","hi":"📝 BDG पर रजिस्टर","te":"📝 BDG రిజిస్టర్"},
 "kw_rg_b": {"en":"1. Click: {link}\n2. Phone number\n3. Password (letters+numbers)\n4. Code: `{invite}`","hi":"1. क्लिक: {link}\n2. फ़ोन\n3. पासवर्ड\n4. कोड: `{invite}`","te":"1. క్లిక్: {link}\n2. ఫోన్\n3. పాస్‌వర్డ్\n4. కోడ్: `{invite}`"},
 "kw_bn_t": {"en":"🎁 Gift Code","hi":"🎁 गिफ्ट कोड","te":"🎁 గిఫ్ట్ కోడ్"},
 "kw_bn_b": {"en":"Today's code:\n`{code}`\n\n⏱ Valid 24 hours","hi":"आज का कोड:\n`{code}`\n\n24 घंटे","te":"ఈరోజు కోడ్:\n`{code}`\n\n24 గంటలు"},
}

def t(k, lang, **kw):
    txt = TEXTS.get(k, {}).get(lang, TEXTS.get(k, {}).get("en", ""))
    try: return txt.format(**kw) if kw else txt
    except: return txt

def lang_of(context, uid):
    l = context.user_data.get('lang')
    if not l: l = get_lang(uid); context.user_data['lang'] = l
    return l

# ═══════════════════════════════════════════
#  LANGUAGE SELECTION
# ═══════════════════════════════════════════
async def show_lang(update, context) -> int:
    kb = [[InlineKeyboardButton("🇬🇧 English", callback_data='lang_en')],
          [InlineKeyboardButton("🇮🇳 हिंदी", callback_data='lang_hi')],
          [InlineKeyboardButton("🇮🇳 తెలుగు", callback_data='lang_te')]]
    txt = "🌐 *Choose your language:*\n🌐 *अपनी भाषा चुनें:*\n🌐 *మీ భాషను ఎంచుకోండి:*"
    if update.message: await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    else:
        try: await update.callback_query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
        except: await update.callback_query.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    return CHOOSE_LANG

async def set_lang_cb(update, context) -> int:
    q = update.callback_query; await q.answer()
    lg = q.data.split('_')[1]; uid = q.from_user.id
    set_lang(uid, lg); context.user_data['lang'] = lg
    try: await q.edit_message_text(t("lang_set", lg), parse_mode='Markdown')
    except: pass
    return await show_menu(update, context)

# ═══════════════════════════════════════════
#  MAIN MENU (PREMIUM LAYOUT)
# ═══════════════════════════════════════════
def build_menu(lg, refs=0):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("b_gift", lg), callback_data='gift')],
        [InlineKeyboardButton(t("b_ref", lg), callback_data='referral')],
        [InlineKeyboardButton(t("b_pred", lg), url=PREDICTOR_BOT)],
        [InlineKeyboardButton(t("b_dep", lg), callback_data='deposit')],
        [InlineKeyboardButton(t("b_faq", lg), callback_data='faq')],
        [InlineKeyboardButton(t("b_human", lg), callback_data='human')],
        [InlineKeyboardButton(t("b_profile", lg), callback_data='profile'),
         InlineKeyboardButton(t("b_lang", lg), callback_data='changelang')],
        [InlineKeyboardButton(t("b_channel", lg), url=TELEGRAM_CHANNEL)],
    ])

async def show_menu(update, context) -> int:
    uid = update.effective_user.id if update.effective_user else update.callback_query.from_user.id
    lg = lang_of(context, uid)
    u = get_user(uid) or {}
    name = u.get('first_name', 'Player')
    refs = get_referral_count(uid)
    txt = t("welcome", lg, name=name) + f"\n\n👥 *Referrals:* `{refs}`"
    kb = build_menu(lg, refs)
    if update.message: await update.message.reply_text(txt, reply_markup=kb, parse_mode='Markdown')
    else:
        try: await update.callback_query.edit_message_text(txt, reply_markup=kb, parse_mode='Markdown')
        except: await update.callback_query.message.reply_text(txt, reply_markup=kb, parse_mode='Markdown')
    return MAIN_MENU

async def start(update, context) -> int:
    u = update.effective_user
    ref = None
    if context.args:
        try: ref = int(context.args[0])
        except: pass
    is_new = save_user(u.id, u.username, u.first_name, ref)
    context.user_data['lang'] = get_lang(u.id)
    if is_new:
        await log_to_channel(context.bot,
            f"🆕 *NEW BDG USER*\n\n👤 {u.first_name}\n📛 @{u.username or 'N/A'}\n🆔 `{u.id}`\n👥 Total: `{count_users()}`")
        return await show_lang(update, context)
    return await show_menu(update, context)

async def cmd_language(update, context) -> int:
    return await show_lang(update, context)

# ═══════════════════════════════════════════
#  COMMANDS
# ═══════════════════════════════════════════
def back_kb(lg): return InlineKeyboardMarkup([[InlineKeyboardButton(t("b_back", lg), callback_data='back')]])
def back_ch_kb(lg): return InlineKeyboardMarkup([
    [InlineKeyboardButton(t("b_channel", lg), url=TELEGRAM_CHANNEL)],
    [InlineKeyboardButton(t("b_back", lg), callback_data='back')]])

async def cmd_help(update, context):
    lg = lang_of(context, update.effective_user.id)
    txt = (
        "📖 *BDG Game Help Center*\n━━━━━━━━━━━━━━━\n"
        "🏠 /start — Main Menu\n"
        "🎁 /gift — Daily Gift Code\n"
        "🔗 /referral — Referral Link\n"
        "🎯 /predict — AI Predictor\n"
        "👤 /profile — My Stats\n"
        "❓ /faq — FAQ\n"
        "💬 /contact — Contact Admin\n"
        "🌐 /language — Change Language\n"
        "━━━━━━━━━━━━━━━\n"
        "💡 *Pro Tip:* Type keywords like *otp*, *withdraw*, *password* for instant help!"
    )
    await update.message.reply_text(txt, reply_markup=back_ch_kb(lg), parse_mode='Markdown')

async def cmd_gift(update, context):
    lg = lang_of(context, update.effective_user.id)
    txt = f"🎁 *Today's BDG Gift Code*\n\n`{TODAY_GIFT_CODE}`\n\n📋 Copy and redeem in the game's Bonus section.\n⏱ Valid 24 hours.\n\n🔗 Register: {REGISTER_LINK}"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Register on BDG", url=REGISTER_LINK)],
        [InlineKeyboardButton(t("b_channel", lg), url=TELEGRAM_CHANNEL)],
        [InlineKeyboardButton(t("b_back", lg), callback_data='back')]])
    await update.message.reply_text(txt, reply_markup=kb, parse_mode='Markdown')

async def cmd_referral(update, context):
    uid = update.effective_user.id
    lg = lang_of(context, uid)
    refs = get_referral_count(uid)
    txt = t("referral", lg, link=REGISTER_LINK, invite=INVITE_CODE, refs=refs)
    await update.message.reply_text(txt, reply_markup=back_ch_kb(lg), parse_mode='Markdown')

async def cmd_faq(update, context):
    lg = lang_of(context, update.effective_user.id)
    await update.message.reply_text(t("faq", lg, invite=INVITE_CODE), reply_markup=back_kb(lg), parse_mode='Markdown')

async def cmd_contact(update, context):
    lg = lang_of(context, update.effective_user.id)
    txt = f"💬 *Contact BDG Support*\n\n👤 Admin: {ADMIN_ID}\n📢 Channel: {TELEGRAM_CHANNEL}\n\n⏱ Response: ~30 mins"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(t("b_contact", lg), url=f"https://t.me/{ADMIN_ID.replace('@','')}")],
        [InlineKeyboardButton(t("b_channel", lg), url=TELEGRAM_CHANNEL)],
        [InlineKeyboardButton(t("b_back", lg), callback_data='back')]])
    await update.message.reply_text(txt, reply_markup=kb, parse_mode='Markdown')

async def cmd_profile(update, context):
    uid = update.effective_user.id
    lg = lang_of(context, uid)
    u = get_user(uid) or {}
    refs = get_referral_count(uid)
    joined = (u.get('joined_at','') or '')[:10]
    txt = t("profile", lg,
        id=uid, name=u.get('first_name','Player'),
        level=u.get('level',1), xp=u.get('xp',0),
        streak=u.get('streak',0), checkins=u.get('total_checkins',0),
        refs=refs, lang=lg.upper(), joined=joined)
    streak = update_checkin(uid)
    await update.message.reply_text(txt, reply_markup=back_ch_kb(lg), parse_mode='Markdown')

async def cmd_predict(update, context):
    lg = lang_of(context, update.effective_user.id)
    txt = "🎯 *AI Predictor*\n\nGet real-time number predictions from our AI bot!"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 Open Predictor", url=PREDICTOR_BOT)],
        [InlineKeyboardButton(t("b_back", lg), callback_data='back')]])
    await update.message.reply_text(txt, reply_markup=kb, parse_mode='Markdown')

# ═══════════════════════════════════════════
#  ADMIN
# ═══════════════════════════════════════════
async def cmd_broadcast(update, context):
    if update.effective_user.id != ADMIN_NUMERIC_ID: return ConversationHandler.END
    await update.message.reply_text(f"📢 Broadcast Mode\n👥 Total: `{count_users()}`\n\nSend message. /cancel to abort.", parse_mode='Markdown')
    return BROADCAST_MSG

async def do_broadcast(update, context):
    if update.effective_user.id != ADMIN_NUMERIC_ID: return ConversationHandler.END
    m = update.message; uids = get_all_user_ids(); total = len(uids)
    if not total: await m.reply_text("❌ No users."); return ConversationHandler.END
    st = await m.reply_text(f"📡 Sending to {total}...")
    ok = fail = 0
    for uid in uids:
        try:
            await context.bot.copy_message(chat_id=uid, from_chat_id=m.chat_id, message_id=m.message_id)
            ok += 1; await asyncio.sleep(0.05)
        except: fail += 1
    await st.edit_text(f"✅ *Broadcast Done!*\n📤 Sent: `{ok}`\n❌ Failed: `{fail}`", parse_mode='Markdown')
    return ConversationHandler.END

async def cmd_stats(update, context):
    if update.effective_user.id != ADMIN_NUMERIC_ID: return
    txt = (f"📊 *Bot Statistics*\n━━━━━━━━━━━━━━━\n"
           f"👥 Users: `{count_users()}`\n"
           f"🎁 Gift Code: `{TODAY_GIFT_CODE}`\n"
           f"🔑 Invite Code: `{INVITE_CODE}`\n"
           f"💾 DB: Supabase\n🌍 Langs: EN / HI / TE\n"
           f"⚡ Status: Online 24/7")
    await update.message.reply_text(txt, parse_mode='Markdown')

# ═══════════════════════════════════════════
#  FLOWS
# ═══════════════════════════════════════════
async def f_gift(update, context) -> int:
    q = update.callback_query; await q.answer()
    lg = lang_of(context, q.from_user.id)
    await q.edit_message_text(t("gift_prompt", lg), parse_mode='Markdown')
    return ASK_GAME_ID

async def f_game_id(update, context) -> int:
    d = "Screenshot" if update.message.photo else update.message.text
    context.user_data['gid'] = d
    lg = lang_of(context, update.effective_user.id)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(t("b_yes_reg", lg), callback_data='team_yes')],
        [InlineKeyboardButton(t("b_no_new", lg), callback_data='team_no')],
        [InlineKeyboardButton(t("b_back", lg), callback_data='back')]])
    await update.message.reply_text(t("gift_received", lg, data=d), reply_markup=kb, parse_mode='Markdown')
    return ASK_TEAM_STATUS

async def f_team(update, context) -> int:
    q = update.callback_query; await q.answer()
    u = q.from_user; lg = lang_of(context, u.id); gid = context.user_data.get('gid', '?')
    if q.data == 'team_yes':
        txt = t("gift_verified", lg, admin=ADMIN_ID, id=gid)
        await log_to_channel(context.bot, f"✅ BDG Gift Claim\n👤 {u.first_name}\n🆔 `{gid}`")
    else:
        txt = t("gift_not_reg", lg, link=REGISTER_LINK, invite=INVITE_CODE)
        await log_to_channel(context.bot, f"❌ Unregistered\n👤 {u.first_name}")
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(t("b_channel", lg), url=TELEGRAM_CHANNEL)],
        [InlineKeyboardButton(t("b_back", lg), callback_data='back')]])
    await q.edit_message_text(txt, reply_markup=kb, parse_mode='Markdown')
    return ConversationHandler.END

async def f_dep(update, context) -> int:
    q = update.callback_query; await q.answer()
    lg = lang_of(context, q.from_user.id)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(t("b_dep_iss", lg), callback_data='dep_issue')],
        [InlineKeyboardButton(t("b_wd_iss", lg), callback_data='with_issue')],
        [InlineKeyboardButton(t("b_back", lg), callback_data='back')]])
    await q.edit_message_text(t("dep_menu", lg), reply_markup=kb, parse_mode='Markdown')
    return DEPOSIT_MENU

async def f_dep_choice(update, context) -> int:
    q = update.callback_query; await q.answer()
    lg = lang_of(context, q.from_user.id)
    txt = t("dep_help", lg) if q.data == 'dep_issue' else t("wd_help", lg)
    st = DEPOSIT_HELP if q.data == 'dep_issue' else WITHDRAW_HELP
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(t("b_solved", lg), callback_data='solved')],
        [InlineKeyboardButton(t("b_need_h", lg), callback_data='need_human')],
        [InlineKeyboardButton(t("b_back", lg), callback_data='back')]])
    await q.edit_message_text(txt, reply_markup=kb, parse_mode='Markdown')
    return st

async def f_resolve(update, context) -> int:
    q = update.callback_query; await q.answer()
    lg = lang_of(context, q.from_user.id)
    if q.data == 'solved': txt = t("solved", lg)
    else:
        txt = t("human_req", lg, admin=ADMIN_ID)
        await log_to_channel(context.bot, f"🆘 ESCALATED\n👤 {q.from_user.first_name}")
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(t("b_contact", lg), url=f"https://t.me/{ADMIN_ID.replace('@','')}")],
        [InlineKeyboardButton(t("b_channel", lg), url=TELEGRAM_CHANNEL)],
        [InlineKeyboardButton(t("b_back", lg), callback_data='back')]])
    await q.edit_message_text(txt, reply_markup=kb, parse_mode='Markdown')
    return ConversationHandler.END

async def f_human(update, context) -> int:
    q = update.callback_query; await q.answer()
    lg = lang_of(context, q.from_user.id)
    await q.edit_message_text(t("human_prompt", lg), parse_mode='Markdown')
    return HUMAN_AGENT

async def f_human_recv(update, context) -> int:
    d = "Screenshot" if update.message.photo else update.message.text
    u = update.effective_user; lg = lang_of(context, u.id)
    txt = t("human_received", lg, data=d, admin=ADMIN_ID)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(t("b_contact", lg), url=f"https://t.me/{ADMIN_ID.replace('@','')}")],
        [InlineKeyboardButton(t("b_channel", lg), url=TELEGRAM_CHANNEL)],
        [InlineKeyboardButton(t("b_back", lg), callback_data='back')]])
    await update.message.reply_text(txt, reply_markup=kb, parse_mode='Markdown')
    await log_to_channel(context.bot, f"💬 HUMAN REQUEST\n👤 {u.first_name}\n📝 {d}")
    return ConversationHandler.END

# ═══════════════════════════════════════════
#  BUTTONS
# ═══════════════════════════════════════════
async def on_btn(update, context) -> int:
    q = update.callback_query; await q.answer()
    uid = q.from_user.id; lg = lang_of(context, uid); d = q.data
    if d == 'changelang': return await show_lang(update, context)
    if d == 'referral':
        refs = get_referral_count(uid)
        txt = t("referral", lg, link=REGISTER_LINK, invite=INVITE_CODE, refs=refs)
        await q.edit_message_text(txt, reply_markup=back_ch_kb(lg), parse_mode='Markdown'); return MAIN_MENU
    if d == 'faq':
        await q.edit_message_text(t("faq", lg, invite=INVITE_CODE), reply_markup=back_kb(lg), parse_mode='Markdown'); return MAIN_MENU
    if d == 'profile':
        u = get_user(uid) or {}; refs = get_referral_count(uid)
        joined = (u.get('joined_at','') or '')[:10]
        update_checkin(uid)
        txt = t("profile", lg, id=uid, name=u.get('first_name','Player'),
                level=u.get('level',1), xp=u.get('xp',0), streak=u.get('streak',0),
                checkins=u.get('total_checkins',0), refs=refs, lang=lg.upper(), joined=joined)
        await q.edit_message_text(txt, reply_markup=back_ch_kb(lg), parse_mode='Markdown'); return MAIN_MENU
    if d == 'back': return await show_menu(update, context)
    return MAIN_MENU

# ═══════════════════════════════════════════
#  KEYWORDS
# ═══════════════════════════════════════════
async def on_kw(update, context):
    if not update.message or not update.message.text: return
    txt_in = update.message.text.lower()
    u = update.effective_user; lg = lang_of(context, u.id)
    save_user(u.id, u.username, u.first_name)
    if "otp" in txt_in: body = t("kw_otp_b", lg, admin=ADMIN_ID); title = t("kw_otp_t", lg)
    elif "password" in txt_in: body = t("kw_pwd_b", lg); title = t("kw_pwd_t", lg)
    elif "withdraw" in txt_in: body = t("kw_wd_b", lg); title = t("kw_wd_t", lg)
    elif "deposit" in txt_in: body = t("kw_dep_b", lg); title = t("kw_dep_t", lg)
    elif "login" in txt_in: body = t("kw_lg_b", lg); title = t("kw_lg_t", lg)
    elif "register" in txt_in: body = t("kw_rg_b", lg, link=REGISTER_LINK, invite=INVITE_CODE); title = t("kw_rg_t", lg)
    elif "bonus" in txt_in or "gift" in txt_in: body = t("kw_bn_b", lg, code=TODAY_GIFT_CODE); title = t("kw_bn_t", lg)
    else:
        await update.message.reply_text(t("kw_unknown", lg), reply_markup=back_kb(lg), parse_mode='Markdown'); return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(t("b_contact", lg), url=f"https://t.me/{ADMIN_ID.replace('@','')}")],
        [InlineKeyboardButton(t("b_channel", lg), url=TELEGRAM_CHANNEL)],
        [InlineKeyboardButton(t("b_back", lg), callback_data='back')]])
    await update.message.reply_text(f"*{title}*\n\n{body}", reply_markup=kb, parse_mode='Markdown')

async def cancel_cmd(update, context) -> int:
    await show_menu(update, context); return MAIN_MENU

# ═══════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════
if __name__ == '__main__':
    threading.Thread(target=run_web_server, daemon=True).start()
    bot = ApplicationBuilder().token(TOKEN).build()

    bcast = ConversationHandler(
        entry_points=[CommandHandler('broadcast', cmd_broadcast)],
        states={BROADCAST_MSG: [MessageHandler(filters.ALL & ~filters.COMMAND, do_broadcast)]},
        fallbacks=[CommandHandler('cancel', cancel_cmd)])

    main_conv = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CommandHandler('language', cmd_language),
            CallbackQueryHandler(f_gift, pattern='^gift$'),
            CallbackQueryHandler(f_dep, pattern='^deposit$'),
            CallbackQueryHandler(f_human, pattern='^human$'),
            CallbackQueryHandler(set_lang_cb, pattern='^lang_(en|hi|te)$'),
        ],
        states={
            CHOOSE_LANG: [CallbackQueryHandler(set_lang_cb, pattern='^lang_(en|hi|te)$')],
            MAIN_MENU: [CallbackQueryHandler(on_btn), CallbackQueryHandler(f_gift, pattern='^gift$'),
                        CallbackQueryHandler(f_dep, pattern='^deposit$'), CallbackQueryHandler(f_human, pattern='^human$')],
            ASK_GAME_ID: [MessageHandler(filters.TEXT | filters.PHOTO, f_game_id), CallbackQueryHandler(on_btn)],
            ASK_TEAM_STATUS: [CallbackQueryHandler(f_team, pattern='^(team_yes|team_no)$')],
            DEPOSIT_MENU: [CallbackQueryHandler(f_dep_choice, pattern='^(dep_issue|with_issue)$')],
            DEPOSIT_HELP: [CallbackQueryHandler(f_resolve, pattern='^(solved|need_human)$')],
            WITHDRAW_HELP: [CallbackQueryHandler(f_resolve, pattern='^(solved|need_human)$')],
            HUMAN_AGENT: [MessageHandler(filters.TEXT | filters.PHOTO, f_human_recv)],
        },
        fallbacks=[
            CommandHandler('start', start),
            CommandHandler('language', cmd_language),
            CallbackQueryHandler(on_btn)])

    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("language", cmd_language))
    bot.add_handler(CommandHandler("help", cmd_help))
    bot.add_handler(CommandHandler("gift", cmd_gift))
    bot.add_handler(CommandHandler("referral", cmd_referral))
    bot.add_handler(CommandHandler("predict", cmd_predict))
    bot.add_handler(CommandHandler("profile", cmd_profile))
    bot.add_handler(CommandHandler("faq", cmd_faq))
    bot.add_handler(CommandHandler("contact", cmd_contact))
    bot.add_handler(CommandHandler("stats", cmd_stats))
    bot.add_handler(bcast)
    bot.add_handler(main_conv)
    bot.add_handler(CallbackQueryHandler(on_btn))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_kw))

    print("🚀 BDG Game Premium Bot running 24/7...")
    bot.run_polling()
