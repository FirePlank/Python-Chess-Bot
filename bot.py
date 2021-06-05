import json
import asyncio
import time

import chess
import chess.engine
from termcolor import cprint

import lichess

BASE_URL = "https://lichess.org"
TOKEN = "kTAA8rwMEoYNNAc3"  # Token for lichess

import os
import stat

Engine = chess.engine.SimpleEngine.popen_uci('main.cmd')

LOG = False
COLOR = False

GAME_ONGOING = False


def info(*why):
    if COLOR:
        cprint('Info: ' + ' '.join(map(str, why)), 'blue')
    else:
        print('Info: ' + ' '.join(map(str, why)))


def warn(*why):
    if COLOR:
        cprint('Warning: ' + ' '.join(map(str, why)), 'yellow')
    else:
        print('Warning: ' + ' '.join(map(str, why)))


def log(*why):
    if LOG:
        print(' '.join(map(str, why)))


async def event_stream(li: lichess.Lichess):
    global first_time, GAME_ONGOING
    game_threads = []

    try:
        info("Logged onto lichess.")

        for line in li.get_event_stream().iter_lines():
            if line:
                event = json.loads(line.decode('utf-8'))
                log("Event:", event)
                if event["type"] == "challenge":
                    challenge = event["challenge"]
                    if GAME_ONGOING:
                        li.decline_challenge(challenge["id"], "Sorry, I'm currently in a game right now and I can only play one at a time. This will hopefully soon change!")

                    elif challenge["variant"]["name"] != "Standard" and challenge["variant"]["name"] != "From Position":
                        li.decline_challenge(challenge["id"], "Sorry, I only accept challenges to the standard variant.")
                        info(f"Declined challenge {challenge['id']} ({challenge['url']}) from {challenge['challenger']['name']} ({challenge['challenger']['rating']})")
                    else:
                        GAME_ONGOING = True
                        li.accept_challenge(challenge["id"])
                        try:li.chat(challenge["id"], "player", "Hi! It's brave for you to challenge me. Let's see if you've got what it takes to beat me. glhf :)")
                        except:pass
                        info(f"Accepted challenge {challenge['id']} ({challenge['url']}) from {challenge['challenger']['name']} ({challenge['challenger']['rating']})")

                if event["type"] == "gameStart":
                    info("Game started: " + event['game']['id'])
                    k = asyncio.create_task(game_stream(li, event['game']['id']))
                    game_threads.append(k)
                    await k

    except KeyboardInterrupt:
        return game_threads


async def game_stream(li: lichess.Lichess, game_id: str):
    global first_time, GAME_ONGOING, org_fen
    org_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    print("START")
    is_white = True

    try:
        for line in li.get_game_stream(game_id).iter_lines():
            if line:
                event = json.loads(line.decode('utf-8'))
                log("Game Event:", event)

                if event["type"] == "gameFull":
    #                 info(f"""Game data for game {event['id']}:
    # - Rated: {event['rated']}
    # - Variant: {event['variant']['name']}
    # - Speed: {event['speed']}
    # - White: {event['white']['name']}({event['white']['rating']})
    # - Black: {event['black']['name']}({event['black']['rating']})""")
                    try:
                        org_fen = event['initialFen']
                    except:
                        pass
                    is_white = event["white"]["id"] == li.get_profile()["id"]
                    # info(f"Playing as white: {is_white}")

                    event = event["state"]
                    event["type"] = "gameState"

                if event["type"] == "gameState":
                    # info(f"""Game state change for game {game_id}:
    # - Moves:
    # {event['moves']}
    # - Status: {event['status']}""")

                    # Record moves
                    board = chess.Board(fen=org_fen)
                    moves = [w for w in event['moves'].strip().split(" ") if w]

                    # info(f"White's move: {len(moves) % 2 == 0 and is_white}")
                    # info(f"Black's move: {len(moves) % 2 != 0 and not is_white}")
                    # info(len(moves) % 2 == 0)

                    if (len(moves) % 2 == 0 and is_white) or (len(moves) % 2 != 0 and not is_white):
                        if event["status"] == "started":
                            for move in moves:
                                if 3 < len(move) < 6:
                                    board.push(chess.Move.from_uci(move))

                            # Play move
                            start = time.time()
                            try:
                                result = Engine.play(board, chess.engine.Limit(white_clock=event["wtime"], black_clock=event["btime"], white_inc=event["winc"], black_inc=event["binc"]))
                            except chess.engine.EngineError:
                                li.resign(game_id)
                            info("Think time taken: " + str(round(time.time()-start, 2)))
                            try:
                                li.make_move(game_id, result.move)
                            except:
                                info(f"Move {str(result.move.uci())} was unable to be sent to the server.")
                        else:
                            info(
                                f"Game {game_id} ended due to {event['status']}."
                                f"{' Winner: ' + event['winner'] if 'winner' in event else ''}")
                            GAME_ONGOING = False
                            return
    except KeyboardInterrupt:
        return


async def main():
    lich = lichess.Lichess(TOKEN, BASE_URL, "0.0.1")

    game_threads = await asyncio.create_task(event_stream(lich))
    warn("exiting bot.")
    print(game_threads)
    exit(0)
    return


if __name__ == '__main__':
    asyncio.run(main())