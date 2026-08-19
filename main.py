import json
import os
import subprocess
import threading
import time
import telebot
from telebot import types

TOKEN = "8724320555:AAGQnxw2OaBnXV2-b_MNKm41Ypk4j_bYPH8"
INITIAL_ADMIN_ID = "8173349543"  # آیدی عددی مالک اصلی ربات (ریس شاهد)

bot = telebot.TeleBot(TOKEN)

DATA_FILE = "users_data.json"
ADMINS_FILE = "admins.json"
CHANNELS_FILE = "channels.json"
USER_BOTS_DIR = "user_bots"
os.makedirs(USER_BOTS_DIR, exist_ok=True)

# ذخیره پردازش ربات‌های کاربران برای امکان متوقف کردن آن‌ها
active_user_processes = {}

# سیستم ترجمه دو زبانه (دری و انگلیسی)
TRANSLATIONS = {
    "dr": {
        "choose_lang": "لطفاً زبان خود را انتخاب کنید:\n请选择您的语言 / Please choose your language:",
        "welcome_menu": (
            "🌟 به پیشرفته‌ترین ربات‌ساز تلگرامی خوش آمدید ✨\n\n"
            "🛠 لطفاً از منوی زیر برای مدیریت ربات خود استفاده کنید: 👇"
        ),
        "profile": (
            "👤 **پروفایل کاربری:**\n\n"
            "⚡ نام: {name}\n"
            "📊 وضعیت ربات: {bot_status}\n"
            "🟢 امتیاز فعلی شما: `{score}`\n"
            "🆔 آیدی عددی شما: `{uid}`\n"
            "🌐 لینک اختصاصی دعوت شما:\n`{link}`"
        ),
        "ref_bonus": "🎉 یک کاربر جدید با لینک دعوت شما به ربات پیوست! امتیاز به حساب شما اضافه شد.",
        "support_prompt": "✍️ لطفاً پیام، سؤال یا مشکل خود را ارسال کنید تا مستقیماً به تیم پشتیبانی و مدیریت برسد:",
        "support_sent": "✅ پیام شما با موفقیت به پشتیبانی ارسال شد. به زودی پاسخ داده خواهد شد.",
        "join_lock": (
            "📢 **توجه مهم!**\n\n"
            "برای استفاده از امکانات ربات، لطفاً ابتدا در کانال‌های زیر عضو شوید:\n\n"
            "پس از عضویت، روی دکمه «عضو شدم ✅» کلیک کنید."
        ),
        "btn_check_join": "عضو شدم ✅ بررسی اشتراک",
        "not_joined_alert": "❌ شما هنوز در تمام کانال‌ها عضو نشده‌اید! لطفاً عضویت خود را تکمیل کنید.",
        "btn_online": "🛠 آنلاین کردن ربات",
        "btn_delete": "❌ حذف ربات",
        "btn_transfer": "🔄 انتقال امتیاز",
        "btn_buy": "🛒 خرید امتیاز",
        "btn_info": "✔ اطلاعات من",
        "btn_support": "✔ پشتیبانی و ارتباط",
    },
    "en": {
        "choose_lang": "Please choose your language:",
        "welcome_menu": (
            "🌟 Welcome to the most advanced Bot Builder ✨\n\n"
            "🛠 Please use the menu below to manage your bot: 👇"
        ),
        "profile": (
            "👤 **User Profile:**\n\n"
            "⚡ Name: {name}\n"
            "📊 Bot Status: {bot_status}\n"
            "🟢 Current Score: `{score}`\n"
            "🆔 Your User ID: `{uid}`\n"
            "🌐 Your Special Invite Link:\n`{link}`"
        ),
        "ref_bonus": "🎉 A new user joined via your referral link! Score added to your account.",
        "support_prompt": "✍️ Please send your message, question, or issue to reach the support team:",
        "support_sent": "✅ Your message has been successfully sent to support. We will reply soon.",
        "join_lock": (
            "📢 **Important Notice!**\n\n"
            "To use our bot, please join our official channels first:\n\n"
            "After joining, click the 'Joined ✅' button."
        ),
        "btn_check_join": "Joined ✅ Check Status",
        "not_joined_alert": "❌ You have not joined all required channels yet!",
        "btn_online": "🛠 Online Bot",
        "btn_delete": "❌ Delete Bot",
        "btn_transfer": "🔄 Transfer Score",
        "btn_buy": "🛒 Buy Score",
        "btn_info": "✔ My Info",
        "btn_support": "✔ Support & Contact",
    }
}


def load_data():
  if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
      return json.load(f)
  return {}


def save_data(data):
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


def load_admins():
  admins = [str(INITIAL_ADMIN_ID)]
  if os.path.exists(ADMINS_FILE):
    try:
      with open(ADMINS_FILE, "r", encoding="utf-8") as f:
        loaded = json.load(f)
        for aid in loaded:
          if str(aid) not in admins:
            admins.append(str(aid))
    except Exception as e:
      print(f"Error loading admins: {e}")
  return admins


def save_admins(admins):
  unique_admins = list(set([str(INITIAL_ADMIN_ID)] + [str(a) for a in admins]))
  with open(ADMINS_FILE, "w", encoding="utf-8") as f:
    json.dump(unique_admins, f, ensure_ascii=False, indent=4)


def is_admin(user_id):
  admins = load_admins()
  return str(user_id) in admins


