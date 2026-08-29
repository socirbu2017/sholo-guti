from functools import lru_cache

class SholoGutiEngine:
    def __init__(self):
        # 20 Straight lines defining board paths
        self.STRAIGHT_LINES = [
            [0, 1, 2, 3, 4], [5, 6, 7, 8, 9], [10, 11, 12, 13, 14],
            [15, 16, 17, 18, 19], [20, 21, 22, 23, 24],
            [0, 5, 10, 15, 20], [1, 6, 11, 16, 21],
            [26, 29, 2, 7, 12, 17, 22, 32, 35],
            [3, 8, 13, 18, 23], [4, 9, 14, 19, 24],
            [0, 6, 12, 18, 24], [4, 8, 12, 16, 20],
            [25, 26, 27], [28, 29, 30], [31, 32, 33], [34, 35, 36],
            [25, 28, 2, 8, 14], [27, 30, 2, 6, 10],
            [34, 31, 22, 18, 14], [36, 33, 22, 16, 10]
        ]

        # Strategic Node Weights
        self.POSITION_WEIGHTS = {
            12: 15, 7: 10, 17: 10, 11: 10, 13: 10,
            16: 8, 18: 8, 6: 8, 8: 8, 2: 5, 22: 5, 10: 5, 14: 5,
            0: 2, 4: 2, 20: 2, 24: 2, 25: 3, 27: 3, 34: 3, 36: 3
        }
        
        # Transposition cache for fast search
        self.transposition_table = {}

    def _get_chain_captures(self, board, curr_pos, player, visited_caps, path, all_captures):
        found_further_jump = False
        opponent = 2 if player == 1 else 1

        for line in self.STRAIGHT_LINES:
            if curr_pos in line:
                idx = line.index(curr_pos)
                # Forward Jump
                if idx + 2 < len(line):
                    nxt, landing = line[idx + 1], line[idx + 2]
                    if nxt not in visited_caps and board[nxt] == opponent and board[landing] == 0:
                        found_further_jump = True
                        nb = list(board)
                        nb[curr_pos], nb[nxt], nb[landing] = 0, 0, player
                        self._get_chain_captures(tuple(nb), landing, player, visited_caps + [nxt], path + [landing], all_captures)
                # Backward Jump
                if idx - 2 >= 0:
                    nxt, landing = line[idx - 1], line[idx - 2]
                    if nxt not in visited_caps and board[nxt] == opponent and board[landing] == 0:
                        found_further_jump = True
                        nb = list(board)
                        nb[curr_pos], nb[nxt], nb[landing] = 0, 0, player
                        self._get_chain_captures(tuple(nb), landing, player, visited_caps + [nxt], path + [landing], all_captures)

        if not found_further_jump and len(visited_caps) > 0:
            all_captures.append((path[0], curr_pos, tuple(visited_caps), list(path)))

    def get_valid_moves(self, board, player, force_capture=False):
        captures = []
        normal_moves = []
        board_tuple = tuple(board)

        # 1. Calculate Captures
        for src in range(37):
            if board[src] == player:
                self._get_chain_captures(board_tuple, src, player, [], [src], captures)

        unique_captures = list({(c[0], c[1], c[2]): c for c in captures}.values())

        # If force_capture is explicitly requested as True
        if force_capture and unique_captures:
            return unique_captures

        # 2. Calculate Normal Moves
        for line in self.STRAIGHT_LINES:
            for i in range(len(line) - 1):
                u, v = line[i], line[i+1]
                if board[u] == player and board[v] == 0:
                    normal_moves.append((u, v, (), [u, v]))
                elif board[v] == player and board[u] == 0:
                    normal_moves.append((v, u, (), [v, u]))

        unique_normals = list({(m[0], m[1]): m for m in normal_moves}.values())

        # Return BOTH captures and normal moves so players have complete freedom
        return unique_captures + unique_normals

    def evaluate_board(self, board, player):
        opponent = 2 if player == 1 else 1

        my_pieces = board.count(player)
        opp_pieces = board.count(opponent)
        material_score = (my_pieces - opp_pieces) * 5000

        my_pos_score = sum(self.POSITION_WEIGHTS.get(i, 2) for i, cell in enumerate(board) if cell == player)
        opp_pos_score = sum(self.POSITION_WEIGHTS.get(i, 2) for i, cell in enumerate(board) if cell == opponent)

        my_moves = self.get_valid_moves(board, player, force_capture=False)
        opp_moves = self.get_valid_moves(board, opponent, force_capture=False)

        my_caps = sum(1 for m in my_moves if len(m[2]) > 0)
        opp_caps = sum(1 for m in opp_moves if len(m[2]) > 0)

        threat_score = (my_caps * 1500) - (opp_caps * 3000)
        mobility_score = (len(my_moves) - len(opp_moves)) * 15

        return material_score + threat_score + mobility_score + (my_pos_score - opp_pos_score)

    def minimax(self, board, depth, alpha, beta, maximizing_player, player):
        state_key = (tuple(board), depth, maximizing_player, alpha, beta)
        if state_key in self.transposition_table:
            return self.transposition_table[state_key]

        if depth == 0:
            eval_val = self.evaluate_board(board, player)
            return eval_val, None

        current_turn = player if maximizing_player else (2 if player == 1 else 1)
        valid_moves = self.get_valid_moves(board, current_turn, force_capture=False)

        if not valid_moves:
            return (-50000 if maximizing_player else 50000), None

        valid_moves.sort(key=lambda m: (len(m[2]), self.POSITION_WEIGHTS.get(m[1], 2)), reverse=True)
        best_move = valid_moves[0]

        if maximizing_player:
            max_eval = -float('inf')
            for move in valid_moves:
                src, dst, captured, _ = move
                temp_board = list(board)
                temp_board[src] = 0
                temp_board[dst] = current_turn
                for cap in captured:
                    temp_board[cap] = 0

                eval_val, _ = self.minimax(temp_board, depth - 1, alpha, beta, False, player)
                if eval_val > max_eval:
                    max_eval = eval_val
                    best_move = move
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            self.transposition_table[state_key] = (max_eval, best_move)
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in valid_moves:
                src, dst, captured, _ = move
                temp_board = list(board)
                temp_board[src] = 0
                temp_board[dst] = current_turn
                for cap in captured:
                    temp_board[cap] = 0

                eval_val, _ = self.minimax(temp_board, depth - 1, alpha, beta, True, player)
                if eval_val < min_eval:
                    min_eval = eval_val
                    best_move = move
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            self.transposition_table[state_key] = (min_eval, best_move)
            return min_eval, best_move

    def get_best_move(self, board, player=1, depth=6):
        self.transposition_table.clear()
        _, move = self.minimax(board, depth, -float('inf'), float('inf'), True, player)
        return move

