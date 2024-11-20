import requests
import schedule
import time
from datetime import datetime, timedelta
import pytz
import logging
import json
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler, CallbackQueryHandler
import nest_asyncio
import asyncio

# ตั้งค่า logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telegram_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Telegram Bot configuration
BOT_TOKEN = "7427156872:AAFwKfSmGQyQSzYtovuaATPJhuDiVJX8PHc"
CHAT_ID = "-4572778669"
API_URL = "https://walrus-app-5ugwj.ondigitalocean.app"
MEMBER_LIST_URL = "https://ag.ambkingapi.com/a/p/memberList"
DEPOSIT_URL = "https://ag.ambkingapi.com/a/p/deposit"

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

def log_request_response(method, url, request_data=None, response=None, error=None):
    """บันทึก request และ response"""
    log_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "method": method,
        "url": url,
        "request_data": request_data
    }
    
    if response:
        log_data.update({
            "status_code": response.status_code,
            "response_data": response.json() if response.text else None,
            "response_time": response.elapsed.total_seconds()
        })
    
    if error:
        log_data["error"] = str(error)
    
    logger.info(f"API Call Details:\n{json.dumps(log_data, indent=2, ensure_ascii=False)}")

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        logger.info(f"Sending Telegram message:\n{message}")
        response = requests.post(url, json=payload)
        log_request_response("POST", url, payload, response)
        return response.json()
    except Exception as e:
        log_request_response("POST", url, payload, error=e)
        logger.error(f"Failed to send Telegram message: {e}")
        return None

def get_winlose_report():
    try:
        # 1. Login
        login_data = {
            "username": "df88a",
            "password": "@Arm987654Arm"
        }
        
        logger.info("Attempting login...")
        login_url = f"{API_URL}/login"
        login_response = requests.post(login_url, json=login_data)
        log_request_response("POST", login_url, login_data, login_response)
        
        if login_response.status_code != 200:
            error_msg = f"Login failed: {login_response.json().get('message')}"
            logger.error(error_msg)
            return error_msg
        
        token = login_response.json().get('token')
        logger.info("Login successful")
        
        # 2. Get dates
        tz = pytz.timezone('Asia/Bangkok')
        today = datetime.now(tz)
        yesterday = today - timedelta(days=1)
        
        # Format dates as required by the API
        start_date = yesterday.strftime("%d-%m-%Y")
        end_date = today.strftime("%d-%m-%Y")
        
        
        logger.info(f"Date range: {start_date} to {end_date}")
        
        # 3. Get winlose data
        wl_data = {
            "token": token,
            "startDate": start_date,
            "endDate": end_date
        }
        
        logger.info("Fetching winlose data...")
        wl_url = f"{API_URL}/getwlagent"
        wl_response = requests.post(wl_url, json=wl_data)
        log_request_response("POST", wl_url, wl_data, wl_response)
        
        if wl_response.status_code != 200:
            error_msg = f"Failed to get winlose data: {wl_response.json().get('message')}"
            logger.error(error_msg)
            return error_msg
        
        data = wl_response.json()
        logger.info("Successfully retrieved winlose data")
        
        # 4. Format message
        footer_data = data.get('footer', {}).get('data', [])[0]

        message = (
            f"🎮 รายงานผลประจำวัน ({start_date} ถึง {end_date})\n\n"
            f"💰 ยอดเดิมพัน: {abs(footer_data.get('betAmt', 0)):,.2f}\n"
            f"💵 ยอดชนะ/แพ้ (Member): {footer_data.get('memberWl', 0):,.2f}\n"
            f"💵 ยอดชนะ/แพ้ (Agent): {footer_data.get('agentWl', 0):,.2f}\n"
            f"💵 ยอดชนะ/แพ้ (Company): {footer_data.get('companyWl', 0):,.2f}\n"
            f"📊 คอมมิชชั่น (Member): {footer_data.get('memberComm', 0):,.2f}\n"
            f"📊 คอมมิชชั่น (Agent): {footer_data.get('agentComm', 0):,.2f}\n"
            f"📊 คอมมิชชั่น (Company): {footer_data.get('companyComm', 0):,.2f}\n"
            f"📊 Gross Commission: {footer_data.get('grossCom', 0):,.2f}\n"
            f"🔄 ยอดรวมสุทธิ (Member): {footer_data.get('memberTotal', 0):,.2f}\n"
            f"🔄 ยอดรวมสุทธิ (Agent): {footer_data.get('agentTotal', 0):,.2f}\n"
            f"🔄 ยอดรวมสุทธิ (Company): {footer_data.get('companyTotal', 0):,.2f}\n"
            f"💹 Valid Amount: {abs(footer_data.get('validAmt', 0)):,.2f}\n"
            f"💹 Win/Lose Total: {footer_data.get('winLoseTotal', 0):,.2f}"
        )
        
        logger.info(f"Prepared message:\n{message}")
        return message
        
    except Exception as e:
        error_msg = f"Error occurred: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg

