"""
Sholo Guti Game Engine

Implements game logic, move validation, and AI using minimax algorithm with alpha-beta pruning.
The engine manages board state evaluation and optimal move calculation.
"""

from typing import List, Tuple, Optional, Dict


class SholoGutiEngine:
    """
    Game engine for Sholo Guti board game.
    
    Provides move generation, board evaluation, and AI move calculation using
    minimax algorithm with alpha-beta pruning and transposition table caching.
    """

    def __init__(self):
        """Initialize the game engine with board configuration and evaluation weights."""
        # 20 Straight lines defining board paths and valid movement directions
        self.STRAIGHT_LINES: List[List[int]] = [
            # Horizontal rows
            [0, 1, 2, 3, 4], 
            [5, 6, 7, 8, 9], 
            [10, 11, 12, 13, 14],
            [15, 16, 17, 18, 19], 
            [20, 21, 22, 23, 24],
            
            # Vertical columns
            [0, 5, 10, 15, 20], 
            [1, 6, 11, 16, 21],
            [26, 29, 2, 7, 12, 17, 22, 32, 35],
            [3, 8, 13, 18, 23], 
            [4, 9, 14, 19, 24],
            
            # Diagonals
            [0, 6, 12, 18, 24], 
            [4, 8, 12, 16, 20],
            
            # Corner lines
            [25, 26, 27], 
            [28, 29, 30], 
            [31, 32, 33], 
            [34, 35, 36],
            [25, 28, 2, 8, 14], 
            [27, 30, 2, 6, 10],
            [34, 31, 22, 18, 14], 
            [36, 33, 22, 16, 10]
        ]

        # Strategic position weights for board evaluation
        # Higher weights indicate more valuable positions
        self.POSITION_WEIGHTS: Dict[int, int] = {
            12: 15,  # Center - highest strategic value
            7: 10, 17: 10, 11: 10, 13: 10,  # Central positions
            16: 8, 18: 8, 6: 8, 8: 8,       # Important central nodes
            2: 5, 22: 5, 10: 5, 14: 5,      # Medium value
            0: 2, 4: 2, 20: 2, 24: 2,       # Corner pieces
            25: 3, 27: 3, 34: 3, 36: 3      # Edge pieces
        }
        
        # Cache for evaluated board positions (transposition table)
        self.transposition_table: Dict = {}

    def _get_chain_captures(
        self,
        board: Tuple[int, ...],
        curr_pos: int,
        player: int,
        visited_caps: List[int],
        path: List[int],
        all_captures: List[Tuple]
    ) -> None:
        """
        Recursively find all possible chain captures from a position.
        
        Chain captures allow continued jumping if more opponent pieces can be captured
        after an initial capture move.
        
        Args:
            board: Current board state (immutable tuple)
            curr_pos: Current piece position
            player: Current player (1 or 2)
            visited_caps: List of already captured opponent pieces
            path: Path taken by the piece during captures
            all_captures: Accumulator for all valid capture sequences
        """
        found_further_jump = False
        opponent = 2 if player == 1 else 1

        for line in self.STRAIGHT_LINES:
            if curr_pos in line:
                idx = line.index(curr_pos)
                
                # Forward Jump - jump 2 positions ahead
                if idx + 2 < len(line):
                    nxt, landing = line[idx + 1], line[idx + 2]
                    if nxt not in visited_caps and board[nxt] == opponent and board[landing] == 0:
                        found_further_jump = True
                        nb = list(board)
                        nb[curr_pos], nb[nxt], nb[landing] = 0, 0, player
                        self._get_chain_captures(
                            tuple(nb), landing, player, 
                            visited_caps + [nxt], path + [landing], all_captures
                        )
                
                # Backward Jump - jump 2 positions back
                if idx - 2 >= 0:
                    nxt, landing = line[idx - 1], line[idx - 2]
                    if nxt not in visited_caps and board[nxt] == opponent and board[landing] == 0:
                        found_further_jump = True
                        nb = list(board)
                        nb[curr_pos], nb[nxt], nb[landing] = 0, 0, player
                        self._get_chain_captures(
                            tuple(nb), landing, player,
                            visited_caps + [nxt], path + [landing], all_captures
                        )

        # If no further jumps available and at least one capture was made, save the sequence
        if not found_further_jump and len(visited_caps) > 0:
            all_captures.append((path[0], curr_pos, tuple(visited_caps), list(path)))

    def get_valid_moves(
        self,
        board: List[int],
        player: int,
        force_capture: bool = False
    ) -> List[Tuple]:
        """
        Get all valid moves for a player in the current board state.
        
        A move consists of:
        - src: Source position
        - dst: Destination position
        - captured: Tuple of captured opponent pieces
        - path: List of positions traversed
        
        Args:
            board: Current board state (list of 37 integers: 0=empty, 1=P1, 2=P2)
            player: Current player (1 or 2)
            force_capture: If True, only return capture moves
            
        Returns:
            List of valid moves as tuples (src, dst, captured, path)
        """
        captures = []
        normal_moves = []
        board_tuple = tuple(board)

        # 1. Calculate all possible captures
        for src in range(37):
            if board[src] == player:
                self._get_chain_captures(board_tuple, src, player, [], [src], captures)

        # Remove duplicate captures (same source and destination but different paths)
        unique_captures = list({(c[0], c[1], c[2]): c for c in captures}.values())

        # If captures are forced, return only capture moves
        if force_capture and unique_captures:
            return unique_captures

        # 2. Calculate normal (non-capture) moves
        for line in self.STRAIGHT_LINES:
            for i in range(len(line) - 1):
                u, v = line[i], line[i+1]
                
                # Move from u to v
                if board[u] == player and board[v] == 0:
                    normal_moves.append((u, v, (), [u, v]))
                
                # Move from v to u (reverse direction)
                elif board[v] == player and board[u] == 0:
                    normal_moves.append((v, u, (), [v, u]))

        # Remove duplicate normal moves
        unique_normals = list({(m[0], m[1]): m for m in normal_moves}.values())

        # Return both captures and normal moves so players have complete freedom
        return unique_captures + unique_normals

    def evaluate_board(self, board: List[int], player: int) -> int:
        """
        Evaluate the board state from a player's perspective.
        
        Combines multiple evaluation metrics:
        - Material score: Piece count advantage
        - Position score: Strategic position value
        - Threat score: Available capture opportunities
        - Mobility score: Number of available moves
        
        Args:
            board: Current board state
            player: Player to evaluate for (1 or 2)
            
        Returns:
            Integer evaluation score (higher is better for the player)
        """
        opponent = 2 if player == 1 else 1

        # Material advantage (piece count)
        my_pieces = board.count(player)
        opp_pieces = board.count(opponent)
        material_score = (my_pieces - opp_pieces) * 5000

        # Position advantage (strategic node occupation)
        my_pos_score = sum(
            self.POSITION_WEIGHTS.get(i, 2) 
            for i, cell in enumerate(board) if cell == player
        )
        opp_pos_score = sum(
            self.POSITION_WEIGHTS.get(i, 2)
            for i, cell in enumerate(board) if cell == opponent
        )

        # Move availability and threat analysis
        my_moves = self.get_valid_moves(board, player, force_capture=False)
        opp_moves = self.get_valid_moves(board, opponent, force_capture=False)

        # Count available captures
        my_caps = sum(1 for m in my_moves if len(m[2]) > 0)
        opp_caps = sum(1 for m in opp_moves if len(m[2]) > 0)

        # Threat and mobility scores
        threat_score = (my_caps * 1500) - (opp_caps * 3000)
        mobility_score = (len(my_moves) - len(opp_moves)) * 15

        # Combine all scoring factors
        total_score = (
            material_score + threat_score + mobility_score + 
            (my_pos_score - opp_pos_score)
        )
        
        return total_score

    def minimax(
        self,
        board: List[int],
        depth: int,
        alpha: float,
        beta: float,
        maximizing_player: bool,
        player: int
    ) -> Tuple[int, Optional[Tuple]]:
        """
        Minimax algorithm with alpha-beta pruning.
        
        Recursively evaluates game positions to find the best move for the AI.
        Uses alpha-beta pruning to reduce the search space and transposition table
        for caching evaluated positions.
        
        Args:
            board: Current board state
            depth: Remaining search depth
            alpha: Alpha value for pruning
            beta: Beta value for pruning
            maximizing_player: True if maximizing node, False if minimizing
            player: The AI player (1 or 2)
            
        Returns:
            Tuple of (evaluation_score, best_move) at this node
        """
        # Check transposition table for previously evaluated position
        state_key = (tuple(board), depth, maximizing_player)
        if state_key in self.transposition_table:
            return self.transposition_table[state_key]

        # Terminal node - evaluate board position
        if depth == 0:
            eval_val = self.evaluate_board(board, player)
            return eval_val, None

        # Determine whose turn it is
        current_turn = player if maximizing_player else (2 if player == 1 else 1)
        valid_moves = self.get_valid_moves(board, current_turn, force_capture=False)

        # No legal moves - terminal condition
        if not valid_moves:
            score = -50000 if maximizing_player else 50000
            return score, None

        # Move ordering - prioritize captures and valuable positions
        valid_moves.sort(
            key=lambda m: (len(m[2]), self.POSITION_WEIGHTS.get(m[1], 2)),
            reverse=True
        )
        best_move = valid_moves[0]

        if maximizing_player:
            # Maximize node - find best move for current player
            max_eval = -float('inf')
            for move in valid_moves:
                src, dst, captured, _ = move
                temp_board = list(board)
                temp_board[src] = 0
                temp_board[dst] = current_turn
                for cap in captured:
                    temp_board[cap] = 0

                eval_val, _ = self.minimax(
                    temp_board, depth - 1, alpha, beta, False, player
                )
                
                if eval_val > max_eval:
                    max_eval = eval_val
                    best_move = move
                
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break  # Beta cutoff
            
            self.transposition_table[state_key] = (max_eval, best_move)
            return max_eval, best_move
        
        else:
            # Minimize node - find best move for opponent
            min_eval = float('inf')
            for move in valid_moves:
                src, dst, captured, _ = move
                temp_board = list(board)
                temp_board[src] = 0
                temp_board[dst] = current_turn
                for cap in captured:
                    temp_board[cap] = 0

                eval_val, _ = self.minimax(
                    temp_board, depth - 1, alpha, beta, True, player
                )
                
                if eval_val < min_eval:
                    min_eval = eval_val
                    best_move = move
                
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break  # Alpha cutoff
            
            self.transposition_table[state_key] = (min_eval, best_move)
            return min_eval, best_move

    def get_best_move(
        self,
        board: List[int],
        player: int = 1,
        depth: int = 6
    ) -> Optional[Tuple]:
        """
        Calculate the best move for a player using minimax algorithm.
        
        Args:
            board: Current board state
            player: Player to calculate move for (1 or 2, default: 1)
            depth: Search depth for minimax (default: 6)
            
        Returns:
            Best move as tuple (src, dst, captured, path) or None if no moves available
        """
        self.transposition_table.clear()
        _, move = self.minimax(board, depth, -float('inf'), float('inf'), True, player)
        return move
