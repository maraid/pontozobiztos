from dotenv import load_dotenv
load_dotenv()

import logging
logger = logging.getLogger('chatbot')

from pontozobiztos.HomoBot import HomoBot


if __name__ == "__main__":
    logger.info('PONTOZOBOT starting up!')
    bot = HomoBot.create()
    try:
        bot.listen()
    except Exception as e:
        logger.error(str(e))
        raise
