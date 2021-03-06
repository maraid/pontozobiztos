"""Main entry point"""
import fbchat
import logging
import functools
import types


class ClientProxy:
    """Proxy for fbchat.Client. It's purpose is to separate those functions
    that need to be exposed, from those that don't.
    It can also be used to add extra functionality, such as send_text.

    Args:
        obj (MyClient): MyClient object to act as a proxy on.
    """
    functions = {}

    # this block lists the methods to be registered. The purpose of this
    # is to suppress PyCharm warnings.
    send: types.MethodType
    send_uri: types.MethodType
    react_to_message: types.MethodType
    fetch_message_info: types.MethodType
    fetch_group_info: types.MethodType

    def __init__(self, obj):
        self.uid = obj.uid
        for name, func in self.functions.items():
            setattr(self, name, functools.partial(func, obj))

    @classmethod
    def register(cls, name):
        def something(func):
            cls.functions.update({name: func})
            return func
        return something

    def send_text(self, text):
        """Sends a text message back"""
        self.send(fbchat.Message(text=text,))

    def send_reply(self, reply_to_id, text):
        """Sends a text response to reply_to_id"""
        self.send(fbchat.Message(text=text, reply_to_id=reply_to_id))

    def send_uri_reply(self, reply_to_id, uri, text=None):
        self.send_uri(uri, fbchat.Message(text=text, reply_to_id=reply_to_id))

    def remove_reaction(self, message_id):
        """Removes a reaction from message marked by message_id"""
        self.react_to_message(message_id, None)


class MyClient(fbchat.Client):
    """MyClient is the first layer on top fbchat. This class only
    allows access to the chat through some functions.."""
    GROUP_ID = '232447473612485'
    SILENT = False
    ENABLED = True

    def __init__(self, *args, **kwargs):
        super(MyClient, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger("chatbot.MyClient")
        self.proxy = ClientProxy(self)

    @ClientProxy.register("fetch_message_info")
    def fetch_message_info(self, mid, thread_id=None):
        del thread_id
        return super().fetch_message_info(mid, self.GROUP_ID)

    @ClientProxy.register("fetch_group_info")
    def fetch_group_info(self, *group_ids):
        del group_ids
        return (super().fetchGroupInfo(self.GROUP_ID))[self.GROUP_ID]

    @ClientProxy.register("send")
    def send(self, message, thread_id=None, thread_type=None):
        del thread_id
        # del thread_type

        if not self.ENABLED:
            self.logger.info("Message hasn't been sent due to inactive mode")
            return None

        if self.SILENT:
            self.logger.info("Message hasn't been sent due to silent mode")
            return None

        return super().send(message, self.GROUP_ID, ThreadType.GROUP)
        # return await super().send(message, '1445795951', ThreadType.USER)

    @ClientProxy.register("send_uri")
    def send_uri(self, uri, message=None):
        return super().sendUri(uri, message,
                               thread_id=self.GROUP_ID,
                               thread_type=ThreadType.GROUP)

    @ClientProxy.register("react_to_message")
    def react_to_message(self, message_id, reaction):
        if not self.ENABLED:
            self.logger.info("Reaction hasn't been sent due to disabled mode")
            return None

        # if self.SILENT:
        #     self.logger.info("Reaction hasn't been sent due to silent mode.")
        #     return None

        if not isinstance(reaction, fbchat.MessageReaction) \
                or reaction is not None:
            try:
                reaction = fbchat.MessageReaction[reaction]
            except KeyError:
                self.logger.error("was called with an incorrect reaction type."
                                  "Check MessageReaction for further info")
                return None

        return super().reactToMessage(message_id, reaction)