def load_channels():
  if os.path.exists(CHANNELS_FILE):
    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
      return json.load(f)
  default_channels = [
      {"name": "@hackwhatandetc", "url": "https://t.me/hackwhatandetc", "id": "@hackwhatandetc"},
      {"name": "@hackwhatandetcb", "url": "https://t.me/hackwhatandetcb", "id": "@hackwhatandetcb"}
  ]
  save_channels(default_channels)
  return default_channels


def save_channels(channels):
  with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
    json.dump(channels, f, ensure_ascii=False, indent=4)


def check_user_membership(user_id):
  channels = load_channels()
  if not channels:
    return True
  for ch in channels:
    ch_id = ch["id"]
    try:
      member = bot.get_chat_member(ch_id, int(user_id))
      if member.status not in ["member", "administrator", "creator"]:
        return False
    except Exception as e:
      print(f"Error checking membership for {ch_id}: {e}")
      return False
  return True


def get_main_menu(lang="dr"):
  t = TRANSLATIONS.get(lang, TRANSLATIONS["dr"])
  markup = types.InlineKeyboardMarkup(row_width=2)
  markup.add(
      types.InlineKeyboardButton(t["btn_online"], callback_data="online_bot_menu"),
      types.InlineKeyboardButton(t["btn_delete"], callback_data="delete_bot_menu"),
      types.InlineKeyboardButton(t["btn_transfer"], callback_data="transfer_score_menu"),
      types.InlineKeyboardButton(t["btn_buy"], callback_data="buy_score_menu"),
      types.InlineKeyboardButton(t["btn_info"], callback_data="my_info"),
      types.InlineKeyboardButton(t["btn_support"], callback_data="support_btn")
  )
  return markup


def send_main_menu(chat_id, lang="dr"):
  t = TRANSLATIONS.get(lang, TRANSLATIONS["dr"])
  bot.send_message(chat_id, t["welcome_menu"], reply_markup=get_main_menu(lang), parse_mode="Markdown")


# ترد بررسی‌کننده زمان انقضای ربات‌ها (خاموش‌سازی خودکار چندگانه)
def background_expiration_checker():
  while True:
    try:
      data = load_data()
      current_time = time.time()
      updated = False

      for uid, user_info in list(data.items()):
        bots_dict = user_info.get("bots", {})
        if bots_dict:
          for b_unique_id, b_data in list(bots_dict.items()):
            expire_time = b_data.get("expire_time")
            if expire_time and current_time >= expire_time:
              path = os.path.join(USER_BOTS_DIR, f"{b_unique_id}_bot.py")
              
              if b_unique_id in active_user_processes:
                try:
                  active_user_processes[b_unique_id].terminate()
                  del active_user_processes[b_unique_id]
                except Exception as e:
                  print(f"Error terminating expired process for {b_unique_id}: {e}")

              if os.path.exists(path):
                try:
                  os.remove(path)
                except Exception as e:
                  print(f"Error removing expired file for {b_unique_id}: {e}")

              del bots_dict[b_unique_id]
              updated = True

              lang = user_info.get("lang", "dr")
              b_name = b_data.get("file_name", "ربات")
              expired_msg = (
                  f"⏳ **مدت زمان فعال‌سازی ربات ({b_name}) به پایان رسید و ربات خاموش شد.**\n\n"
                  "برای روشن کردن مجدد آن، لطفاً از منوی «آنلاین کردن ربات» اقدام فرمایید."
              ) if lang != "en" else (
                  f"⏳ **Your bot's ({b_name}) active duration has expired and it has been stopped.**"
              )
              try:
                bot.send_message(int(uid), expired_msg, parse_mode="Markdown")
              except:
                pass

      if updated:
        save_data(data)
    except Exception as e:
      print(f"Error in expiration checker thread: {e}")
    
    time.sleep(60)


@bot.message_handler(commands=["start"])
def start(message):
  uid = str(message.from_user.id)
  data = load_data()
  args = message.text.split()

  is_new_user = uid not in data

  if is_new_user:
    data[uid] = {"score": 0, "lang": None, "bots": {}}
    if len(args) > 1:
      referrer_id = args[1]
      if referrer_id in data and referrer_id != uid:
        data[referrer_id]["score"] += 5
        ref_lang = data[referrer_id].get("lang", "dr")
        try:
          bot.send_message(int(referrer_id), TRANSLATIONS[ref_lang]["ref_bonus"])
        except:
          pass
    save_data(data)

    try:
      admins = load_admins()
      user_name = message.from_user.first_name or "بدون نام"
      username = f"@{message.from_user.username}" if message.from_user.username else "ندارد"
      
      admin_text = (
          f"👤 **کاربر جدید ربات را استارت زد:**\n\n"
          f"⚡ نام: {user_name}\n"
          f"🔗 یوزرنیم: {username}"
      )

      photos = bot.get_user_profile_photos(message.from_user.id, limit=1)
      for admin_id in admins:
        try:
          if photos.total_count > 0:
            file_id = photos.photos[0][0].file_id
            bot.send_photo(int(admin_id), file_id, caption=admin_text, parse_mode="Markdown")
          else:
            bot.send_message(int(admin_id), admin_text, parse_mode="Markdown")
        except Exception:
          pass
    except Exception as e:
      print(f"Error sending new user info to admin: {e}")

  if data[uid].get("lang") is None:
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("دری 🇦🇫", callback_data="lang_dr"),
        types.InlineKeyboardButton("English 🇬🇧", callback_data="lang_en")
    )
    bot.send_message(message.chat.id, TRANSLATIONS["dr"]["choose_lang"], reply_markup=markup)
    return

  lang = data[uid]["lang"]

  if not check_user_membership(uid):
    channels = load_channels()
    markup = types.InlineKeyboardMarkup(row_width=1)
    for ch in channels:
      markup.add(types.InlineKeyboardButton(ch["name"], url=ch["url"]))
    markup.add(types.InlineKeyboardButton(TRANSLATIONS[lang]["btn_check_join"], callback_data="check_join"))
    
    bot.send_message(message.chat.id, TRANSLATIONS[lang]["join_lock"], reply_markup=markup, parse_mode="Markdown")
    return

  send_main_menu(message.chat.id, lang)


