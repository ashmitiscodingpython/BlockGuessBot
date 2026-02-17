import os
import dotenv
import random
import threading
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import time
import flask

dotenv.load_dotenv()
matches = {}
ciam = []  # Currently In A Match
match_id = 5
blocks = open("Blocks.txt", "r").read().split("\n")
app = App(token='xoxb-2210535565-10464203332802-iIVPjrhLk2jZG4Hfpw7FYf3T')
flask_app = flask.Flask(__name__)

def difficultify(diff: str):
    spli = diff.split("_")
    full = ''
    for word in spli:
        full += word + ' '
    return caseify(full[:-1])

def caseify(text: str):
    words = text.split(" ")
    casified = []
    for word in words:
        casified.append(word[0].upper() + word[1:].lower())
    end = ""
    for word in casified:
        end += word + " "
    return end[:-1]

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
    if len(parameters) == 1:
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
        respond("Doing some processing ma-jig. This may take some time. Hold on!", response_type="ephemeral")
        chosen = get_user_id_by_username(parameters[1][1:], body["channel_id"])
        if chosen == body["user_id"] and not chosen == "U09PH1UUF6K":
            respond("You can't play against yourself!", response_type="ephemeral")
            return
    difficulty = difficultify(parameters[0])
    timestamp = post_message(client, body["channel_id"], f"Match: <@{body['user_id']}> V/S <@{chosen}> in this thread!")
    post_message(client, body["channel_id"], f"<@{body['user_id']}> starts by choosing a block! Please choose your block outside the thread due to Slack bot limitations. Remember, the difficulty is {difficulty}. Choose accordingly.", thread_ts=timestamp)
    match_id += 1
    matches[match_id] = {"initiator": body["user_id"], "matched": chosen, "ts": timestamp, "stage": 0, "Block 1": None, "Block 2": None, "Points": [0, 0], "diff": difficulty}
    if not body["user_id"] in ciam:
        ciam.append(body["user_id"])
    if chosen not in ciam:
        ciam.append(chosen)

@app.command("/chooseblock")
def handle_block_choose_command(ack, body, respond, client, logger):
    ack()
    logger.info(body)
    sent = body["user_id"]
    text = caseify(body["text"])
    if sent in ciam:
        for match_id in matches:
            matchx = matches[match_id]
            if matchx["stage"] == 0:
                if sent == matchx["initiator"]:
                    if text in blocks:
                        matchx["Block 1"] = text
                        respond("Block successfully chosen!", response_type="ephemeral")
                        post_message(client, body["channel_id"], f"<@{body['user_id']}> has chosen a block! Play on!", matchx["ts"])
                        break
                    else:
                        respond("Please choose a block that exists!", response_type="ephemeral")
                elif sent == matchx["matched"]:
                    respond("It's not your turn to choose a block! It's your turn to guess the block!" + " (well, when your opponent chooses a block, that is :eye_roll:" if matchx["Block 1"] is None else "", response_type="ephemeral")
            else:
                if sent == matchx["matched"]:
                    if text in blocks:
                        matchx["Block 2"] = text
                        respond("Block successfully chosen!", response_type="ephemeral")
                        post_message(client, body["channel_id"], f"<@{matchx['matched']}> has chosen a block! Play on!", matchx["ts"])
                        break
                    else:
                        respond("Please choose a block that exists!", response_type="ephemeral")
                elif sent == matchx["initiator"]:
                    respond("It's not your turn to choose a block! It's your turn to guess the block!" + " (well, when your opponent chooses a block, that is :eye_roll:)" if matchx["Block 2"] is None else "", response_type="ephemeral")
    else:
        respond("You need to be playing a match to use this command!", response_type="ephemeral")

@app.event("message")
def handle_message_events(ack, body: dict, client, logger):
    ack()
    logger.info(body)
    info = body["event"]
    print(body)
    print("Message: ", info["text"], "[THREADED]" if info.get("thread_ts") else "")
    if info.get("thread_ts") and info.get("parent_user_id") == "U0ADN5Z9SPL":
        for id in matches:
            matchx = matches[id]
            if matchx["ts"] == info.get("thread_ts"):
                if info["user"] == matchx["initiator"] and matchx["stage"] == 0 and matchx["Block 1"] in caseify(info["text"]):
                    print("BLOCK 1 GUESSED")
                    post_message(
                        client,
                        info["channel"],
                        f"<@{matchx['matched']}> has guessed the block! <@{matchx['initiator']}> gets {0} points. It's <@{matchx['matched']}>'s turn to choose a block now! Remember, the difficulty is {caseify(matchx['diff'])}. Choose accordingly.",
                        matchx["ts"]
                    )
                    matchx["stage"] += 1
                elif info["user"] == matchx["matched"] and matchx["stage"] == 1 and matchx["Block 2"] in caseify(info["text"]):
                    print("BLOCK 2 GUESSED")
                    post_message(
                        client,
                        info["channel"],
                        f"<@{matchx['initiator']}> has guessed the block! The match is over and the winner is... *drumroll*",
                        matchx["ts"]
                    )
                    time.sleep(1)
                    p1 = matchx["Points"][0]
                    p2 = matchx["Points"][1]
                    if p1 > p2:
                        post_message(
                            client,
                            info["channel"],
                            f"<@{matchx['initiator']}>! Good job! Better luck next time, <@{matchx['matched']}!",
                            matchx["ts"]
                        )
                    elif p1 < p2:
                        post_message(
                            client,
                            info["channel"],
                            f"<@{matchx['matched']}>! Good job! Better luck next time, <@{matchx['initiator']}>!",
                            matchx["ts"]
                        )
                    else:
                        post_message(
                            client,
                            info["channel"],
                            f"Oh wait, it's a draw! Well then, better luck next time <@{matchx['initiator']}> AND <@{matchx['matched']}>!",
                            matchx["ts"]
                        )
                else:
                    if matchx["matched"] == info["user"] and matchx["stage"] == 0 and "[REMINDER]" not in info["text"]:
                        matchx["Points"][0] += 1
                    elif matchx["initiator"] == info["user"] and matchx["stage"] == 1 and "[REMINDER]" not in info["text"]:
                        matchx["Points"][1] += 1
                break
        #THREAD
        #post_message(client, info["channel"], "Thready :thread:", info["thread_ts"])

def post_message(client, channel, text, thread_ts=None):
    response = client.chat_postMessage(
        channel=channel,
        text=text,
        thread_ts=thread_ts
    )
    return response["ts"]

@flask_app.route("/")
def home():
    return "hello"

@flask_app.route("/ping")
def get_flask():
    return {"message": "it works!"}

def run_flask():
    flask_app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    SocketModeHandler(app, os.getenv("API_KEY")).start()
