
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import sqlite3
import os

app = Flask(__name__)

# LINE Bot credentials (replace with env variables in Render)
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# SQLite Setup
def init_db():
    conn = sqlite3.connect("db.sqlite3")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS total (amount INTEGER)")
    if c.execute("SELECT COUNT(*) FROM total").fetchone()[0] == 0:
        c.execute("INSERT INTO total (amount) VALUES (0)")
    conn.commit()
    conn.close()

def update_amount(change):
    conn = sqlite3.connect("db.sqlite3")
    c = conn.cursor()
    c.execute("UPDATE total SET amount = amount + ?", (change,))
    conn.commit()
    amount = c.execute("SELECT amount FROM total").fetchone()[0]
    conn.close()
    return amount

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text.strip()
    if msg.startswith("+") or msg.startswith("-"):
        try:
            change = int(msg)
            new_total = update_amount(change)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"ยอดรวมตอนนี้: {new_total} บาท")
            )
        except ValueError:
            pass

if __name__ == "__main__":
    init_db()
    app.run()
