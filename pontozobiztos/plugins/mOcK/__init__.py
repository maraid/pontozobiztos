def on_message(message, author):
    """
        Args:
            message (fbchat.MessageData)
            author(models.User.User)
    """

    formatted = message.text.lower().strip()

    if "@cseh" in formatted or "botond" in formatted:
        mocking_text = ""
        for i in range(len(formatted)):
            if i % 2 == 0:
                mocking_text += formatted[i].upper()
            else:
                mocking_text += formatted[i]

        # mocking_text = "".join(c.upper() if i % 2 else c
        #                        for i, c in enumerate(formatted))
        message.thread.send_text(mocking_text)
