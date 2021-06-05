import chess
import chess.polyglot

PIECE_VALUES = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330, chess.ROOK: 500, chess.QUEEN: 900}

CHECKMATE = 999999998
FIRST_END = True
ending = False

PAWN_SQUARE_EVAL = [
 0,  0,  0,  0,  0,  0,  0,  0,
50, 50, 50, 50, 50, 50, 50, 50,
10, 10, 20, 30, 30, 20, 10, 10,
 5,  5, 10, 25, 25, 10,  5,  5,
 0,  0,  0, 20, 20,  0,  0,  0,
 5, -5,-10,  0,  0,-10, -5,  5,
 5, 10, 10,-20,-20, 10, 10,  5,
 0,  0,  0,  0,  0,  0,  0,  0
]

KNIGHT_SQUARE_EVAL = [
-50,-40,-30,-30,-30,-30,-40,-50,
-40,-20,  0,  0,  0,  0,-20,-40,
-30,  0, 10, 15, 15, 10,  0,-30,
-30,  5, 15, 20, 20, 15,  5,-30,
-30,  0, 15, 20, 20, 15,  0,-30,
-30,  5, 10, 15, 15, 10,  5,-30,
-40,-20,  0,  5,  5,  0,-20,-40,
-50,-40,-30,-30,-30,-30,-40,-50,
]

BISHOP_SQUARE_EVAL = [
-20,-10,-10,-10,-10,-10,-10,-20,
-10,  0,  0,  0,  0,  0,  0,-10,
-10,  0,  5, 10, 10,  5,  0,-10,
-10,  5,  5, 10, 10,  5,  5,-10,
-10,  0, 10, 10, 10, 10,  0,-10,
-10, 10, 10, 10, 10, 10, 10,-10,
-10,  5,  0,  0,  0,  0,  5,-10,
-20,-10,-10,-10,-10,-10,-10,-20,
]

ROOK_SQUARE_EVAL = [
    0, 0, 0, 0, 0, 0, 0, 0,
    5, 10, 10, 10, 10, 10, 10, 5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    0, 0, 0, 5, 5, 0, 0, 0
]

QUEEN_SQUARE_EVAL = [
-20,-10,-10, -5, -5,-10,-10,-20,
-10,  0,  0,  0,  0,  0,  0,-10,
-10,  0,  5,  5,  5,  5,  0,-10,
 -5,  0,  5,  5,  5,  5,  0, -5,
  0,  0,  5,  5,  5,  5,  0, -5,
-10,  5,  5,  5,  5,  5,  0,-10,
-10,  0,  5,  0,  0,  0,  0,-10,
-20,-10,-10, -5, -5,-10,-10,-20
]

KING_SQUARE_EVAL = [
-30,-40,-40,-50,-50,-40,-40,-30,
-30,-40,-40,-50,-50,-40,-40,-30,
-30,-40,-40,-50,-50,-40,-40,-30,
-30,-40,-40,-50,-50,-40,-40,-30,
-20,-30,-30,-40,-40,-30,-30,-20,
-10,-20,-20,-20,-20,-20,-20,-10,
 20, 20,  0,  0,  0,  0, 20, 20,
 20, 30, 10,  0,  0, 10, 30, 20
]

def passed_pawn(pm, is_end_game=True):
    whiteYmax = [ -1 ] * 8
    blackYmin = [ 8 ] * 8

    for key, p in pm.items():
        if p.piece_type != chess.PAWN:
            continue

        x = key & 7
        y = key >> 3

        if p.color == chess.WHITE:
            whiteYmax[x] = max(whiteYmax[x], y)
        else:
            blackYmin[x] = min(blackYmin[x], y)

    scores = [ [ 0, 15, 30, 40, 50, 60, 90, 0 ], [ 0, 15, 30, 50, 80, 130, 210, 0 ] ]

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
    files = [ 0 ] * (8 * 7 * 2)

    for p, piece in piece_map.items():
        files[piece.color * 8 * 7 + piece.piece_type * 8 + (p & 7)] += 1

    return files

