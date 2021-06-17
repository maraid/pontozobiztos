def on_message(message, author):
    """
        Args:
            message (fbchat.MessageData)
            author(models.User.User)
    """

    if message.text == 'ping':
        message.thread.send_text('pong')
