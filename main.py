from dotenv import load_dotenv
import logging
import pickle
import asyncio
import os
from pontozobiztos import HomoBot

load_dotenv()
logger = logging.getLogger("chatbot")
loop = asyncio.get_event_loop()


async def start():
    try:
        logger.debug("Reading cookies...")
        with open("cookies", "rb") as cookies:
            session_cookies = pickle.load(cookies)
        logger.debug("Cookies found. Trying to use them to log in")
    except (FileNotFoundError, pickle.UnpicklingError, EOFError):
        session_cookies = None
        logger.debug("Cookies were not found. Using email and password...")

    logger.info("Logging in...")
    client = await HomoBot.create(email=os.getenv('EMAIL'),
                                  password=os.getenv('PASSWORD'),
                                  session_cookies=session_cookies,
                                  loop=loop)
    logger.info("Login successful!")
    with open("cookies", "wb") as cookies:
        pickle.dump(client.get_session(), cookies)
        logger.debug("Cookies saved with pickle protocol")

    logger.info("facebook client is listening...")
    client.listen()


if __name__ == "__main__":
    loop.run_until_complete(start())
    loop.run_forever()
