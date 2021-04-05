import chess
from evaluation import evaluation

cpdef int negamax(board, list valid_moves, int depth, alpha, beta, maximizing_player, int DEPTH=4, q=None):
    cdef int max_score = -999999999

    if depth == 0:
        return evaluation(board, maximizing_player)

    for move in valid_moves:
        copy_board = board.copy()
        copy_board.push(move)
        next_moves = [*copy_board.legal_moves]

        # Move ordering
        for index, pos_move in enumerate(next_moves):
            prev = copy_board.move_stack
            try:
                if pos_move == prev[-2] and pos_move == prev[-4] and prev[-1] == prev[-3]:
                    if evaluation(board, maximizing_player) > -600:
                        next_moves.pop(index)
                elif copy_board.is_capture(pos_move) or copy_board.is_into_check(pos_move):
                    next_moves.pop(index)
                    next_moves.insert(0, pos_move)
            except:
                if copy_board.is_capture(pos_move) or copy_board.is_into_check(pos_move):
                    next_moves.pop(index)
                    next_moves.insert(0, pos_move)

        side = chess.WHITE if maximizing_player==chess.BLACK else chess.BLACK
        score = -negamax(copy_board, next_moves, depth-1, -beta, -alpha, side, DEPTH, q)
        if score > max_score:
            max_score = score
            if depth == DEPTH:
                q.put((move.uci(), max_score))

        if max_score > alpha:
            alpha = max_score
        if alpha >= beta:
            break
    return max_score