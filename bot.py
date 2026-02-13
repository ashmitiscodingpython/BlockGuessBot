import os
import dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

dotenv.load_dotenv()
app = App(token='xoxb-2210535565-10464203332802-iIVPjrhLk2jZG4Hfpw7FYf3T')

@app.message("ping")
def ping(ack, say):
    ack()
    say("pong :table_tennis_paddle_and_ball:")

@app.event("message")
def handle_message_events(body: dict, client, logger):
    logger.info(body)
    info = body["event"]
    if info.get("thread_ts") and info.get("parent_user_id") == "U0ADN5Z9SPL":
        post_message(client, info["channel"], "Thready :thread:", info["thread_ts"])

def post_message(client, channel, text, thread_ts=None):
    client.chat_postMessage(
        channel=channel,
        text=text,
        thread_ts=thread_ts
    )

if __name__ == "__main__":
    SocketModeHandler(app, os.getenv("API_KEY")).start()
