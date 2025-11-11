"""
Tic Tac Toe Player
"""

import copy
import math

X = "X"
O = "O"
EMPTY = None


def initial_state():
    """
    Returns starting state of the board.
    """
    return [[EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY]]


def player(board):
    """
    Returns player who has the next turn on a board.
    """
    counter = 0
    for i in range(len(board)): 
        for j in range(len(board[i])):
            if(board[i][j] != EMPTY):
                counter += 1
    return O if counter % 2 == 1 else X

def actions(board):
    """
    Returns set of all possible actions (i, j) available on the board.
    """
    actions = set()
    for i in range(len(board)):
        for j in range(len(board[i])):
            if(board[i][j] == EMPTY):
                actions.add((i, j))
    return actions


def result(board, action):
    """
    Returns the board that results from making move (i, j) on the board.
    """
    # Make a deep copy of the board
    board_copy = copy.deepcopy(board)
    i, j = action
    if board_copy[i][j] != EMPTY:
        raise Exception("Invalid move: cell is not empty")
    
    # Place the corersponding variable in the corresponding location.
    player_turn = player(board_copy)
    board_copy[i][j] = player_turn
    return board_copy


def winner(board):
    """
    Returns the winner of the game, if there is one.
    """
    # Check each row
    for row in board:
        if row[0] == row[1] == row[2] != EMPTY:
            return X if row[0] == X else O
    
    # Check each column
    for j in range(len(board)):
        if board[0][j] == board[1][j] == board[2][j] != EMPTY:
            return X if board[0][j] == X else O
    
    # Check each diagonal
    if board[0][0] == board[1][1] == board[2][2] != EMPTY:
        return X if board[0][0] == X else O
    elif board[0][2] == board[1][1] == board[2][0] != EMPTY:
        return X if board[0][2] == X else O
    
    return None


def terminal(board):
    """
    Returns True if game is over, False otherwise.
    """

    # If a winner won, game is over
    if winner(board) != None:
        return True
    
    # If there are empty squares, the game is not over.
    for row in board:
        for cell in row:
            if cell == EMPTY:
                return False
    return True

# Receive a terminal board. If X wins, return 1. If O wins, return -1. Tie return 0
def utility(board):
    
    if winner(board) == X:
        return 1
    elif winner(board) == O:
        return -1
    return 0

def minimax(board):
    if terminal(board):
        return None
    # First figure out whose turn it is
    # based on that, you are trying to maximize/minimize. X winning = 1, O winning = -1. Thus, x will try to maximize, while O minimizes.
    turn = player(board)

    # If it's X's turn, we try to maximize our result value based on all the possible moves available.
    # We assign a utility to each of the possible actions based on the minimum values 
    # (since after the action, it is the O's turn and it will try to minimize)
    if turn == X:
        val = -math.inf
        best_action = None
        for action in actions(board):
            result_val = min_value(result(board, action))
            if result_val > val:
                best_action = action
                val = result_val
        return best_action
    #we do the reverse logic for O's turn
    elif turn == O:
        val = math.inf
        best_action = None
        for action in actions(board):
            result_val = max_value(result(board, action))
            #choose the smallest value. O is trying to minimize
            if result_val < val:
                best_action = action
                val = result_val
        return best_action

# Gets the minimum value of all the maximum values after that action takes place
def min_value(board):
    if terminal(board):
        return utility(board)
    
    min_val = math.inf
    for action in actions(board):
        min_val = min(min_val, max_value(result(board, action)))
    return min_val

    
def max_value(board):
    if terminal(board):
        return utility(board)
    
    max_val = -math.inf
    # Looks at all next possible future boards, and determine what O (the minimizer) will do. Choose the max from the minimum utilities of each board
    for action in actions(board):
        max_val = max(max_val, min_value(result(board, action)))
    return max_val
