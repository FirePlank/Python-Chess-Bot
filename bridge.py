import chess
import chess.polyglot
import chess.engine

import os
import stat

st = os.stat('/app/main.exe')
os.chmod('/app/main.exe', st.st_mode | stat.S_IEXEC)

Engine = chess.engine.SimpleEngine.popen_uci('/app/main.exe')

def opening_book(board, file):
    best_move = (None, 0)
    with chess.polyglot.open_reader(file) as reader:
        for entry in reader.find_all(board):
            if entry.weight>best_move[1]:
                best_move = (entry.move, entry.weight)
    return best_move

while True:
    line = input()
    if line == "quit":
        break
    elif line == "uci":
        print("id name FirefullBot")
        print("id author FirefullBot's developer")
        print("uciok")
    elif line == "isready":
        print("readyok")
    elif line == "ucinewgame":
        board = chess.Board()
        done_opening = False
    elif line.startswith("position"):
        board = chess.Board()
        for x in line.split()[3:]:
            board.push_uci(x)
    elif line.startswith("go"):
        splitted = line.split(" ")
        try:
            DEPTH = int(splitted[splitted.index("depth")+1])
        except: pass
        try:
            if DEPTH>2:
                white_time = int(splitted[splitted.index("wtime")+1])/1000000
                black_time = int(splitted[splitted.index("btime")+1])/1000000
                white_inc = int(splitted[splitted.index("winc")+1])/1000000
                black_inc = int(splitted[splitted.index("binc") + 1]) / 1000000
        
                think_time = (white_time+white_inc)/30 if board.turn else (black_time+black_inc)/30
                if white_time + white_inc < 5 and board.turn: DEPTH = 1
                elif white_time + white_inc < 25 and board.turn: DEPTH = 2
                elif white_time + white_inc < 45 and board.turn: DEPTH = 3
                elif black_time + black_inc < 5 and not board.turn: DEPTH = 1
                elif black_time + black_inc < 25 and not board.turn: DEPTH = 2
                elif black_time + black_inc < 45 and not board.turn: DEPTH = 3
        except: pass

        if not done_opening:
            opening = opening_book(board, "openings.bin")
            if opening[0] is not None:
                print("bestmove", str(opening[0]))
                continue
            else:
                done_opening = True

        result = Engine.play(board, chess.engine.Limit(depth=DEPTH))
        print("bestmove", result.move.uci())

    else:
        print("Unknown command: " + line)