from telegram import Bot
import yaml

with open("config.yaml") as f:
    config = yaml.safe_load(f)

bot = Bot(token=config["telegram"]["token"])
chat_id = config["telegram"]["chat_id"]

def send_alert(message):
    bot.send_message(chat_id, message)
