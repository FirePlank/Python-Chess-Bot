import chess
import chess.polyglot
from multiprocessing import Process, Queue
from evaluation import evaluation
from algorithm import negamax

board = chess.Board()

DEPTH = 4
think_time = 5
MIN_VALUE = -999999999
MAX_VALUE = 999999999

def opening_book(board, file):
    best_move = (None, 0)
    with chess.polyglot.open_reader(file) as reader:
        for entry in reader.find_all(board):
            if entry.weight>best_move[1]:
                best_move = (entry.move, entry.weight)
    return best_move

def find_best_move(board, valid_moves):
    global nextMove, hash_table
    nextMove = None

    side = chess.WHITE if board.turn else chess.BLACK
    lenght = len(valid_moves)

    # Move ordering
    for index, move in enumerate(valid_moves):
        prev = board.move_stack
        try:
            if move == prev[-2] and move == prev[-4] and prev[-1] == prev[-3]:
                if evaluation(board, side) > -600:
                    valid_moves.pop(index)
            elif board.is_capture(move) or board.is_into_check(move):
                valid_moves.pop(index)
                valid_moves.insert(0, move)
        except:
            if board.is_capture(move) or board.is_into_check(move):
                valid_moves.pop(index)
                valid_moves.insert(0, move)

    q = Queue()
    processes = [Process(target=negamax, args=(board, valid_moves[:round(lenght*0.2)], DEPTH, MIN_VALUE, MAX_VALUE, side, DEPTH, q)),
                 Process(target=negamax, args=(board, valid_moves[round(lenght*0.2):round(lenght*0.4)], DEPTH, MIN_VALUE, MAX_VALUE, side, DEPTH, q)),
                 Process(target=negamax, args=(board, valid_moves[round(lenght*0.4):round(lenght*0.6)], DEPTH, MIN_VALUE, MAX_VALUE, side, DEPTH, q)),
                 Process(target=negamax, args=(board, valid_moves[round(lenght*0.6):round(lenght*0.8)], DEPTH, MIN_VALUE, MAX_VALUE, side, DEPTH, q)),
                 Process(target=negamax, args=(board, valid_moves[round(lenght*0.8):], DEPTH, MIN_VALUE, MAX_VALUE, side, DEPTH, q))]
    for process in processes:
        process.start()
    for process in processes:
        process.join()

    best_move = ("e2e4", MIN_VALUE)
    while q.empty() is False:
        move = q.get()
        if move[1]>best_move[1]:best_move=move
    return best_move[0]

def main():
    global DEPTH, think_time
    board = chess.Board()
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

            while 1:
                opening = opening_book(board, "openings.bin")
                if opening[0] is None:
                    toMove = find_best_move(board, [*board.legal_moves])
                    if toMove is None:
                        print("bestmove", toMove)
                        break
                    try:
                        board.push_uci(toMove)
                    except:
                        DEPTH-=1
                        continue
                    print("bestmove", toMove)
                else:
                    board.push(opening[0])
                    print("bestmove", str(opening[0]))
                break

        elif line == "stop":
            toMove = find_best_move(board, [*board.legal_moves])
            board.push_uci(toMove)
            print("bestmove", toMove)
        else:
            print("Unknown command: " + line)


if __name__ == '__main__':
    main()