def send_daily_report():
    logger.info("Starting daily report process...")
    message = get_winlose_report()
    send_telegram_message(message)
    logger.info("Completed daily report process")

# เพิ่ม keyboard layout
def get_keyboard():
    return ReplyKeyboardMarkup([
        ['💰 เช็คเครดิต'],
        ['💸 เติมเครดิต'],
        ['📊 รายงานวันนี้']
    ], resize_keyboard=True)

async def check_credit_balance(update: Update, context: CallbackContext):
    try:
        logger.info("Attempting login for credit check...")
        login_url = f"{API_URL}/login"
        login_data = {
            "username": "df88a",
            "password": "@Arm987654Arm"
        }
        login_response = requests.post(login_url, json=login_data)
        log_request_response("POST", login_url, login_data, login_response)
        
        if login_response.status_code != 200:
            await update.message.reply_text(f"❌ Login failed: {login_response.json().get('message')}")
            return
        
        token = login_response.json().get('token')
        
        # ใช้ get_profile แทน check_credit
        headers = {
            "accept": "application/json, text/plain, */*",
            "authorization": token,
            "content-type": "application/json",
            "origin": "https://ag.ambkub.com",
            "referer": "https://ag.ambkub.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0"
        }
        
        profile_url = f"{API_URL}/get-profile"
        profile_response = requests.post(profile_url, json={"token": token}, headers=headers)
        log_request_response("POST", profile_url, {"token": token}, profile_response)
        
        if profile_response.status_code != 200:
            await update.message.reply_text("❌ ไม่สามารถดึงข้อมูลเครดิตได้")
            return
            
        data = profile_response.json()
        balance = data.get('data', {}).get('balance', {}).get('THB', {}).get('balance', {}).get('$numberDecimal', '0')
        
        message = (
            f"💰 ยอดเครดิตคงเหลือ\n\n"
            f"จำนวน: {float(balance):,.2f} บาท"
        )
        
        await update.message.reply_text(message)
        
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        await update.message.reply_text(error_msg)

async def handle_message(update: Update, context: CallbackContext):
    text = update.message.text
    
    if text == "/credit" or text == "💰 เช็คเครดิต":
        await check_credit_balance(update, context)
    elif text == "📊 รายงานวันนี้":
        message = get_winlose_report()
        await update.message.reply_text(message)

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "เลือกเมนูที่ต้องการ:",
        reply_markup=get_keyboard()
    )

# กำหนด states สำหรับ conversation
CHOOSE_AGENT, ENTER_AMOUNT = range(2)

# Dictionary เก็บข้อมูลชั่วคราวระหว่างการทำรายการ
user_deposit_data = {}

async def deposit_credit(update: Update, context: CallbackContext):
    try:
        # Log เริ่มต้นการทำงาน
        logger.info("Starting deposit_credit function")
        
        # Login
        login_data = {
            "username": "df88a",
            "password": "@Arm987654Arm"
        }
        logger.info(f"Sending login request: {json.dumps(login_data, indent=2)}")
        login_response = requests.post(f"{API_URL}/login", json=login_data)
        logger.info(f"Login response: {json.dumps(login_response.json(), indent=2)}")
        
        if login_response.status_code != 200:
            logger.error(f"Login failed with status code: {login_response.status_code}")
            await update.message.reply_text("❌ ไม่สามารถเข้าสู่ระบบได้")
            return ConversationHandler.END
            
        token = login_response.json().get('token')
        
        # ดึงรายชื่อ agents
        headers = {
            "accept": "application/json, text/plain, */*",
            "authorization": token,
            "content-type": "application/json",
            "origin": "https://ag.ambkub.com",
            "referer": "https://ag.ambkub.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0"
        }
        
        member_payload = {
            "page": 1,
            "limit": 100
        }
        
        logger.info(f"Sending member list request: {json.dumps(member_payload, indent=2)}")
        logger.info(f"Member list headers: {json.dumps(headers, indent=2)}")
        
        member_response = requests.post(MEMBER_LIST_URL, json=member_payload, headers=headers)
        logger.info(f"Member list response: {json.dumps(member_response.json(), indent=2)}")
        
        if member_response.status_code != 200:
            logger.error(f"Failed to get member list with status code: {member_response.status_code}")
            await update.message.reply_text("❌ ไม่สามารถดึงรายชื่อ Agent ได้")
            return ConversationHandler.END
            
        members = member_response.json().get('data', {}).get('docs', [])
        
        # สร้าง inline keyboard จากรายชื่อ agents พร้อมชื่อ
        keyboard = []
        for member in members:
            username = member['username']
            name = member['name']
            display_text = f"{username} - {name}"
            keyboard.append([InlineKeyboardButton(
                display_text,
                callback_data=f"agent_{username}"
            )])
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # เก็บข้อมูลไว้ใช้ในขั้นตอนต่อไป
        context.user_data['token'] = token
        context.user_data['members'] = {m['username']: m['name'] for m in members}
        
        await update.message.reply_text(
            "เลือก Agent ที่ต้องการเติมเครดิต:",
            reply_markup=reply_markup
        )
        
        return CHOOSE_AGENT
        
    except Exception as e:
        logger.error(f"Error in deposit_credit: {str(e)}", exc_info=True)
        await update.message.reply_text("❌ เกิดข้อผิดพลาด")
        return ConversationHandler.END

