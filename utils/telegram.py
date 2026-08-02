from telegram import Bot
import yaml

with open("config.yaml") as f:
    config = yaml.safe_load(f)

token = config["telegram"]["token"]
chat_id = config["telegram"]["chat_id"]

def send_alert(message: str):
    """Send a Telegram alert message synchronously."""
    try:
        bot = Bot(token=token)
        bot.send_message(chat_id=chat_id, text=message)
    except Exception as e:
        print(f"Telegram alert failed: {e}")
