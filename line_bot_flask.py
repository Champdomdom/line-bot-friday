from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import sqlite3
import os

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "YOUR_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET", "YOUR_SECRET"))

# สร้าง DB
conn = sqlite3.connect('balance.db')
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS balance (id INTEGER PRIMARY KEY, amount INTEGER)')
c.execute('INSERT OR IGNORE INTO balance (id, amount) VALUES (1, 0)')
conn.commit()
conn.close()

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    conn = sqlite3.connect('balance.db')
    c = conn.cursor()
    c.execute('SELECT amount FROM balance WHERE id=1')
    current_balance = c.fetchone()[0]

    if text.startswith('+') and text[1:].isdigit():
        change = int(text[1:])
        current_balance += change
        c.execute('UPDATE balance SET amount = ? WHERE id=1', (current_balance,))
        conn.commit()
        reply = f"เพิ่มแล้ว: +{change}\nยอดรวม: {current_balance}"
    elif text.startswith('-') and text[1:].isdigit():
        change = int(text[1:])
        current_balance -= change
        c.execute('UPDATE balance SET amount = ? WHERE id=1', (current_balance,))
        conn.commit()
        reply = f"ลดแล้ว: -{change}\nยอดรวม: {current_balance}"
    else:
        reply = f"ยอดรวมตอนนี้: {current_balance}"
    conn.close()

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    app.run()
