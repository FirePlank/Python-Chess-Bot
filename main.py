import chess
import chess.polyglot
from multiprocessing import Process, Queue

board = chess.Board()

DEPTH = 4
think_time = 5
MIN_VALUE = -999999999
MAX_VALUE = 999999999

PIECE_VALUES = {chess.PAWN: 100, chess.KNIGHT: 300, chess.BISHOP: 325, chess.ROOK: 500, chess.QUEEN: 900,
                chess.KING: 9999}
FIRST_END = True
FIRST_MIDDLE = True

PAWN_SQUARE_EVAL = [
    0, 0, 0, 0, 0, 0, 0, 0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5, 5, 10, 25, 25, 10, 5, 5,
    0, 0, 5, 20, 20, 5, 0, 0,
    5, -5, -10, 0, 0, -10, -5, 5,
    5, 10, 10, -20, -20, 10, 10, 5,
    0, 0, 0, 0, 0, 0, 0, 0
]

KNIGHT_SQUARE_EVAL = [
    -50, -30, -30, -30, -30, -30, -30, -50,
    -40, -5, 0, 0, 0, 0, -5, -40,
    -30, 0, 15, 15, 15, 15, 0, -30,
    -30, 5, 15, 30, 30, 15, 5, -30,
    -30, 5, 15, 30, 30, 15, 5, -30,
    -40, 0, 15, 15, 15, 15, 0, -40,
    -40, -5, 0, 0, 0, 0, -5, -40,
    -50, -40, -30, -30, -30, -30, -40, -50,
]

BISHOP_SQUARE_EVAL = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 10, 10, 5, 0, -10,
    -10, 5, 5, 10, 10, 5, 5, -10,
    -10, 0, 10, 10, 10, 10, 0, -10,
    -10, 10, 10, 10, 10, 10, 10, -10,
    -10, 10, 0, 0, 0, 0, 10, -10,
    -20, -10, -20, -10, -10, -20, -10, -20
]

ROOK_SQUARE_EVAL = [
    0, 0, 0, 0, 0, 0, 0, 0,
    40, 40, 40, 40, 40, 40, 40, 40,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    0, 0, 0, 10, 10, 0, 0, 0,
]

QUEEN_SQUARE_EVAL = [
    -20, -10, -10, -5, -5, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 5, 5, 5, 0, -10,
    -5, 0, 5, 15, 15, 15, 0, -5,
    0, 5, 5, 15, 15, 15, 5, 0,
    -10, 5, 10, 10, 10, 10, 0, -10,
    -10, 0, 5, 5, 5, 5, 0, -10,
    -20, -10, -10, -5, -5, -10, -10, -20
]

KING_SQUARE_EVAL = [
    -99, -99, -99, -99, -99, -99, -99, -99,
    -80, -80, -80, -80, -80, -80, -80, -80,
    -50, -50, -50, -50, -50, -50, -50, -50,
    -40, -40, -40, -50, -50, -40, -40, -40,
    -40, -40, -40, -40, -40, -40, -40, -40,
    -40, -40, -40, -40, -40, -40, -40, -40,
    5, 5, -40, -40, -40, -40, 5, 5,
    20, 20, 15, 0, 0, 0, 25, 25
]

def pawn_islands(board: chess.Board, color: bool):
    seen = False
    square = 0
    increment = 0
    islands = 1
    for x in range(8):
        for i in range(7):
            square += 8
            piece = board.piece_at(square)
            if piece is None: continue
            if piece.color == color and piece.piece_type == chess.PAWN:
                seen = True
                break
        if not seen:
            islands += 1
        seen = False
        square = increment + 1
        increment = square

    return islands


def is_open_file(board, file):
    open_file = True
    for i in range(7):
        file += 8
        piece = board.piece_at(file)
        if piece is None: continue
        if piece.piece_type == chess.PAWN:
            open_file = False
            break
    return open_file


def passed_pawn(pm, is_end_game):
    whiteYmax = [-1] * 8
    blackYmin = [8] * 8

    for key, p in pm.items():
        if p.piece_type != chess.PAWN:
            continue

        x = key & 7
        y = key >> 3

        if p.color == chess.WHITE:
            whiteYmax[x] = max(whiteYmax[x], y)
        else:
            blackYmin[x] = min(blackYmin[x], y)

    scores = [[0, 5, 15, 20, 30, 40, 75, 0], [0, 15, 30, 50, 80, 130, 210, 0]]

    score = 0

    for key, p in pm.items():
        if p.piece_type != chess.PAWN:
            continue

        x = key & 7
        y = key >> 3

        if p.color == chess.WHITE:
            left = (x > 0 and (blackYmin[x - 1] <= y or blackYmin[x - 1] == 8)) or x == 0
            front = blackYmin[x] < y or blackYmin[x] == 8
            right = (x < 7 and (blackYmin[x + 1] <= y or blackYmin[x + 1] == 8)) or x == 7

            if left and front and right:
                score += scores[is_end_game][y]

        else:
            left = (x > 0 and (whiteYmax[x - 1] >= y or whiteYmax[x - 1] == -1)) or x == 0
            front = whiteYmax[x] > y or whiteYmax[x] == -1
            right = (x < 7 and (whiteYmax[x + 1] >= y or whiteYmax[x + 1] == -1)) or x == 7

            if left and front and right:
                score -= scores[is_end_game][7 - y]

    return score


