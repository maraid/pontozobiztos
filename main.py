from dotenv import load_dotenv
import logging
import json
import asyncio
import os
from pontozobiztos import HomoBot

COOKIES_LOC = "/chatbot_data/cookies"

load_dotenv()
logger = logging.getLogger("chatbot")
# loop = asyncio.get_event_loop()


def start():
    try:
        logger.debug("Reading cookies...")
        with open(COOKIES_LOC, "r") as cookies:
            session_cookies = json.load(cookies)
        logger.debug("Cookies found. Trying to use them to log in")
    except (FileNotFoundError, EOFError):
        session_cookies = None
        logger.debug("Cookies were not found. Using email and password...")

    logger.info("Logging in...")
    client = HomoBot.HomoBot(email=os.getenv('EMAIL'),
                             password=os.getenv('PASSWORD'),
                             session_cookies=session_cookies)
    logger.info("Login successful!")
    with open(COOKIES_LOC, "w") as cookies:
        json.dump(client.getSession(), cookies)
        logger.debug("Cookies saved with pickle protocol")

    logger.info("facebook client is listening...")
    client.listen()


if __name__ == "__main__":
    start()