@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def set_language_callback(call):
  uid = str(call.from_user.id)
  selected_lang = call.data.split("_")[1]
  
  data = load_data()
  is_new_user = uid not in data
  if is_new_user:
    data[uid] = {"score": 0, "bots": {}}
  data[uid]["lang"] = selected_lang
  save_data(data)

  bot.answer_callback_query(call.id, "✅ Language saved!" if selected_lang == "en" else "✅ زبان ذخیره شد!")
  try:
    bot.delete_message(call.message.chat.id, call.message.message_id)
  except:
    pass

  if not check_user_membership(uid):
    channels = load_channels()
    markup = types.InlineKeyboardMarkup(row_width=1)
    for ch in channels:
      markup.add(types.InlineKeyboardButton(ch["name"], url=ch["url"]))
    markup.add(types.InlineKeyboardButton(TRANSLATIONS[selected_lang]["btn_check_join"], callback_data="check_join"))
    
    bot.send_message(call.message.chat.id, TRANSLATIONS[selected_lang]["join_lock"], reply_markup=markup, parse_mode="Markdown")
    return

  send_main_menu(call.message.chat.id, selected_lang)


@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join_callback(call):
  uid = str(call.from_user.id)
  data = load_data()
  lang = data.get(uid, {}).get("lang", "dr")

  if check_user_membership(uid):
    bot.answer_callback_query(call.id, "✅ Approved!" if lang == "en" else "✅ عضویت شما تایید شد!")
    try:
      bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
      pass
    send_main_menu(call.message.chat.id, lang)
  else:
    bot.answer_callback_query(call.id, TRANSLATIONS[lang]["not_joined_alert"], show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data == "my_info")
def my_info_callback(call):
  uid = str(call.from_user.id)
  data = load_data()
  lang = data.get(uid, {}).get("lang", "dr")
  
  if not check_user_membership(uid):
    bot.answer_callback_query(call.id, "❌ Join channels first!" if lang == "en" else "❌ ابتدا باید در کانال‌ها عضو شوید!", show_alert=True)
    return

  if uid not in data:
    data[uid] = {"score": 0, "lang": lang, "bots": {}}
    save_data(data)

  user = call.from_user
  ref_link = f"https://t.me/Robat_online_bot?start={uid}"
  
  user_bots = data.get(uid, {}).get("bots", {})
  if user_bots:
    bot_status = f"🟢 روشن و فعال ({len(user_bots)} ربات روی سرور)" if lang != "en" else f"🟢 Running ({len(user_bots)} bots on server)"
  else:
    bot_status = "🔴 غیرفعال (بدون ربات)" if lang != "en" else "🔴 Inactive (No Bot)"

  text = TRANSLATIONS[lang]["profile"].format(
      name=user.first_name,
      bot_status=bot_status,
      score=data[uid]["score"],
      uid=uid,
      link=ref_link,
  )
  bot.answer_callback_query(call.id)
  bot.send_message(call.message.chat.id, text, reply_markup=get_main_menu(lang), parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "transfer_score_menu")
def transfer_score_callback(call):
  uid = str(call.from_user.id)
  data = load_data()
  lang = data.get(uid, {}).get("lang", "dr")
  
  if not check_user_membership(uid):
    bot.answer_callback_query(call.id, "❌ Join channels first!" if lang == "en" else "❌ ابتدا باید در کانال‌ها عضو شوید!", show_alert=True)
    return

  bot.answer_callback_query(call.id)
  msg = bot.send_message(
      call.message.chat.id,
      "📤 لطفاً آیدی عددی کاربر مقصد و مقدار امتیازی که می‌خواهید انتقال دهید را با فاصله ارسال کنید:\n\nمثال:\n`123456789 20`\n\n*(توجه: ۵ امتیاز کارمزد از حساب شما کسر می‌گردد)*"
      if lang != "en" else
      "📤 Please send target user ID and amount separated by space:\n\nExample:\n`123456789 20`\n\n*(Note: 5 score fee will be deducted)*",
      parse_mode="Markdown"
  )
  bot.register_next_step_handler(msg, process_score_transfer)