def pm_to_filemap(piece_map):
    files = [0] * (8 * 7 * 2)

    for p, piece in piece_map.items():
        files[piece.color * 8 * 7 + piece.piece_type * 8 + (p & 7)] += 1

    return files


def double_pawns(file_map):
    n = 0

    for i in range(0, 8):
        if file_map[chess.WHITE * 8 * 7 + chess.PAWN * 8 + i] >= 2:
            n += file_map[chess.WHITE * 8 * 7 + chess.PAWN * 8 + i] - 1

        if file_map[chess.BLACK * 8 * 7 + chess.PAWN * 8 + i] >= 2:
            n -= file_map[chess.BLACK * 8 * 7 + chess.PAWN * 8 + i] - 1

    return n


def is_endgame(board):
    pieces = 0
    PIECE_VALUE = {chess.KNIGHT: 300, chess.BISHOP: 325, chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 9999}
    for key in PIECE_VALUE.keys():
        pieces += len(board.pieces(key, chess.WHITE))
        pieces += len(board.pieces(key, chess.BLACK))
    moves = len(board.move_stack)
    return True if moves > 20 and pieces <= 5 else False


def count_rooks_on_open_file(file_map):
    n = 0
    for i in range(0, 8):
        if file_map[chess.WHITE * 8 * 7 + chess.PAWN * 8 + i] == 0 and file_map[chess.WHITE * 8 * 7 + chess.ROOK * 8 + i] > 0:
            n += 1

        if file_map[chess.BLACK * 8 * 7 + chess.PAWN * 8 + i] == 0 and file_map[chess.BLACK * 8 * 7 + chess.ROOK * 8 + i] > 0:
            n -= 1
    return n


def king_near_open_files(file_map, color):
    n = 0
    for i in range(0, 8):
        if file_map[color * 8 * 7 + chess.PAWN * 8 + i] == 0 and file_map[color * 8 * 7 + chess.KING * 8 + i] > 0:
            n += 2
        if file_map[color * 8 * 7 + chess.PAWN * 8 + (i - 1)] == 0 and file_map[
            color * 8 * 7 + chess.KING * 8 + i] > 0:
            n += 1
        if file_map[color * 8 * 7 + chess.PAWN * 8 + (i + 1)] == 0 and file_map[
            color * 8 * 7 + chess.KING * 8 + i] > 0:
            n += 1
    return n


