from server.config import config
from bot import BotTelegram
import os
from dotenv import load_dotenv
load_dotenv()
myBot=BotTelegram(os.getenv('ApiTelegram'),config["schema"])
myBot.polling()