def is_endgame(board):
    pieces = 0
    for key in PIECE_VALUES.keys():
        if key != chess.QUEEN:
            pieces += len(board.pieces(key, chess.WHITE))
            pieces += len(board.pieces(key, chess.BLACK))
        else:
            pieces += len(board.pieces(key, chess.WHITE))*2
            pieces += len(board.pieces(key, chess.BLACK))*2
    return pieces<=5

def force_king_to_corner_eval(board, maximizing_color):
    result = board.result()
    if board.is_game_over():
        if maximizing_color and result == "1-0":
            return CHECKMATE
        elif not maximizing_color and result == "0-1":
            return CHECKMATE
        else:
            return -CHECKMATE-100
    evaluation = 0
    file_map = pm_to_filemap(board.piece_map())
    other = False
    if maximizing_color:
        for i in range(0, 8):
            if file_map[chess.BLACK * 8 * 7 + chess.KING * 8 + i] == 1:
                opponent_king_file = i+1
                opponent_king_rank = board.king(False)//8
                if other:break
                other = True
            if file_map[chess.WHITE * 8 * 7 + chess.KING * 8 + i] == 1:
                friendly_king_file = i+1
                friendly_king_rank = board.king(True)//8
                if other:break
                other = True
    else:
        for i in range(0, 8):
            if file_map[chess.WHITE * 8 * 7 + chess.KING * 8 + i] == 1:
                opponent_king_file = i+1
                opponent_king_rank = board.king(True)//8
                if other:break
                other = True
            if file_map[chess.BLACK * 8 * 7 + chess.KING * 8 + i] == 1:
                friendly_king_file = i+1
                friendly_king_rank = board.king(False)//8
                if other:break
                other = True

    dist_to_center_file = max(3-opponent_king_file, opponent_king_file-4)
    dist_to_center_rank = max(3 - opponent_king_rank, opponent_king_rank - 4)
    dist_from_center = dist_to_center_file + dist_to_center_rank
    evaluation += dist_from_center

    dist_between_files = abs(friendly_king_file-opponent_king_file)
    dist_between_ranks = abs(friendly_king_rank-opponent_king_rank)
    dist_between_kings = dist_between_files+dist_between_ranks
    evaluation += 14 - dist_between_kings

    return evaluation * 10

