def on_message(message, author):
    """
        Args:
            message (fbchat.MessageData)
            author(models.User.User)
    """
    
    formatted = message.text.lower().strip()
    
    if formatted[1:] == 'ing':
        message.thread.send_text(formatted[0] + 'ong')
    elif formatted[2:] == 'ing' and formatted[:2] in ('cs', 'dz', 'gy', 'ly', 'ny', 'sz', 'ty', 'zs'):
        message.thread.send_text(formatted[:2] + 'ong')
    elif formatted == 'dzsing':
        message.thread.send_text('dzsong')