async def agent_chosen(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    username = query.data.replace("agent_", "")
    name = context.user_data['members'].get(username, '')
    
    context.user_data['chosen_username'] = username
    
    await query.edit_message_text(f"กรุณาระบุจำนวนเงินที่ต้องการเติมให้ {username} - {name}:")
    
    return ENTER_AMOUNT

async def amount_entered(update: Update, context: CallbackContext):
    try:
        amount = round(float(update.message.text), 2)
        username = context.user_data['chosen_username']
        token = context.user_data['token']
        
        # ดึงรายชื่อสมาชิกเพื่อหา user_id
        member_headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9,th;q=0.8",
            "authorization": token,
            "content-type": "application/json",
            "sec-ch-ua": '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "origin": "https://ag.ambkub.com",
            "referer": "https://ag.ambkub.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }
        
        member_payload = {
            "page": 1,
            "limit": 100
        }
        
        session = requests.Session()
        
        logger.info(f"Sending member list request: {json.dumps(member_payload, indent=2)}")
        member_response = session.post(MEMBER_LIST_URL, json=member_payload, headers=member_headers)
        logger.info(f"Member list response: {json.dumps(member_response.json(), indent=2)}")
        
        if member_response.status_code != 200:
            logger.error(f"Failed to get member list with status code: {member_response.status_code}")
            await update.message.reply_text("❌ เกิดข้อผิดพลาดในการค้นหาข้อมูลสมาชิก")
            return ConversationHandler.END
            
        members = member_response.json().get('data', {}).get('docs', [])
        user_id = None
        
        # ค้นหา _id ของ username ที่ต้องการ
        for member in members:
            if member['username'] == username:
                user_id = member['_id']
                break
                
        if not user_id:
            logger.error(f"User ID not found for username: {username}")
            await update.message.reply_text("❌ ไม่พบข้อมูลสมาชิก")
            return ConversationHandler.END
            
        # Payload สำหรับการฝากเงิน
        deposit_data = {
            "token": token,
            "userId": user_id,  # ใช้ user_id ที่ได้จากการค้นหา
            "cur": "THB",
            "amount": amount,
            "passcode": "042734"
        }
        
        logger.info(f"Sending deposit request: {json.dumps(deposit_data, indent=2)}")
        
        deposit_response = session.post(DEPOSIT_URL, json=deposit_data, headers=member_headers)
        
        # Log responses
        logger.info(f"Raw deposit response: {deposit_response.text}")
        logger.info(f"Response status code: {deposit_response.status_code}")
        logger.info(f"Response headers: {dict(deposit_response.headers)}")
        
        try:
            response_data = deposit_response.json()
            logger.info(f"Deposit response JSON: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError as je:
            logger.error(f"Failed to parse JSON response: {je}")
            logger.error(f"Response content: {deposit_response.text}")
                
        if deposit_response.status_code == 200:
            if response_data.get('code') == 0:
                name = context.user_data['members'].get(username, '')
                await update.message.reply_text(
                    f"✅ เติมเครดิตสำเร็จ\n"
                    f"จำนวน: {amount:,.2f} บาท\n"
                    f"ให้กับ: {username} - {name}"
                )
            else:
                error_msg = response_data.get('msg', 'ไม่ทราบสาเหตุ')
                logger.error(f"Deposit failed with error: {error_msg}")
                await update.message.reply_text(f"❌ เติมเครดิตไม่สำเร็จ\nสาเหตุ: {error_msg}")
        else:
            logger.error(f"Deposit failed with status code: {deposit_response.status_code}")
            await update.message.reply_text("❌ เติมเครดิตไม่สำเร็จ")
            
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text("❌ กรุณาระบุจำนวนเงินเป็นตัวเลขเท่านั้น")
        return ENTER_AMOUNT
    except Exception as e:
        logger.error(f"Error in amount_entered: {str(e)}", exc_info=True)
        await update.message.reply_text("❌ เกิดข้อผิดพลาด")
        return ConversationHandler.END

async def main():
    logger.info("Bot starting...")
    
    # สร้าง application ด้วย builder pattern
    application = Application.builder().token(BOT_TOKEN).build()
    
    # เพิ่ม conversation handler สำหรับการเติมเครดิต
    deposit_conv = ConversationHandler(
        entry_points=[
            CommandHandler('deposit', deposit_credit),
            MessageHandler(filters.Regex('^💸 เติมเครดิต$'), deposit_credit)
        ],
        states={
            CHOOSE_AGENT: [CallbackQueryHandler(agent_chosen)],
            ENTER_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, amount_entered)]
        },
        fallbacks=[],
    )
    
    application.add_handler(deposit_conv)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("credit", check_credit_balance))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # เริ่มการทำงานของ bot
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())