import time
from datetime import datetime
import logging
import json
from threading import Thread

import requests
from dotenv import load_dotenv
import os

# ====== CONFIGURATION SETTINGS ======
# Bot Settings
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Get this from BotFather

# Token Contract Addresses
BASE_TOKEN_CA = '0x55cD6469F597452B5A7536e2CD98fDE4c1247ee4'
SOL_TOKEN_CA = '9se6kma7LeGcQWyRBNcYzyxZPE3r9t9qWZ8SnjnN3jJ7'

# Alert Settings
PRICE_DIFFERENCE_THRESHOLD = 4.0  # Minimum price difference to trigger alert (percentage)
MINIMUM_PERCENTAGE_CHANGE = 0.1   # Minimum change in percentage to trigger new alert
ALERT_COOLDOWN_SECONDS = 60      # Cooldown period between similar alerts (seconds)

# Monitoring Settings
PRICE_CHECK_INTERVAL = 20        # How often to check prices (seconds)
ERROR_RETRY_INTERVAL = 10        # How long to wait after an error before retrying (seconds)

# Logging Settings
LOG_FILE = 'price_monitor.log'
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# ====== END CONFIGURATION ======

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

class TelegramBot:
    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.subscribers = self.load_subscribers()
        self.last_update_id = 0
        self.last_alert_time = None
        self.last_alert_percentage = None
        self.setup_commands()
        
    def setup_commands(self):
        """Set up the bot's command menu"""
        commands = [
            {
                "command": "start",
                "description": "Get started with the price alert bot"
            },
            {
                "command": "startalert",
                "description": "Subscribe to price difference alerts"
            },
            {
                "command": "stopalert",
                "description": "Unsubscribe from price alerts"
            },
            {
                "command": "status",
                "description": "Check your current subscription status"
            },
            {
                "command": "help",
                "description": "Get help and command information"
            }
        ]
        
        try:
            url = f"{self.base_url}/setMyCommands"
            response = requests.post(url, json={"commands": commands})
            response.raise_for_status()
            logging.info("Bot commands set up successfully")
        except Exception as e:
            logging.error(f"Failed to set up bot commands: {str(e)}")
    
    def load_subscribers(self):
        try:
            with open('static/subscribers.json', 'r') as f:
                return set(json.load(f))
        except FileNotFoundError:
            return set()
    
    def save_subscribers(self):
        with open('static/subscribers.json', 'w') as f:
            json.dump(list(self.subscribers), f)
    
    def send_message(self, chat_id, message):
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Failed to send Telegram message: {str(e)}")

    def broadcast_message(self, message):
        for chat_id in self.subscribers:
            self.send_message(chat_id, message)
    
    def get_updates(self):
        try:
            url = f"{self.base_url}/getUpdates"
            params = {
                "offset": self.last_update_id + 1,
                "timeout": 30
            }
            response = requests.get(url, params=params, timeout=31)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Failed to get updates: {str(e)}")
            return {"ok": False, "result": []}

    def send_help_message(self, chat_id):
        help_text = (
            "🤖 <b>Price Alert Bot Commands</b>\n\n"
            "/start - Start using the bot\n"
            "/startalert - Subscribe to price alerts\n"
            "/stopalert - Unsubscribe from alerts\n"
            "/status - Check your subscription status\n"
            "/help - Show this help message\n\n"
            "ℹ️ <b>About the Alerts</b>\n"
            f"This bot monitors price differences between Solana and Base chains. "
            f"You'll receive alerts when the price difference exceeds {PRICE_DIFFERENCE_THRESHOLD}%.\n\n"
            f"Updates occur every {PRICE_CHECK_INTERVAL} seconds for subscribed users."
        )
        self.send_message(chat_id, help_text)

    def handle_commands(self):
        while True:
            updates = self.get_updates()
            if updates.get("ok"):
                for update in updates["result"]:
                    self.last_update_id = update["update_id"]
                    
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"]
                        username = update["message"]["from"].get("username", "User")
                        
                        if text == "/start":
                            welcome_message = (
                                f"👋 Welcome {username}!\n\n"
                                "I monitor price differences between Solana and Base chains.\n"
                                "Use /startalert to begin receiving alerts.\n"
                                "Use /help to see all available commands."
                            )
                            self.send_message(chat_id, welcome_message)
                        
                        elif text == "/startalert":
                            if chat_id not in self.subscribers:
                                self.subscribers.add(chat_id)
                                self.save_subscribers()
                                self.send_message(chat_id, "✅ You are now subscribed to price alerts!")
                            else:
                                self.send_message(chat_id, "You are already subscribed to alerts!")
                        
                        elif text == "/stopalert":
                            if chat_id in self.subscribers:
                                self.subscribers.remove(chat_id)
                                self.save_subscribers()
                                self.send_message(chat_id, "❌ You have been unsubscribed from price alerts!")
                            else:
                                self.send_message(chat_id, "You are not subscribed to alerts!")
                        
                        elif text == "/status":
                            status = "subscribed" if chat_id in self.subscribers else "not subscribed"
                            self.send_message(chat_id, f"You are currently {status} to price alerts.")
                        
                        elif text == "/help":
                            self.send_help_message(chat_id)