def evaluation(board, maximizing_color):
    global KING_SQUARE_EVAL, FIRST_END, FIRST_MIDDLE, PIECE_VALUES

    result = board.result()
    # Checks if its checkmate
    if board.is_checkmate():
        if maximizing_color == chess.WHITE and result == "1-0":
            return 99999999999999
        elif maximizing_color == chess.WHITE and result == "0-1":
            return -99999999999999
        elif maximizing_color == chess.BLACK and result == "0-1":
            return 99999999999999
        elif maximizing_color == chess.BLACK and result == "1-0":
            return -99999999999999

    # Checks if its a draw
    if board.is_game_over() and result == "1/2-1/2":
        return 0

    endgame = is_endgame(board)
    file_map = pm_to_filemap(board.piece_map())

    # Updates square and piece evaluations if endgame and if not already done so
    if FIRST_END and endgame:
        FIRST_END = False
        KING_SQUARE_EVAL = [-50, -40, -30, -20, -20, -30, -40, -50,
                            -30, -20, -10, 0, 0, -10, -20, -30,
                            -30, -10, 20, 30, 30, 20, -10, -30,
                            -30, -10, 30, 40, 40, 30, -10, -30,
                            -30, -10, 30, 40, 40, 30, -10, -30,
                            -30, -10, 20, 30, 30, 20, -10, -30,
                            -30, -30, 0, 0, 0, 0, -30, -30,
                            -50, -30, -30, -30, -30, -30, -30, -50]

        PIECE_VALUES = {chess.PAWN: 250, chess.KNIGHT: 350, chess.BISHOP: 325, chess.ROOK: 500, chess.QUEEN: 900,
                        chess.KING: 9999}

    white_score = 0
    black_score = 0

    # Checks for bishop pair
    if str(board).count("B") >= 2:
        white_score += 30
    elif str(board).count("b") >= 2:
        black_score += 30

    # Gives points for all the pieces
    for key in PIECE_VALUES.keys():
        white_score += len(board.pieces(key, chess.WHITE)) * (PIECE_VALUES[key] * 5)
        black_score += len(board.pieces(key, chess.BLACK)) * (PIECE_VALUES[key] * 5)

    # Gives points for all the available moves
    turn = board.turn
    board.turn = True
    white_score += board.legal_moves.count()
    board.turn = False
    black_score += board.legal_moves.count()
    board.turn = turn

    # Reduces points based on the amount of pawn islands
    white_score -= (pawn_islands(board, True) * 5)
    black_score -= (pawn_islands(board, False) * 5)

    # Checks if king is safe

    # Checks if kings are on or near an open file
    if not endgame:
        white_score -= abs(king_near_open_files(file_map, chess.WHITE)) * 22
        black_score -= abs(king_near_open_files(file_map, chess.BLACK)) * 22

    # Checks if rooks are on open files
    rooks_on_open_files = count_rooks_on_open_file(file_map)
    if rooks_on_open_files < 0:
        black_score += abs(rooks_on_open_files) * 30
    else:
        white_score += abs(rooks_on_open_files) * 30

    # Checks for passed pawns
    passed_pawns = passed_pawn(board.piece_map(), endgame)
    if passed_pawns < 0:
        black_score += abs(passed_pawns)
        white_score -= abs(passed_pawns)
    else:
        black_score -= abs(passed_pawns)
        white_score += abs(passed_pawns)

    # Checks for doubled pawns
    doubled_pawns = double_pawns(file_map)
    if doubled_pawns < 0:
        black_score -= abs(doubled_pawns) * 10
    else:
        white_score -= abs(doubled_pawns) * 10

    # Gives points based on the pieces locations for white
    pieces = board.piece_map()
    for key in pieces.keys():
        if str(pieces[key]) == 'P':
            white_score += PAWN_SQUARE_EVAL[key]
        elif str(pieces[key]) == 'K':
            white_score += KNIGHT_SQUARE_EVAL[key]
        elif str(pieces[key]) == 'B':
            white_score += BISHOP_SQUARE_EVAL[key]
        elif str(pieces[key]) == 'R':
            white_score += ROOK_SQUARE_EVAL[key]
        elif str(pieces[key]) == 'Q':
            white_score += QUEEN_SQUARE_EVAL[key]
        elif str(pieces[key]) == 'K':
            white_score += KING_SQUARE_EVAL[key]

    # Gives points based on the pieces locations for black
    pieces = board.mirror().piece_map()
    for key in pieces.keys():
        if str(pieces[key]) == 'P':
            black_score += PAWN_SQUARE_EVAL[key]
        elif str(pieces[key]) == 'K':
            black_score += KNIGHT_SQUARE_EVAL[key]
        elif str(pieces[key]) == 'B':
            black_score += BISHOP_SQUARE_EVAL[key]
        elif str(pieces[key]) == 'R':
            black_score += ROOK_SQUARE_EVAL[key]
        elif str(pieces[key]) == 'Q':
            black_score += QUEEN_SQUARE_EVAL[key]
        elif str(pieces[key]) == 'K':
            black_score += KING_SQUARE_EVAL[key]

    if maximizing_color == chess.WHITE:
        return white_score - black_score
    else:
        return black_score - white_score

def negamax(board, valid_moves, depth, alpha, beta, maximizing_player, DEPTH = 4, q = None):
    max_score = -999999999

    if depth == 0:
        return evaluation(board, maximizing_player)

    for move in valid_moves:
        copy_board = board.copy()
        copy_board.push(move)
        next_moves = [*copy_board.legal_moves]

        # Move ordering
        for index, pos_move in enumerate(next_moves):
            if copy_board.is_capture(pos_move) or copy_board.is_into_check(pos_move):
                next_moves.pop(index)
                next_moves.insert(0, pos_move)

        side = chess.WHITE if maximizing_player == chess.BLACK else chess.BLACK
        score = -negamax(copy_board, next_moves, depth - 1, -beta, -alpha, side, DEPTH, q)
        if score > max_score:
            max_score = score
            if depth == DEPTH:
                q.put((move.uci(), max_score))

        if max_score > alpha:
            alpha = max_score
        if alpha >= beta:
            break

    return max_score

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