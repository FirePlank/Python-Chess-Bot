import chess
import chess.polyglot

class Entry:
    def __init__(self,val, flag, depth, move):
        self.val = val
        self.flag = flag
        self.depth = depth
        self.move = move

class TranspositionTable:
    def __init__(self, size):
        self.size = size
        self.basic_cache = {}

    def __getitem__(self, position):
        return self.basic_cache.get(chess.polyglot.zobrist_hash(position), None)

    def store(self, position, value, flag, depth, move):
        self.basic_cache[chess.polyglot.zobrist_hash(position)] = Entry(value, flag, depth, move)
        return True

    def empty_cache(self):
        self.basic_cache = {}