def process_score_transfer(message):
  sender_uid = str(message.from_user.id)
  data = load_data()

  if message.text and message.text.startswith("/"):
    return

  try:
    parts = message.text.strip().split()
    if len(parts) < 2:
      bot.reply_to(message, "❌ فرمت اشتباه است. لطفاً طبق مثال ارسال کنید.")
      return

    target_uid = parts[0]
    amount = int(parts[1])

    if amount <= 0:
      bot.reply_to(message, "❌ مقدار امتیاز باید بیشتر از صفر باشد.")
      return

    if target_uid == sender_uid:
      bot.reply_to(message, "❌ شما نمی‌توانید به خودتان امتیاز انتقال دهید.")
      return

    if target_uid not in data:
      bot.reply_to(message, "❌ کاربر مقصد در ربات ثبت‌نام نکرده است.")
      return

    total_needed = amount + 5
    sender_score = data[sender_uid].get("score", 0)

    if sender_score < total_needed:
      bot.reply_to(message, f"❌ موجودی شما کافی نیست! شما به {total_needed} امتیاز نیاز دارید (شامل ۵ امتیاز کارمزد)، اما امتیاز فعلی شما {sender_score} است.")
      return

    data[sender_uid]["score"] -= total_needed
    data[target_uid]["score"] += amount
    save_data(data)

    bot.reply_to(message, f"✅ انتقال با موفقیت انجام شد!\n📉 مقدار {amount} امتیاز به کاربر ارسال شد.\n⚙️ ۵ امتیاز بابت کارمزد کسر گردید.\n🟢 موجودی جدید شما: {data[sender_uid]['score']}")
    
    try:
      bot.send_message(int(target_uid), f"🎉 کاربر گرامی، مقدار {amount} امتیاز از طرف یک کاربر به حساب شما واریز شد!")
    except:
      pass

  except ValueError:
    bot.reply_to(message, "❌ مقدار امتیاز را فقط به صورت عدد وارد کنید.")
  except Exception as e:
    bot.reply_to(message, f"❌ خطا در پردازش انتقال: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "buy_score_menu")
def buy_score_menu_callback(call):
  uid = str(call.from_user.id)
  data = load_data()
  lang = data.get(uid, {}).get("lang", "dr")
  
  if not check_user_membership(uid):
    bot.answer_callback_query(call.id, "❌ Join channels first!" if lang == "en" else "❌ ابتدا باید در کانال‌ها عضو شوید!", show_alert=True)
    return

  bot.answer_callback_query(call.id)
  text = (
      "🛒 **راهنمای خرید امتیاز:**\n\n"
      "برای خرید امتیاز و ارتقای حساب کاربری خود، می‌توانید بسته‌های زیر را تهیه کنید:\n"
      "🔹 ۵۰ امتیاز - ۱۰۰ افغانی\n"
      "🔹 ۱۰۰ امتیاز - ۲۰۰ افغانی\n\n"
      "📩 برای نهایی کردن خرید و ارسال رسید پرداختی، لطفاً از طریق دکمه «پشتیبانی و ارتباط» در منوی اصلی به مدیریت پیام دهید."
  ) if lang != "en" else (
      "🛒 **Score Purchase Guide:**\n\n"
      "To purchase score, please contact support via the main menu."
  )
  bot.send_message(call.message.chat.id, text, reply_markup=get_main_menu(lang), parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "online_bot_menu")
def online_bot_callback(call):
  uid = str(call.from_user.id)
  data = load_data()
  lang = data.get(uid, {}).get("lang", "dr")
  
  if not check_user_membership(uid):
    bot.answer_callback_query(call.id, "❌ Join channels first!" if lang == "en" else "❌ ابتدا باید در کانال‌ها عضو شوید!", show_alert=True)
    return

  bot.answer_callback_query(call.id)
  
  markup = types.InlineKeyboardMarkup(row_width=1)
  markup.add(
      types.InlineKeyboardButton("⏱ ۲۴ ساعت (۵۰ امتیاز)", callback_data="plan_24h"),
      types.InlineKeyboardButton("📅 ۷ روز (۳۵۰ امتیاز)", callback_data="plan_7d"),
      types.InlineKeyboardButton("🗓 ۲ هفته (۷۰۰ امتیاز)", callback_data="plan_14d"),
      types.InlineKeyboardButton("ماهانه (۱۵۰۰ امتیاز)", callback_data="plan_30d"),
      types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")
  )
  
  text = (
      "⏳ **انتخاب مدت زمان آنلاین ماندن ربات:**\n\n"
      "لطفاً مدت‌زمانی که می‌خواهید ربات شما روی سرور فعال بماند را انتخاب کنید:"
  ) if lang != "en" else (
      "⏳ **Select Bot Online Duration:**\n\n"
      "Please choose how long you want your bot to stay online:"
  )
  bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data.startswith("plan_"))
def select_plan_callback(call):
  uid = str(call.from_user.id)
  data = load_data()
  lang = data.get(uid, {}).get("lang", "dr")
  
  plan = call.data
  duration_map = {
      "plan_24h": 24 * 3600,
      "plan_7d": 7 * 24 * 3600,
      "plan_14d": 14 * 24 * 3600,
      "plan_30d": 30 * 24 * 3600
  }
  
  cost_map = {
      "plan_24h": 50,
      "plan_7d": 350,
      "plan_14d": 700,
      "plan_30d": 1500
  }
  
  cost = cost_map.get(plan, 50)
  duration = duration_map.get(plan, 24 * 3600)
  score = data.get(uid, {}).get("score", 0)

  if score < cost:
    msg_text = f"❌ Not enough score! Need {cost} score." if lang == "en" else f"❌ امتیاز شما کافی نیست!\nبرای این مدت زمان {cost} امتیاز نیاز دارید اما امتیاز فعلی شما {score} است."
    bot.answer_callback_query(call.id, "❌ امتیاز کافی نیست!", show_alert=True)
    bot.send_message(call.message.chat.id, msg_text)
    return

  bot.answer_callback_query(call.id)
  
  if uid not in data:
    data[uid] = {"score": score, "lang": lang, "bots": {}}
  
  data[uid]["pending_cost"] = cost
  data[uid]["pending_duration"] = duration
  save_data(data)

  prompt_text = f"📂 لطفا فایل سورس ربات خود (با فرمت `.py`) را ارسال کنید:\n*(هزینه این پکیج: {cost} امتیاز)*" if lang != "en" else f"📂 Please send your bot file (`.py`):\n*(Cost: {cost} score)*"
  msg = bot.send_message(call.message.chat.id, prompt_text, parse_mode="Markdown")
  bot.register_next_step_handler(msg, handle_docs_from_step)


