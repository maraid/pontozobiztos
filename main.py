from dotenv import load_dotenv
import logging
from pontozobiztos.HomoBot import HomoBot

load_dotenv()
logger = logging.getLogger("chatbot")


if __name__ == "__main__":
    bot = HomoBot.create()
    bot.listen()
