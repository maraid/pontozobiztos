from dotenv import load_dotenv
load_dotenv()

import logging
logger = logging.getLogger('chatbot')

from pontozobiztos.HomoBot import HomoBot


if __name__ == "__main__":
    bot = HomoBot.create()
    bot.listen()