@bot.callback_query_handler(func=lambda call: call.data == "back_to_menu")
def back_to_menu_callback(call):
  uid = str(call.from_user.id)
  data = load_data()
  lang = data.get(uid, {}).get("lang", "dr")
  bot.answer_callback_query(call.id)
  try:
    bot.delete_message(call.message.chat.id, call.message.message_id)
  except:
    pass
  send_main_menu(call.message.chat.id, lang)


@bot.callback_query_handler(func=lambda call: call.data == "delete_bot_menu")
def delete_bot_callback(call):
  uid = str(call.from_user.id)
  data = load_data()
  lang = data.get(uid, {}).get("lang", "dr")
  bot.answer_callback_query(call.id)
  
  user_bots = data.get(uid, {}).get("bots", {})
  
  # سازگاری با ساختار قبلی داده‌ها اگر وجود داشته باشد
  if not user_bots:
    legacy_files = [f for f in os.listdir(USER_BOTS_DIR) if f.startswith(f"{uid}_") and f.endswith(".py")]
    if legacy_files:
      user_bots = {}
      for lf in legacy_files:
        b_id = lf.replace("_bot.py", "")
        user_bots[b_id] = {"file_name": b_id.replace(f"{uid}_", "")}

  if not user_bots:
    msg_text = "❌ شما هیچ ربات فعالی روی سرور ندارید." if lang != "en" else "❌ You have no active bots."
    bot.send_message(call.message.chat.id, msg_text, reply_markup=get_main_menu(lang))
    return

  markup = types.InlineKeyboardMarkup(row_width=1)
  
  for b_unique_id, b_info in user_bots.items():
    b_name = b_info.get("file_name", b_unique_id)
    markup.add(types.InlineKeyboardButton(f"🤖 ربات: {b_name} (حذف و توقف)", callback_data=f"confirm_del_bot_{b_unique_id}"))
    
  markup.add(types.InlineKeyboardButton("🔙 انصراف", callback_data="cancel_delete"))

  text = (
      "🗑️ **مدیریت و حذف ربات:**\n\n"
      "لیست ربات‌های فعال شما روی سرور:\n"
      "👇 برای حذف و توقف هر کدام روی آن کلیک کنید:"
  )
  bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_del_bot_"))
def confirm_delete_bot_callback(call):
  uid = str(call.from_user.id)
  target_bot_unique_id = call.data.replace("confirm_del_bot_", "")
  data = load_data()
  lang = data.get(uid, {}).get("lang", "dr")
  bot.answer_callback_query(call.id)
  
  path = os.path.join(USER_BOTS_DIR, f"{target_bot_unique_id}_bot.py")

  if target_bot_unique_id in active_user_processes:
    try:
      active_user_processes[target_bot_unique_id].terminate()
      del active_user_processes[target_bot_unique_id]
    except:
      pass

  if os.path.exists(path):
    try:
      os.remove(path)
    except:
      pass

  if uid in data and "bots" in data[uid]:
    if target_bot_unique_id in data[uid]["bots"]:
      del data[uid]["bots"][target_bot_unique_id]
      save_data(data)

  msg_text = "🗑️ ربات مورد نظر با موفقیت از سرور پاک شد و متوقف گردید."
  bot.edit_message_text(msg_text, call.message.chat.id, call.message.message_id)
  bot.send_message(call.message.chat.id, "منوی اصلی:", reply_markup=get_main_menu(lang))


@bot.callback_query_handler(func=lambda call: call.data == "cancel_delete")
def cancel_delete_callback(call):
  uid = str(call.from_user.id)
  data = load_data()
  lang = data.get(uid, {}).get("lang", "dr")
  bot.answer_callback_query(call.id)
  try:
    bot.delete_message(call.message.chat.id, call.message.message_id)
  except:
    pass
  send_main_menu(call.message.chat.id, lang)


@bot.callback_query_handler(func=lambda call: call.data == "support_btn")
def support_callback(call):
  uid = str(call.from_user.id)
  data = load_data()
  lang = data.get(uid, {}).get("lang", "dr")

  if not check_user_membership(uid):
    bot.answer_callback_query(call.id, "❌ Join channels first!" if lang == "en" else "❌ ابتدا باید در کانال‌ها عضو شوید!", show_alert=True)
    return

  bot.answer_callback_query(call.id)
  msg = bot.send_message(call.message.chat.id, TRANSLATIONS[lang]["support_prompt"])
  bot.register_next_step_handler(msg, forward_to_support_admin)


