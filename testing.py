import chess, time
import chess.engine
import chess.polyglot
from evaluation import evaluation
from main import main
PIECE_VALUES = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330, chess.ROOK: 500, chess.QUEEN: 900}
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
board = chess.Board()
board.push_uci("a2a4")
# while not board.is_game_over():
#     start = time.time()
#     result = Engine.play(board, chess.engine.Limit(depth=4))
#     board.push(result.move)
#     print(board)
#     # print(f"Time taken: {time.time()-start}")

# start = time.time()
# for i in range(1000):
#     thing = str(board.attackers(True, chess.G4)).replace(" ","")
#     for i in range(thing.count("1")):
#         find = thing.find("1")
#         if board.piece_type_at(find) == chess.PAWN:
#             print("Pawn attacks")
#             break
#         else:
#             thing = thing[:find] + "." + thing[find:]
def movetime(nomoof, time):
    return (2 - min(nomoof, 10) / 10) * (time/7)


print(movetime(4, 60))
# start = time.time()
# for i in range(1000000):
#     t = [1,2,3,4,5,6,7,8,8]
#     t.remove(6)
#     t.insert(0, 6)
# print(time.time()-start)