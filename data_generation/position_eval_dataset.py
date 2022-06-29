import chess
import stockfish
import random
import numpy as np
import multiprocessing



stockfish = stockfish.Stockfish(path="stockfish_14.1_win_x64_avx2\stockfish_14.1_win_x64_avx2.exe")
stockfish.set_depth(1)


squares_index = {
  'a': 0,
  'b': 1,
  'c': 2,
  'd': 3,
  'e': 4,
  'f': 5,
  'g': 6,
  'h': 7
}

def square_to_index(square):
  letter = chess.square_name(square)
  return 8 - int(letter[1]), squares_index[letter[0]]

def split_dims(board):
  board3d = np.zeros((14, 8, 8), dtype=np.int8)

  for piece in chess.PIECE_TYPES:
    for square in board.pieces(piece, chess.WHITE):
      idx = np.unravel_index(square, (8, 8))
      board3d[piece - 1][7 - idx[0]][idx[1]] = 1
    for square in board.pieces(piece, chess.BLACK):
      idx = np.unravel_index(square, (8, 8))
      board3d[piece + 5][7 - idx[0]][idx[1]] = 1


  aux = board.turn
  board.turn = chess.WHITE
  for move in board.legal_moves:
      i, j = square_to_index(move.to_square)
      board3d[12][i][j] = 1
  board.turn = chess.BLACK
  for move in board.legal_moves:
      i, j = square_to_index(move.to_square)
      board3d[13][i][j] = 1
  board.turn = aux

  return board3d




def random_board(max_depth=150):
  board = chess.Board()
  depth = random.randrange(0, max_depth)
  for _ in range(depth):
    all_moves = list(board.legal_moves)
    random_move = random.choice(all_moves)
    board.push(random_move)
    if board.is_game_over():
        board.pop()
        break
  return board


def stockfish_eval(board):
        board_fen = board.fen()
        stockfish.set_fen_position(board_fen)
        eval = stockfish.get_evaluation()
        while eval['type'] == 'mate':
                board.pop()
                board_fen = board.fen()
                stockfish.set_fen_position(board_fen)
                eval = stockfish.get_evaluation()
        eval = eval["value"]
        return board, eval


def generate_dataset():
    board_list = []
    eval_list = []
    i = 1
    for _ in range(100):
        board = random_board()
        board, eval = stockfish_eval(board)
        board = split_dims(board)
        board_list.append(board)
        eval_list.append(eval)
        print(i)
        i = i+1

    return np.array(board_list), np.array(eval_list)

def save_dataset(depth, thread):
    board, eval = generate_dataset()
    data = {'board': board,
            'eval': eval}
    np.savez("dataset_depth_{}_{}.npz".format(depth, thread), x=data['board'], y=data['eval'])

def go():
    i = 1
    while i < 6:
        stockfish.set_depth(i)
        print("depth set to: ", i)
        processes=[]
        j=1
        while j <4 :
            t = multiprocessing.Process(target=save_dataset, args=(i, j))
            processes.append(t)
            t.start()
            print("process{}started".format(j))
            j = j + 1

        for thread in processes:
            thread.join()
        i = i+1

if __name__ == '__main__':
    go()
