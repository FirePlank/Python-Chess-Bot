import chess, time
import chess.polyglot
from transposition_table import TranspositionTable
import numpy as np
from evaluation import evaluation
from multiprocessing import Process, Queue

PIECE_VALUES = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330, chess.ROOK: 500, chess.QUEEN: 900}

LOWER = -1
EXACT = 0
UPPER = 1

move_time = 20
CHECKMATE = 99999998
DEPTH = CHECKMATE

STOPSEARCH = CHECKMATE + 6969

TT = TranspositionTable(10000000)

def opening_book(board, file):
    best_move = (None, 0)
    with chess.polyglot.open_reader(file) as reader:
        for entry in reader.find_all(board):
            if entry.weight>best_move[1]:
                best_move = (entry.move, entry.weight)
    return best_move

def movetime(nomoof, time):
    return (2 - min(nomoof, 10) / 10) * (time/7)

## ALGORITHMS

# starting the quiescence search code (only searches up to 4 ply extra from noisy moves)
def qsearch(board, captureMoves, alpha, beta, color, startingDepth, depth=0, maxDepth=4):
    # get stand-pat for delta pruning
    value = evaluation(board, color, startingDepth)
    # alpha-beta cutoffs
    if value >= beta:
        return beta
    if alpha < value:
        alpha = value
    if depth < maxDepth:
        for move in captureMoves:
            board.push(move)
            score = -1 * qsearch(board, board.generate_legal_captures(), -beta, -alpha, -color, depth + 1, maxDepth)
            board.pop()
            # more alpha-beta cutoffs
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
    return alpha
node = 0

def negamax(board, valid_moves, depth, alpha, beta, org):
    global save_move, save_score
    if time.time() - start_time > move_time:
        return STOPSEARCH, None
    alpha_org = alpha

    ttEntry = TT[board]
    if ttEntry and ttEntry.depth >= depth:
        if ttEntry.flag == EXACT:
            return ttEntry.val, ttEntry.move
        elif ttEntry.flag == LOWER:
            alpha = max(alpha, ttEntry.val)
        elif ttEntry.flag == UPPER:
            beta = min(beta, ttEntry.val)

    if depth == 0 or board.is_game_over():
        return qsearch(board, board.generate_legal_captures(), alpha, beta, board.turn, 0), None

    max_score = -CHECKMATE
    best_move = None
    for move in valid_moves:
        board.push(move)
        sorted = []
        ttEntry1 = TT[board]

        for move1 in board.generate_legal_moves():
            if board.is_capture(move1):
                sorted.insert(0, move1)
            else:
                sorted.append(move1)
        if ttEntry1 and ttEntry1.move is not None:
            sorted.remove(ttEntry1.move)
            sorted.insert(0, ttEntry1.move)
        score = -negamax(board, sorted, depth - 1, -beta, -alpha, board.turn)[0]
        board.pop()
        if score == STOPSEARCH:
            return STOPSEARCH, None
        if score > max_score:
            max_score = score
            best_move = move
            if org == board.turn:
                save_score = score
                save_move = move
        if max_score > alpha:
            alpha = max_score
        if alpha >= beta:
            break

    if score <= alpha_org:
        bound = UPPER
    elif score >= beta:
        bound = LOWER
    else:
        bound = EXACT

    TT.store(board, score, bound, depth, best_move if bound == (LOWER or EXACT)else None)

    return max_score, best_move

def find_best_move(board):
    global start_time, move_time, TT
    valid_moves = []
    for move in board.generate_legal_moves():
        if board.is_capture(move):
            valid_moves.insert(0, move)
        else:
            valid_moves.append(move)
    ttEntry = TT[board]
    if ttEntry and ttEntry.move is not None:
        valid_moves.remove(ttEntry.move)
        valid_moves.insert(0, ttEntry.move)

    start_time = time.time()
    best_move = None
    for CURR_DEPTH in range(1, DEPTH+1):
        # print(CURR_DEPTH)
        # print(time.time()-start_time)
        #     lenght = len(valid_moves)
        #     side = board.turn
        #     q = Queue()
        #     processes = [Process(target=negamax,
        #                          args=(
        #                              board, valid_moves[:round(lenght * 0.2)], DEPTH, -CHECKMATE - 1, CHECKMATE + 1,
        #                              (CURR_DEPTH, side), q)),
        #                  Process(target=negamax, args=(
        #                      board, valid_moves[round(lenght * 0.2):round(lenght * 0.4)], DEPTH, -CHECKMATE - 1,
        #                      CHECKMATE + 1, (CURR_DEPTH, side), q)),
        #                  Process(target=negamax, args=(
        #                      board, valid_moves[round(lenght * 0.4):round(lenght * 0.6)], DEPTH, -CHECKMATE - 1,
        #                      CHECKMATE + 1, (CURR_DEPTH, side), q)),
        #                  Process(target=negamax, args=(
        #                      board, valid_moves[round(lenght * 0.6):round(lenght * 0.8)], DEPTH, -CHECKMATE - 1,
        #                      CHECKMATE + 1, (CURR_DEPTH, side), q)),
        #                  Process(target=negamax,
        #                          args=(
        #                              board, valid_moves[round(lenght * 0.8):], DEPTH, -CHECKMATE - 1, CHECKMATE + 1,
        #                              (CURR_DEPTH, side), q))]
        #
        #     while q.empty() is False:
        #         move = q.get()
        #         if best_score < move[1]:
        #             best_move = move[0]
        #             best_score = move[1]
        #
        # else:
        score, move = negamax(board,valid_moves, CURR_DEPTH, -CHECKMATE-1, CHECKMATE+1, board.turn)
        if move:
            best_score1, best_move1 = score, move
        if score == STOPSEARCH or time.time()-start_time > move_time or score >= CHECKMATE-30:
            if save_score > best_score1:
                best_move1 = save_move
            break
    return best_move1 if best_move1 is not None else move


def main():
    global DEPTH, move_time
    board = chess.Board()
    nomoob = 0
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
            splitted = line.split()
            if splitted[1] == "fen":
                board = chess.Board(" ".join(splitted[2:8]))
                for x in splitted[9:]:
                    board.push_uci(x)
            else:
                board = chess.Board()
                for x in splitted[3:]:
                    board.push_uci(x)
        elif line.startswith("go"):
            splitted = line.split(" ")
            try:
                DEPTH = int(splitted[splitted.index("depth")+1])
            except: pass
            try:
                if board.turn and int(splitted[splitted.index("wtime")+1]) != 2147483647000:
                    move_time = movetime(nomoob, int(splitted[splitted.index("wtime")+1])/1000000+int(splitted[splitted.index("winc")+1])/1000000)
                elif int(splitted[splitted.index("btime")+1]) != 2147483647000:
                    move_time = movetime(nomoob, int(splitted[splitted.index("btime") + 1])/1000000+int(splitted[splitted.index("binc") + 1])/1000000)
            except: pass

            opening = opening_book(board, "openings.bin")
            if opening[0] is None:
                nomoob += 1
                start = time.time()
                move = find_best_move(board)
                print("bestmove", move.uci())
            else:
                print("bestmove", str(opening[0]))

        elif line == "stop":
            pass
        else:
            print("Unknown command: " + line)


main()