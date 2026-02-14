import os
import dotenv
import random
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

dotenv.load_dotenv()
matches = {}
ciam = [] # Currently In A Match
match_id = 5
blocks = open("Blocks.txt", "r").read().split("\n")
print(blocks)
app = App(token='xoxb-2210535565-10464203332802-iIVPjrhLk2jZG4Hfpw7FYf3T')

@app.message("ping")
def ping(ack, say):
    ack()
    say("pong :table_tennis_paddle_and_ball:")

def get_user_id_by_username(username, chanel_id):
    users = members(chanel_id)
    for u in users:
        user = app.client.users_info(user=u)["user"]["name"]
        if username == user:
            return u
    return None

def members(channel_id):
    user_ids = []
    cursor = None
    while True:
        result = app.client.conversations_members(
            channel=channel_id,
            cursor=cursor
        )
        user_ids.extend(result["members"])
        cursor = result.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break
    reals = []
    for uid in user_ids:
        info = app.client.users_info(user=uid)["user"]
        if not info.get("is_bot") and not info.get("is_app_user") and not info.get("deleted"):
            reals.append(uid)
    return reals

@app.command("/match")
def handle_match_command(respond, ack, body, client, logger):
    global match_id
    ack()
    logger.info(body)
    parameters = body["text"].split()
    if len(parameters) == 0:
        respond("Choosing someone for you to play with...", response_type="ephemeral")
        people = members(body["channel_id"])
        others = []
        for uid in people:
            if uid != body["user_id"]:
                others.append(uid)
        chosen = random.choice(others)
        display_name = client.users_info(user=chosen)["user"]["profile"]["display_name"]
        respond(f"Chose {display_name}.", response_type="ephemeral")
    else:
        respond("Crunching the data… hang tight! :hourglass:", response_type="ephemeral")
        chosen = get_user_id_by_username(parameters[0][1:], body["channel_id"])
        if chosen == body["user_id"] and not chosen == "U09PH1UUF6K":
            respond("You can't play against yourself!", response_type="ephemeral")
            return
    timestamp = post_message(client, body["channel_id"], f"Match: <@{body['user_id']}> V/S <@{chosen}> in this thread!")
    post_message(client, body["channel_id"], f"<@{body['user_id']}> starts by choosing a block! Please choose your block outside the thread, as slash commands are not supported in threads.", thread_ts=timestamp)
    match_id += 1
    matches[match_id] = {"initiator": body["user_id"], "matched": chosen, "ts": timestamp, "stage": 0, "Block 1": None, "Block 2": None}
    if not body["user_id"] in ciam:
        ciam.append(body["user_id"])
    if not chosen in ciam:
        ciam.append(chosen)

@app.command("/chooseblock")
def handle_block_choose_command(body, respond, client):
    sent = body["user_id"]
    text = body["text"]
    if sent in ciam:
        for match in matches:
            if match["stage"] == 0:
                if sent == match["initiator"]:
                    if text in blocks:
                        match["Block 1"] = text
                        post_message(client, body["channel_id"], f"<@{body['user_id']}> has chosen a block! Play on!", match["ts"])
                        break
                    else:
                        respond("Please choose a block that exists!", response_type="ephemeral")
                elif sent == match["matched"]:
                    respond("It's not your turn to choose a block! It's your turn to guess the block!" + " (well, when your opponent chooses a block, that is :eye_roll:" if match["Block 1"] is None else "", response_type="ephemeral")
            else:
                if sent == match["matched"]:
                    if text in blocks:
                        match["Block 2"] = text
                        post_message(client, body["channel_id"], f"<@{match['matched']}> has chosen a block! Play on!", match["ts"])
                        break
                    else:
                        respond("Please choose a block that exists!", response_type="ephemeral")
                elif sent == match["initiator"]:
                    respond("It's not your turn to choose a block! It's your turn to guess the block!" + " (well, when your opponent chooses a block, that is :eye_roll:)" if match["Block 2"] is None else "", response_type="ephemeral")
    else:
        respond("You need to be playing a match to use this command!", response_type="ephemeral")


@app.event("message")
def handle_message_events(body: dict, client, logger):
    logger.info(body)
    info = body["event"]
    print("Message: ", info["text"], "[THREADED]" if info.get("thread_ts") else "")
    if info.get("thread_ts") and info.get("parent_user_id") == "U0ADN5Z9SPL":
        pass
        #THREAD
        #post_message(client, info["channel"], "Thready :thread:", info["thread_ts"])

def post_message(client, channel, text, thread_ts=None):
    response = client.chat_postMessage(
        channel=channel,
        text=text,
        thread_ts=thread_ts
    )
    return response["ts"]


if __name__ == "__main__":
    SocketModeHandler(app, os.getenv("API_KEY")).start()
