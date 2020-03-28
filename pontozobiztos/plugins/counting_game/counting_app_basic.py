counter = 0
is_running = True
last_player = None


async def on_message(client, author, message):
    global counter
    global is_running
    global last_player

    try:
        number = int(message.text)
    except ValueError:
        return

    if is_running and (number != (counter + 1) or author.uid == last_player):
        counter = 0
        last_player = None
        return await client.react_to_message(message.uid, 'NO')

    last_player = author.uid
    counter += 1
    await client.react_to_message(message.uid, 'YES')
