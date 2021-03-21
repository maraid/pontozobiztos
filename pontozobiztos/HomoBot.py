from . import chatmongo
from . import plugins
from .models import User
import importlib
import logging
import fbchat
import os
import pickle
from datetime import datetime
import pytz
import pathlib
from dotenv import load_dotenv
load_dotenv()

utc = pytz.UTC

logger = logging.getLogger("chatbot")
logger.setLevel(logging.DEBUG)

COOKIES_LOC = "/chatbot_data/cookies"

logformat = "%(asctime)s.%(msecs)03d [%(levelname)s] <%(module)s> %(funcName)s(): %(message)s"
dateformat = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(fmt=logformat, datefmt=dateformat)

data_dir = pathlib.Path('/chatbot_data')
data_dir.mkdir(exist_ok=True)
log_file = data_dir / 'chatbot.log'
log_file.touch(exist_ok=True)

fh = logging.FileHandler('/chatbot_data/chatbot.log', 'a', 'utf-8')
fh.setFormatter(formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

# Load plugins from plugins folder.
logger.info("Importing plugins from plugins folder...")
plugin_dict = {}
for module in plugins.__all__:
    plugin = importlib.import_module("pontozobiztos.plugins." + module)
    try:
        logger.info(f"Added module {module} to active plugins")
        plugin_dict[module] = plugin
    except AttributeError:
        logger.warning(f"Plugin '{module}' has no attribute 'ENABLED'.")
        del plugin


def init_plugins(*args, **kwargs):
    """Initializes plugins in    plugin_dict"""
    logger.info("Initializing plugins...")
    for name, obj in plugin_dict.items():
        try:
            obj.init(*args, **kwargs)
        except (TypeError, AttributeError):
            logger.warning("Plugin '{}' could not be initialized "
                           "because it doesn't implement 'init'.".format(name))


def on_2fa_callback():
    return int(input("Enter 2FA code: "))


class HomoBot(fbchat.Session):
    GROUP_ID = '232447473612485'
    SILENT = False
    ENABLED = True
    group: fbchat.GroupData

    @classmethod
    def create(cls):
        logger.info("Logging in...")
        try:
            with open(COOKIES_LOC, "rb") as cookies:
                session_cookies = pickle.load(cookies)
            self = cls.from_cookies(session_cookies)
        except (FileNotFoundError, pickle.UnpicklingError):
            self = cls.login(os.getenv('EMAIL'),
                             os.getenv('PASSWORD'))

        logger.info(f"Starting facebook client. ENABLED: {self.ENABLED}; "
                    f"SILENT: {self.SILENT}")

        logger.info("Login successful!")
        with open(COOKIES_LOC, "wb") as cookies:
            pickle.dump(self.get_cookies(), cookies)
        logger.debug("Cookies saved with pickle protocol")

        self.update_users()
        self.sync_database()
        init_plugins()
        return self

    def listen(self):
        listener = fbchat.Listener(session=self,
                                   chat_on=False,
                                   foreground=False)
        logger.info('Listening...')
        for event in listener.listen():
            if isinstance(event, fbchat.ThreadEvent):
                self.handle_event(event)

    def handle_event(self, event: fbchat._events.Event) -> bool:
        if isinstance(event, fbchat.MessageEvent):
            thread = event.message.thread
            try:
                msg = event.message.fetch()
            except fbchat.HTTPError:
                logger.warning('fbchat.Message.fetch() failed. trying again.')
                msg = event.message.fetch()

            logger.info(msg)

            # message has to come from either the groupchat or an admin directly
            if thread.id == self.GROUP_ID:
                # return False  # COMMENT THIS
                thread = self.group  # changes from Group to GroupData
                chatmongo.insert_or_update_message(msg)
            elif not chatmongo.get_user_info(thread.id).get('is_admin', False):
                return False

            if event.author.id == self.user.id:
                return False

            # don't run plugins on bot's messages
            # if event.author.id != self.user.id:
            for name, mod in plugin_dict.items():
                logger.debug('Running plugin: ' + name)
                # try:
                mod.on_message(thread=thread,
                               author=User.User(event.author.id),
                               message=msg)
            else:
                return False
        elif isinstance(event, fbchat.ReactionEvent):
            chatmongo.add_reaction(event.message.id, event.author.id,
                                   event.reaction)
        return False

    def get_group_user_data(self):
        client = fbchat.Client(session=self)
        self.group = next(client.fetch_thread_info([self.GROUP_ID]))
        ids = [p.id for p in self.group.participants]

        user_data = []
        for key, data in client._fetch_info(*ids).items():
            try:
                nickname = self.group.nicknames[key]
            except KeyError:
                nickname = ''
            user_data.append((key, data['name'], nickname,
                              data['profile_picture']['uri']))
        return user_data

    def update_users(self):
        """Updates the database from Facebook
        (ID, username, nickname w/o points)
        """
        logger.debug("Cross-checking facebook data with database")
        for ud in self.get_group_user_data():
            chatmongo.update_or_add_user(*ud)

        admin_id = os.getenv('ADMIN_ID')
        if admin_id is not None:
            logger.debug(f"Setting admin state for {admin_id}")
            chatmongo.update_info(admin_id, 'is_admin', True)

    def sync_database(self):
        logger.debug("Synchronizing database with facebook")
        try:
            latest_msg_ts = chatmongo.get_latest_message().created_at
        except StopIteration:
            latest_msg_ts = datetime(year=2000, month=1, day=1, tzinfo=utc)
        before = datetime.now(tz=utc)
        while before > latest_msg_ts:
            data = self.group._fetch_messages(200, before)
            if len(data) <= 1:  # reached the first message
                logger.info('No more messages. Last before: ' + str(before))
                break
            for msg in data[::-1]:  # reverse order will make it restart proof
                chatmongo.insert_or_update_message(msg)
                before = msg.created_at
            # time.sleep(random.uniform(0, 3))