def evaluation(board, maximizing_color, depth):
    global KING_SQUARE_EVAL, FIRST_END, FIRST_MIDDLE, PIECE_VALUES, ending
    if ending and maximizing_color == board.turn:
        return force_king_to_corner_eval(board, maximizing_color)

    # Checks if its checkmate instantly
    result = board.result()
    if board.is_game_over(claim_draw=True):
        if maximizing_color and result == "1-0":
            return CHECKMATE-depth
        elif maximizing_color and result == "0-1":
            return -CHECKMATE+depth
        elif not maximizing_color and result == "0-1":
            return CHECKMATE-depth
        elif not maximizing_color and result == "1-0":
            return -CHECKMATE+depth
        else:
            return 0

    # Updates square and piece evaluations if endgame and if not already done so
    if FIRST_END and is_endgame(board):
        FIRST_END = False
        KING_SQUARE_EVAL = [-50,-40,-30,-20,-20,-30,-40,-50,
                            -30,-20,-10,  0,  0,-10,-20,-30,
                            -30,-10, 20, 30, 30, 20,-10,-30,
                            -30,-10, 30, 40, 40, 30,-10,-30,
                            -30,-10, 30, 40, 40, 30,-10,-30,
                            -30,-10, 20, 30, 30, 20,-10,-30,
                            -30,-30,  0,  0,  0,  0,-30,-30,
                            -50,-30,-30,-30,-30,-30,-30,-50]
        PIECE_VALUES = {chess.PAWN: 200, chess.KNIGHT: 320, chess.BISHOP: 330, chess.ROOK: 500, chess.QUEEN: 900}
    white_score = 0
    black_score = 0

    # Gives points for all the pieces
    for key, key1 in PIECE_VALUES.items():
        white_score += len(board.pieces(key, chess.WHITE)) * key1
        black_score += len(board.pieces(key, chess.BLACK)) * key1

    if maximizing_color and black_score == 0:
        thing = 0
        piece_map = board.piece_map()
        for i in piece_map:
            if piece_map[i].piece_type == chess.QUEEN or piece_map[i].piece_type == chess.ROOK:
                ending = True
                return force_king_to_corner_eval(board, maximizing_color)
            elif piece_map[i].piece_type == chess.BISHOP:
                thing += 1
                if thing >= 2:
                    ending = True
                    return force_king_to_corner_eval(board, maximizing_color)

    elif not maximizing_color and white_score == 0:
        thing = 0
        piece_map = board.piece_map()
        for i in piece_map:
            if piece_map[i].piece_type == chess.QUEEN or piece_map[i].piece_type == chess.ROOK:
                ending = True
                return force_king_to_corner_eval(board, maximizing_color)
            elif piece_map[i].piece_type == chess.BISHOP:
                thing += 1
                if thing >= 2:
                    ending = True
                    return force_king_to_corner_eval(board, maximizing_color)

    # Gives points for all the available moves
    if board.turn:
        white_score+=board.legal_moves.count()*1.25
        board.turn = False
        black_score+=board.legal_moves.count()*1.25
        board.turn = True
    else:
        black_score += board.legal_moves.count()*1.25
        board.turn = True
        white_score += board.legal_moves.count()*1.25
        board.turn = False

    # TODO Check if king is safe

    # Checks for passed pawns
    if is_endgame(board):
        passed_pawns = passed_pawn(board.piece_map())
        if passed_pawns < 0:
            black_score += abs(passed_pawns)
            white_score -= abs(passed_pawns)
        else:
            black_score -= abs(passed_pawns)
            white_score += abs(passed_pawns)

    # Gives points based on the pieces locations for white and black
    for key in board.piece_map().items():
        key1 = str(key[1])
        if key1 == 'P':
            white_score += PAWN_SQUARE_EVAL[key[0]]
        elif key1 == 'p':
            black_score += PAWN_SQUARE_EVAL[64 - 8 * (key[0] >> 3) + key[0] % 8 - 8]

        elif key1 == 'N':
            white_score += KNIGHT_SQUARE_EVAL[key[0]]
        elif key1 == 'n':
            black_score += KNIGHT_SQUARE_EVAL[64 - 8 * (key[0] >> 3) + key[0] % 8 - 8]

        elif key1 == 'B':
            white_score += BISHOP_SQUARE_EVAL[key[0]]
        elif key1 == 'b':
            black_score += BISHOP_SQUARE_EVAL[64 - 8 * (key[0] >> 3) + key[0] % 8 - 8]

        elif key1 == 'R':
            white_score += ROOK_SQUARE_EVAL[key[0]]
        elif key1 == 'r':
            black_score += ROOK_SQUARE_EVAL[64 - 8 * (key[0] >> 3) + key[0] % 8 - 8]

        elif key1 == 'Q':
            white_score += QUEEN_SQUARE_EVAL[key[0]]
        elif key1 == 'q':
            black_score += QUEEN_SQUARE_EVAL[64 - 8 * (key[0] >> 3) + key[0] % 8 - 8]

        elif key1 == 'K':
            white_score += KING_SQUARE_EVAL[key[0]]
        else:
            black_score += KING_SQUARE_EVAL[64 - 8 * (key[0] >> 3) + key[0] % 8 - 8]

    if maximizing_color == chess.WHITE:
        return white_score - black_score
    else:
        return black_score - white_score
