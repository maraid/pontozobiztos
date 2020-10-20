import logging
from pontozobiztos.HomoBot import HomoBot


logger = logging.getLogger("chatbot")


if __name__ == "__main__":
    bot = HomoBot.create()
    bot.listen()