def forward_to_support_admin(message):
  uid = str(message.from_user.id)
  data = load_data()
  lang = data.get(uid, {}).get("lang", "dr")

  if message.text and message.text.startswith("/"):
    return

  try:
    admins = load_admins()
    user_name = message.from_user.first_name or "بدون نام"
    username = f"@{message.from_user.username}" if message.from_user.username else "ندارد"
    user_text = message.text or message.caption or "فایل / رسانه"

    for admin_id in admins:
      try:
        bot.send_message(
            int(admin_id),
            f"📩 **پیام جدید به پشتیبانی**\n\n"
            f"👤 نام: {user_name}\n"
            f"🔗 یوزرنیم: {username}\n"
            f"🆔 UserID: {uid}\n\n"
            f"💬 متن پیام:\n{user_text}\n\n"
            f"👇 برای پاسخ دادن، همین پیام را ریپلای کنید:",
            parse_mode="Markdown"
        )
      except Exception:
        pass
        
    bot.reply_to(message, TRANSLATIONS[lang]["support_sent"])
  except Exception as e:
    print(f"Error forwarding support message: {e}")


@bot.message_handler(func=lambda message: is_admin(message.from_user.id) and message.reply_to_message is not None)
def admin_reply_to_user(message):
  try:
    replied_msg = message.reply_to_message
    target_uid = None

    if replied_msg.text:
      lines = replied_msg.text.split("\n")
      for line in lines:
        if "UserID:" in line:
          target_uid = "".join(filter(str.isdigit, line))
          break

    if not target_uid:
      bot.reply_to(message, "❌ خطا: نتوانستم آیدی عددی کاربر را از پیام پیدا کنم.")
      return

    bot.send_message(
        chat_id=int(target_uid),
        text=f"💬 **پاسخ پشتیبانی و مدیریت:**\n\n{message.text}",
        parse_mode="Markdown"
    )
    bot.reply_to(message, "✅ پاسخ با موفقیت به کاربر ارسال شد.")
  except Exception as e:
    bot.reply_to(message, f"❌ خطا در ارسال پاسخ: {e}")


