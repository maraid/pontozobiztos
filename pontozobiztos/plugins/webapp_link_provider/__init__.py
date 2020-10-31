import requests

def on_message(thread, author, message):
    if message.text == '!link':
        ip = requests.get("https://api.ipify.org/?format=json").json()['ip']
        thread.send_text('http://' + ip + '/daily_links', reply_to_id=message.id)
        return True
    return False