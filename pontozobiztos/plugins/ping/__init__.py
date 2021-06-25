def on_message(message, author):
    """
        Args:
            message (fbchat.MessageData)
            author(models.User.User)
    """
    
    formatted = message.text.lower().strip()
    
    if formatted[1:] == 'ing':
        message.thread.send_text(formatted[0] + 'ong')
