from . import MyClient
from . import chatmongo
from . import plugins
from .models import User
import importlib
import logging
import fbchat
import pathlib
import urllib.request
import os
import copy


logger = logging.getLogger("chatbot")
logger.setLevel(logging.DEBUG)

logformat = "%(asctime)s.%(msecs)03d [%(levelname)s] <%(module)s> %(funcName)s(): %(message)s"
dateformat = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(fmt=logformat, datefmt=dateformat)

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
        if not plugin.ENABLED:
            logger.info(f"Plugin '{module}' is disabled.")
            del plugin
        else:
            plugin_dict[module] = plugin
    except AttributeError:
        logger.warning(f"Plugin '{module}' has no attribute 'ENABLED'.")
        del plugin


def init_plugins(*args, **kwargs):
    """Initializes plugins in    plugin_dict"""
    for name, obj in plugin_dict.items():
        try:
            obj.init(*args, **kwargs)
        except (TypeError, AttributeError):
            logger.warning("Plugin '{}' could not be initialized "
                           "because it doesn't implement 'init'.".format(name))


class HomoBot(MyClient.MyClient):
    @classmethod
    async def create(cls, email, password, session_cookies=None, loop=None):
        self = HomoBot(loop=loop)
        logger.info(f"Starting facebook client. ENABLED: {self.ENABLED}; "
                    f"SILENT: {self.SILENT}")
        await self.start(email=email,
                         password=password,
                         session_cookies=session_cookies)
        logger.debug("Cross-checking facebook data with database")
        await self.update_users()
        logger.info("Initializing plugins...")
        init_plugins(client=self.proxy)
        return self

    async def on_message(
        self,
        mid=None,
        author_id=None,
        message_object=None,
        thread_id=None,
        thread_type=fbchat.ThreadType.USER,
        at=None,
        metadata=None,
        msg=None,
    ):
        if thread_id != self.GROUP_ID:
            return
        # if thread_id != self.uid:
        #     return

        logger.info(f"{message_object} from {author_id}")

        if message_object.attachments:
            save_images(message_object)  # creates path attr. in ImageAttachment

        chatmongo.insert_or_update_message(message_object)

        for mod in plugin_dict.values():
            try:
                await mod.on_message(client=self.proxy,
                                     author=User.User(author_id),
                                     message=copy.copy(message_object))
            except (AttributeError, TypeError):
                print("found smt" + mid.__name__)

    async def on_message_unsent(
        self,
        mid=None,
        author_id=None,
        thread_id=None,
        thread_type=None,
        at=None,
        msg=None,
    ):
        if thread_id != self.GROUP_ID:
            return

        logger.info(f"{author_id} unsent the message {repr(mid)} at {at}")

        if not chatmongo.mark_message_as_deleted(mid):
            msg = await self.fetch_message_info(mid)
            chatmongo.insert_or_update_message(msg)

        for mod in plugin_dict.values():
            try:
                await mod.on_message_unsent(client=self.proxy,
                                            user=User.User(author_id),
                                            mid=mid)
            except (AttributeError, TypeError):
                pass

    async def on_message_seen(
        self,
        seen_by=None,
        thread_id=None,
        thread_type=fbchat.ThreadType.USER,
        seen_at=None,
        at=None,
        metadata=None,
        msg=None,
    ):
        if thread_id != self.GROUP_ID:
            return

        logger.info(f"Messages seen by {seen_by} at {seen_at}")

        chatmongo.set_last_read_at(seen_by, seen_at)

        for mod in plugin_dict.values():
            try:
                await mod.on_message_seen(client=self.proxy, seen_by=seen_by)
            except (AttributeError, TypeError):
                pass

    async def on_reaction_added(
        self,
        mid=None,
        reaction=None,
        author_id=None,
        thread_id=None,
        thread_type=None,
        at=None,
        msg=None,
    ):
        if thread_id != self.GROUP_ID:
            return

        logger.info(
            f"{author_id} reacted to message {mid} with {reaction.name}")

        if not chatmongo.add_reaction(mid, author_id, reaction):
            msg = await self.fetch_message_info(mid)
            chatmongo.insert_or_update_message(msg)

        for mod in plugin_dict.values():
            try:
                await mod.on_reaction_added(client=self.proxy,
                                            message_id=mid,
                                            reaction=reaction,
                                            user=User.User(author_id))
            except (AttributeError, TypeError):
                pass

    async def on_reaction_removed(
        self,
        mid=None,
        author_id=None,
        thread_id=None,
        thread_type=None,
        at=None,
        msg=None,
    ):
        if thread_id != self.GROUP_ID:
            return
        logger.info(f"{author_id} removed reaction from {mid} message.")
        if not chatmongo.remove_reaction(mid, author_id):
            msg = await self.fetch_message_info(mid)
            chatmongo.insert_or_update_message(msg)

        for mod in plugin_dict.values():
            try:
                await mod.on_reaction_removed(client=self.proxy,
                                              message_id=mid,
                                              user=User.User(author_id))
            except (AttributeError, TypeError):
                pass

    async def update_users(self):
        """Updates the database from Facebook
        (ID, username, nickname w/o points)
        """
        group_info = await self.fetch_group_info()
        fb_id_set = group_info.participants
        db_id_set = set(chatmongo.get_user_ids())
        if (fb_id_set - db_id_set) != set():
            for uid, user in (await self.fetch_user_info(*fb_id_set)).items():
                chatmongo.update_or_add_user(
                    uid,
                    user.name,
                    group_info.nicknames.get(uid)
                )


def save_images(message_object):
    """Save images found in a Message object. The path that the
    image is saved to is stored back into the message_object in the
    ImageAttachment as 'path'.

    filename format:
        YYYYmmddHHMMSS_<user_id>_<attachment_id>.<ext>

    Args:
        message_object (fbchat.Message): fbchat.Message object

    Returns:
        None
    """
    def create_filename(attachment) -> str:
        """Creates filename to save as with extension.

        Args:
            attachment (fbchat.ImageAttachment): attachment obj.

        Returns:
            str: filename
        """
        file_tup = (message_object.created_at.strftime('%Y%m%d%H%M%S'),
                    message_object.author,
                    attachment.uid)
        return '_'.join(file_tup) + '.' + attachment.original_extension

    # TODO: better config file perhaps?!
    img_dir_path = os.getenv('IMAGE_DIRECTORY')
    if img_dir_path is None:
        logger.error("Environmental variable 'IMAGE_DIRECTORY' was not found.")
        return

    path = pathlib.Path(img_dir_path)
    if not path.exists():
        logger.warning(f"Image directory '{img_dir_path}' does not exists."
                       f"Trying to create it...")
        path.mkdir()
        return

    for att in message_object.attachments:
        if isinstance(att, fbchat.ImageAttachment):
            fpath = path / create_filename(att)
            urllib.request.urlretrieve(att.large_preview_url, str(fpath))
            logger.info(f"Image saved to path: {fpath}")
            att.path = str(fpath)
