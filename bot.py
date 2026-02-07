import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

app = App(token='xoxb-2210535565-10464203332802-iIVPjrhLk2jZG4Hfpw7FYf3T')

@app.message("ping")
def ping(ack, say):
    ack()
    say("pong :table_tennis_paddle_and_ball:")

@app.event("message")
def handle_message_events(body, logger):
    logger.info(body)

if __name__ == "__main__":
    SocketModeHandler(app, 'xapp-1-A0ADHBVJBUY-10467810726292-a71b25721cfd4cc7e687910ee24dec4ab117905a591ff28ebd94dc981ee465f7').start()