def get_dexscreener_price(token_ca):
    try:
        response = requests.get(f'https://api.dexscreener.com/latest/dex/tokens/{token_ca}', timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed: {str(e)}")
        raise

def parse_prices(token):
    price_data = get_dexscreener_price(token)
    results = []

    for pair in price_data['pairs']:
        pair_info = {
            'dex': pair['dexId'],
            'price_usd': float(pair['priceUsd']),
            'base_token': pair['baseToken']['symbol'],
            'quote_token': pair['quoteToken']['symbol'],
            'pair_address': pair['pairAddress'],
            'liquidity_usd': pair['liquidity']['usd']
        }
        results.append(pair_info)
    
    results.sort(key=lambda x: x['liquidity_usd'], reverse=True)
    return results

def analyze_and_alert(sol_data, base_data, telegram_bot):
    """
    Analyze prices and send alert if difference exceeds threshold,
    with cooldown period unless percentage is different
    """
    current_time = datetime.now()
    sol_price = sol_data[0]['price_usd']
    base_price = base_data[0]['price_usd']
    
    price_diff = abs(sol_price - base_price)
    avg_price = (sol_price + base_price) / 2
    percent_diff = (price_diff / avg_price) * 100

    # Check if difference exceeds threshold
    if percent_diff >= PRICE_DIFFERENCE_THRESHOLD:
        should_send = False
        
        # If this is the first alert or percentage is different from last alert
        if (telegram_bot.last_alert_time is None or 
            telegram_bot.last_alert_percentage is None or 
            abs(percent_diff - telegram_bot.last_alert_percentage) >= MINIMUM_PERCENTAGE_CHANGE):
            should_send = True
        # If it's been more than the cooldown period since last alert
        elif (current_time - telegram_bot.last_alert_time).total_seconds() >= ALERT_COOLDOWN_SECONDS:
            should_send = True

        if should_send:
            message = (
                f"🚨 <b>Price Difference Alert</b> 🚨\n\n"
                f"Difference: {percent_diff:.2f}%\n"
                f"Solana ({sol_data[0]['dex']}): ${sol_price:.4f}\n"
                f"Base ({base_data[0]['dex']}): ${base_price:.4f}\n\n"
                f"💧 Liquidity:\n"
                f"Solana: ${sol_data[0]['liquidity_usd']:,.2f}\n"
                f"Base: ${base_data[0]['liquidity_usd']:,.2f}\n\n"
                f"Timestamp: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            telegram_bot.broadcast_message(message)
            
            # Update last alert time and percentage
            telegram_bot.last_alert_time = current_time
            telegram_bot.last_alert_percentage = percent_diff
            logging.info(f"Alert sent. Difference: {percent_diff:.2f}%")
        else:
            logging.info(f"Alert skipped (cooldown). Difference: {percent_diff:.2f}%")

def price_monitor(telegram_bot):
    while True:
        try:
            sol_data = parse_prices(SOL_TOKEN_CA)
            base_data = parse_prices(BASE_TOKEN_CA)
            analyze_and_alert(sol_data, base_data, telegram_bot)
            time.sleep(PRICE_CHECK_INTERVAL)
            
        except Exception as e:
            logging.error(f"Error in price monitor: {str(e)}")
            time.sleep(ERROR_RETRY_INTERVAL)

def main():
    telegram_bot = TelegramBot(BOT_TOKEN)
    
    # Start command handler in a separate thread
    command_thread = Thread(target=telegram_bot.handle_commands)
    command_thread.daemon = True
    command_thread.start()
    
    # Start price monitoring in main thread
    logging.info("Starting price monitor...")
    price_monitor(telegram_bot)

if __name__ == "__main__":
    main()