@bot.message_handler(commands=["admin"])
def admin_panel(message):
  if not is_admin(message.from_user.id):
    return
  
  markup = types.InlineKeyboardMarkup(row_width=2)
  markup.add(
      types.InlineKeyboardButton("📢 ارسال پیام همگانی", callback_data="admin_broadcast"),
      types.InlineKeyboardButton("📊 آمار کاربران", callback_data="admin_stats")
  )
  bot.reply_to(message, "⚙️ **پنل مدیریت پیشرفته ربات**\n\nلطفاً یکی از گزینه‌ها را انتخاب کنید:", reply_markup=markup, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats_callback(call):
  if not is_admin(call.from_user.id):
    return
  data = load_data()
  total_users = len(data)
  bot.answer_callback_query(call.id, f"👥 مجموع کاربران ربات: {total_users} نفر", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast")
def admin_broadcast_callback(call):
  if not is_admin(call.from_user.id):
    return
  msg = bot.send_message(call.message.chat.id, "✍️ پیام خود را برای ارسال همگانی به تمام کاربران بنویسید:")
  bot.register_next_step_handler(msg, perform_broadcast)


def perform_broadcast(message):
  data = load_data()
  count = 0
  for uid in data:
    try:
      bot.send_message(int(uid), message.text)
      count += 1
    except:
      pass
  bot.reply_to(message, f"✅ پیام همگانی با موفقیت برای {count} کاربر ارسال شد.")


@bot.message_handler(commands=["GROUP"])
def manage_groups_channels(message):
  if str(message.from_user.id) != str(INITIAL_ADMIN_ID):
    bot.reply_to(message, "❌ فقط مالک اصلی ربات اجازه استفاده از این دستور را دارد.")
    return

  markup = types.InlineKeyboardMarkup()
  markup.add(
      types.InlineKeyboardButton("➕ افزودن کانال/گروه", callback_data="grp_add"),
      types.InlineKeyboardButton("🗑️ حذف کانال/گروه", callback_data="grp_remove")
  )
  channels = load_channels()
  ch_list_text = "\n".join([f"📌 {c['name']} | لینک: {c['url']}" for c in channels])
  
  text = f"⚙️ **مدیریت کانال و گروه‌های عضویت اجباری**\n\nلیست فعلی:\n{ch_list_text if channels else 'خالی است'}"
  bot.reply_to(message, text, reply_markup=markup, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data in ["grp_add", "grp_remove"])
def group_callback_handler(call):
  if str(call.from_user.id) != str(INITIAL_ADMIN_ID):
    return
  
  bot.answer_callback_query(call.id)
  if call.data == "grp_add":
    msg = bot.send_message(
        call.message.chat.id,
        "✍️ لطفاً لینک کانال را بفرستید (یا طبق فرمت `نام,لینک,آیدی` ارسال کنید):",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, save_new_channel_step)
  elif call.data == "grp_remove":
    channels = load_channels()
    if not channels:
      bot.send_message(call.message.chat.id, "❌ هیچ کانال یا گروهی ثبت نشده است.")
      return
    
    markup = types.InlineKeyboardMarkup()
    for i, c in enumerate(channels):
      markup.add(types.InlineKeyboardButton(f"حذف: {c['name']}", callback_data=f"del_ch_{i}"))
    bot.send_message(call.message.chat.id, "🗑️ موردی را که می‌خواهید حذف کنید انتخاب کنید:", reply_markup=markup)


def save_new_channel_step(message):
  if str(message.from_user.id) != str(INITIAL_ADMIN_ID):
    return
  try:
    text = message.text.strip()
    
    if "t.me/" in text:
      parts = text.split("/")
      ch_id = "@" + parts[-1]
      name = "کانال جدید"
      url = text
    else:
      parts = text.split(",")
      if len(parts) < 3:
        bot.reply_to(message, "❌ فرمت اشتباه است. لطفاً لینک را بفرستید یا طبق فرمت `نام,لینک,آیدی` عمل کنید.")
        return
      name, url, ch_id = parts[0].strip(), parts[1].strip(), parts[2].strip()

    channels = load_channels()
    channels.append({"name": name, "url": url, "id": ch_id})
    save_channels(channels)
    bot.reply_to(message, f"✅ کانال `{name}` با آیدی `{ch_id}` با موفقیت اضافه شد!")
  except Exception as e:
    bot.reply_to(message, f"❌ خطا: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("del_ch_"))
def delete_channel_callback(call):
  if str(call.from_user.id) != str(INITIAL_ADMIN_ID):
    return
  try:
    idx = int(call.data.split("_")[2])
    channels = load_channels()
    if 0 <= idx < len(channels):
      removed = channels.pop(idx)
      save_channels(channels)
      bot.answer_callback_query(call.id, f"✅ {removed['name']} حذف شد.")
      bot.edit_message_text("✅ با موفقیت حذف گردید.", call.message.chat.id, call.message.message_id)
  except Exception as e:
    bot.answer_callback_query(call.id, f"❌ خطا: {e}")


@bot.message_handler(commands=["SHAHID"])
def manage_admins(message):
  if str(message.from_user.id) != str(INITIAL_ADMIN_ID):
    bot.reply_to(message, "❌ فقط مالک اصلی اجازه دارد.")
    return

  admins = load_admins()
  admin_list_text = "\n".join([f"👤 آیدی: `{aid}`" for aid in admins])

  markup = types.InlineKeyboardMarkup(row_width=1)
  markup.add(
      types.InlineKeyboardButton("➕ افزودن ادمین", callback_data="admin_add_prompt"),
      types.InlineKeyboardButton("🗑️ حذف ادمین", callback_data="admin_remove_prompt")
  )

  text = (
      f"⚙️ **مدیریت ادمین‌های ربات**\n\n"
      f"📋 **لیست ادمین‌های فعلی:**\n{admin_list_text}\n\n"
      f"لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
  )
  bot.reply_to(message, text, reply_markup=markup, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data in ["admin_add_prompt", "admin_remove_prompt"])
def admin_action_prompt_callback(call):
  if str(call.from_user.id) != str(INITIAL_ADMIN_ID):
    return
  
  bot.answer_callback_query(call.id)
  if call.data == "admin_add_prompt":
    msg = bot.send_message(
        call.message.chat.id,
        "✍️ لطفاً آیدی عددی کاربری که می‌خواهید به عنوان ادمین اضافه کنید را بفرستید:",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, process_add_admin_step)
  elif call.data == "admin_remove_prompt":
    admins = load_admins()
    markup = types.InlineKeyboardMarkup(row_width=1)
    for aid in admins:
      if aid == str(INITIAL_ADMIN_ID):
        continue
      markup.add(types.InlineKeyboardButton(f"حذف آیدی: {aid}", callback_data=f"adm_rem_direct_{aid}"))
    
    if len(admins) <= 1:
      bot.send_message(call.message.chat.id, "❌ هیچ ادمین دیگری برای حذف وجود ندارد.")
    else:
      bot.send_message(call.message.chat.id, "🗑️ ادمینی را که می‌خواهید حذف کنید انتخاب کنید:", reply_markup=markup)


def process_add_admin_step(message):
  if str(message.from_user.id) != str(INITIAL_ADMIN_ID):
    return
  if message.text and message.text.startswith("/"):
    return
  
  target_uid = message.text.strip()
  if not target_uid.isdigit():
    bot.reply_to(message, "❌ آیدی عددی باید فقط شامل عدد باشد.")
    return

  admins = load_admins()
  if target_uid in admins:
    bot.reply_to(message, "⚠️ این کاربر از قبل ادمین است.")
    return

  admins.append(target_uid)
  save_admins(admins)
  bot.reply_to(message, f"✅ کاربر `{target_uid}` با موفقیت به لیست ادمین‌ها اضافه شد.", parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_rem_direct_"))
def remove_admin_callback(call):
  if str(call.from_user.id) != str(INITIAL_ADMIN_ID):
    return
  
  target_uid = call.data.split("_")[3]
  admins = load_admins()
  
  if target_uid in admins and target_uid != str(INITIAL_ADMIN_ID):
    admins.remove(target_uid)
    save_admins(admins)
    bot.answer_callback_query(call.id, f"✅ ادمین {target_uid} حذف شد.")
    bot.edit_message_text("✅ ادمین مورد نظر با موفقیت از لیست حذف گردید.", call.message.chat.id, call.message.message_id)
  else:
    bot.answer_callback_query(call.id, "❌ امکان حذف این کاربر وجود ندارد.")


@bot.message_handler(commands=["add"])
def manage_score(message):
  if not is_admin(message.from_user.id):
    return
  args = message.text.split()
  if len(args) < 3:
    bot.reply_to(message, "❌ فرمت صحیح:\n`/add USER_ID SCORE`", parse_mode="Markdown")
    return
  target_uid = args[1]
  amount = int(args[2])
  data = load_data()
  if target_uid not in data:
    data[target_uid] = {"score": 0, "lang": "dr", "bots": {}}
  data[target_uid]["score"] += amount
  save_data(data)
  bot.reply_to(message, f"✅ امتیاز اضافه شد. موجودی جدید: {data[target_uid]['score']}")


def check_code_syntax(file_path):
  """بررسی صحت سینتکس فایل پایتون پیش از اجرا"""
  try:
    with open(file_path, "r", encoding="utf-8") as f:
      code_content = f.read()
    
    compile(code_content, file_path, "exec")
    return True, None
  except Exception as e:
    return False, str(e)


@bot.message_handler(content_types=["document"])
def handle_docs_from_step(message):
  uid = str(message.from_user.id)
  data = load_data()
  lang = data.get(uid, {}).get("lang", "dr")

  if not check_user_membership(uid):
    bot.reply_to(message, "❌ Join channels first!" if lang == "en" else "❌ ابتدا باید در کانال‌ها عضو شوید!")
    return

  cost = data.get(uid, {}).get("pending_cost", 50)
  duration = data.get(uid, {}).get("pending_duration", 24 * 3600)
  
  if data.get(uid, {}).get("score", 0) < cost:
    msg_text = f"❌ Not enough score! Need {cost} score." if lang == "en" else f"❌ امتیاز شما برای این پکیج کافی نیست ({cost} امتیاز لازم است)."
    bot.reply_to(message, msg_text)
    return

  if not message.document.file_name.endswith(".py"):
    bot.reply_to(message, "❌ لطفاً فقط فایل با پسوند `.py` ارسال کنید." if lang != "en" else "❌ Please send only `.py` files.")
    return

  file_id = message.document.file_id
  file_name = message.document.file_name.replace(".py", "")
  
  # ایجاد شناسه یکتا برای ربات جدید کاربر
  bot_unique_id = f"{uid}_{file_name}"

  file_info = bot.get_file(file_id)
  downloaded_file = bot.download_file(file_info.file_path)
  
  path = os.path.join(USER_BOTS_DIR, f"{bot_unique_id}_bot.py")
  with open(path, "wb") as f:
    f.write(downloaded_file)

  is_valid, error_message = check_code_syntax(path)
  if not is_valid:
    if os.path.exists(path):
      os.remove(path)
      
    error_report = (
        f"❌ **کد نویسی شما دارای خطاست!**\n\n```text\n{error_message}\n```"
    )
    bot.send_message(message.chat.id, error_report, parse_mode="Markdown")
    return

  process = subprocess.Popen(["python3", path])
  active_user_processes[bot_unique_id] = process

  if uid not in data:
    data[uid] = {"score": 0, "lang": lang, "bots": {}}
  
  if "bots" not in data[uid]:
    data[uid]["bots"] = {}

  expire_time = time.time() + duration
  data[uid]["bots"][bot_unique_id] = {
      "file_name": file_name,
      "file_id": file_id,
      "expire_time": expire_time
  }
  
  data[uid]["score"] -= cost
  
  if "pending_cost" in data[uid]:
    del data[uid]["pending_cost"]
  if "pending_duration" in data[uid]:
    del data[uid]["pending_duration"]
    
  save_data(data)

  success_text = f"🚀 **تبریک! ربات ({file_name}) با موفقیت آنلاین و روشن شد** ✨"
  bot.send_message(message.chat.id, success_text, reply_markup=get_main_menu(lang), parse_mode="Markdown")

  try:
    bot.send_message(
        chat_id=int(uid),
        text=(
            "🤖 **اطلاعیه مهم سیستم:**\n\n"
            f"ربات شما ({file_name}) با موفقیت توسط **ریس شاهد** آنلاین و روی سرور فعال گردید! ✨\n\n"
            "💬 اگر می‌خواهید ربات‌های بیشتری بسازید یا سفارشی‌سازی کنید، لطفاً از طریق بخش **پشتیبانی** با ریس شاهد در ارتباط باشید."
        ),
        parse_mode="Markdown"
    )
  except Exception as e:
    print(f"Could not send notification directly to user: {e}")


if __name__ == "__main__":
  print("Bot Manager is running...")
  load_admins()
  
  checker_thread = threading.Thread(target=background_expiration_checker, daemon=True)
  checker_thread.start()

  if os.path.exists(DATA_FILE):
    try:
      with open(DATA_FILE, "r", encoding="utf-8") as f:
        saved_data = json.load(f)
        current_time = time.time()
        for user_id, user_info in saved_data.items():
          bots_dict = user_info.get("bots", {})
          
          # اگر ساختار جدید چند رباتی بود
          if bots_dict:
            for b_unique_id, b_data in list(bots_dict.items()):
              expire_time = b_data.get("expire_time")
              if expire_time and current_time >= expire_time:
                del bots_dict[b_unique_id]
                continue
              
              bot_path = os.path.join(USER_BOTS_DIR, f"{b_unique_id}_bot.py")
              if os.path.exists(bot_path):
                try:
                  proc = subprocess.Popen(["python3", bot_path])
                  active_user_processes[b_unique_id] = proc
                except Exception as e:
                  print(f"Failed to restart bot {b_unique_id}: {e}")
          
          # سازگاری با ساختار قدیمی تک رباتی
          else:
            expire_time = user_info.get("expire_time")
            if expire_time and current_time >= expire_time:
              user_info["file_id"] = None
              user_info["expire_time"] = None
              continue

            bot_path = os.path.join(USER_BOTS_DIR, f"{user_id}_bot.py")
            if os.path.exists(bot_path):
              try:
                proc = subprocess.Popen(["python3", bot_path])
                active_user_processes[user_id] = proc
              except Exception as e:
                print(f"Failed to restart legacy bot for {user_id}: {e}")

        save_data(saved_data)
    except Exception as e:
      print(f"Error loading saved bots on startup: {e}")

  bot.infinity_polling()
