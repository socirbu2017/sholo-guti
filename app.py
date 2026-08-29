"""
Sholo Guti - Ancient Indian Board Game UI

A Kivy-based interactive game board with AI player support.
The game features touch-based controls and AI move calculation using minimax algorithm.
"""

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
import copy
from engine import SholoGutiEngine


class BoardWidget(Widget):
    """
    Widget for rendering the Sholo Guti game board.
    
    Handles visual rendering of the board, nodes, pieces, and game highlights.
    Processes touch events for piece selection and movement.
    """

    def __init__(self, main_app, **kwargs):
        """
        Initialize the board widget.
        
        Args:
            main_app: Reference to the main application instance
            **kwargs: Additional keyword arguments for Widget
        """
        super().__init__(**kwargs)
        self.main_app = main_app
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        """
        Redraw the canvas with current board state.
        
        This method:
        - Scales board coordinates to fit the screen
        - Draws board lines and nodes
        - Renders pieces with appropriate colors
        - Highlights selected pieces and suggested moves
        """
        self.canvas.clear()
        
        # Scale coordinates to fit screen dynamically
        padding_x, padding_y = 40, 40
        w = max(self.width - 2 * padding_x, 100)
        h = max(self.height - 2 * padding_y, 100)
        
        scaled_coords = {}
        for node, (orig_x, orig_y) in self.main_app.coords.items():
            cx = self.x + padding_x + (orig_x - 70) * (w / 280.0)
            cy = self.top - (padding_y + (orig_y - 50) * (h / 400.0))
            scaled_coords[node] = (cx, cy)
            
        self.main_app.current_scaled_coords = scaled_coords

        with self.canvas:
            # Draw Lines
            Color(0.36, 0.36, 0.54, 1)
            for line in self.main_app.engine.STRAIGHT_LINES:
                for i in range(len(line) - 1):
                    p1, p2 = scaled_coords[line[i]], scaled_coords[line[i+1]]
                    Line(points=[p1[0], p1[1], p2[0], p2[1]], width=2)

            # Draw Highlight Move
            if self.main_app.highlight_move and not self.main_app.is_animating:
                Color(1, 0.09, 0.26, 1)
                path = self.main_app.highlight_move[3]
                for i in range(len(path) - 1):
                    p1, p2 = scaled_coords[path[i]], scaled_coords[path[i+1]]
                    Line(points=[p1[0], p1[1], p2[0], p2[1]], width=3.5)

            # Draw Nodes & Pieces
            r = 16
            for node, (x, y) in scaled_coords.items():
                val = self.main_app.board[node]
                if val == 0:
                    # Empty node
                    Color(0.09, 0.09, 0.15, 1)
                    Ellipse(pos=(x - r, y - r), size=(2*r, 2*r))
                    Color(0.2, 0.2, 0.3, 1)
                    Line(ellipse=(x - r, y - r, 2*r, 2*r), width=1.5)
                else:
                    # Node with piece
                    if node == self.main_app.selected_node:
                        # Highlight selected piece
                        Color(1, 0.92, 0.23, 1)
                        Ellipse(pos=(x - r - 4, y - r - 4), size=(2*r + 8, 2*r + 8))

                    if val == 1:
                        Color(0, 0.78, 0.32, 1)  # Green for Player 1
                    elif val == 2:
                        Color(1, 0.42, 0, 1)     # Orange for Player 2
                    
                    Ellipse(pos=(x - r, y - r), size=(2*r, 2*r))

    def on_touch_down(self, touch):
        """
        Handle touch input on the board.
        
        Single tap: Select/move pieces
        Double tap: Toggle node state for board setup
        
        Args:
            touch: Touch event object
            
        Returns:
            bool: True if touch was handled, False otherwise
        """
        if not self.collide_point(*touch.pos) or self.main_app.is_animating:
            return False

        clicked = None
        r = 25
        for node, (cx, cy) in self.main_app.current_scaled_coords.items():
            if (touch.x - cx)**2 + (touch.y - cy)**2 <= r**2:
                clicked = node
                break

        if clicked is not None:
            if touch.is_double_tap:
                # Toggle node state for board editing
                self.main_app.save_state()
                self.main_app.board[clicked] = (self.main_app.board[clicked] + 1) % 3
                self.main_app.selected_node = None
                self.main_app.highlight_move = None
                self.update_canvas()
            else:
                if self.main_app.selected_node is None:
                    # Select a piece if it exists
                    if self.main_app.board[clicked] != 0:
                        self.main_app.selected_node = clicked
                else:
                    if clicked == self.main_app.selected_node:
                        # Deselect
                        self.main_app.selected_node = None
                    elif self.main_app.board[clicked] != 0:
                        # Select different piece
                        self.main_app.selected_node = clicked
                    else:
                        # Try to move selected piece to destination
                        src = self.main_app.selected_node
                        dst = clicked
                        self.main_app.selected_node = None
                        self.main_app.try_make_move(src, dst)
                self.update_canvas()
            return True
        return super().on_touch_down(touch)


class SholoGutiApp(App):
    """
    Main Kivy application for Sholo Guti game.
    
    Manages game state, UI controls, and user interactions.
    Coordinates between the game engine and the visual board representation.
    """

    def build(self):
        """
        Build and configure the application UI.
        
        Returns:
            BoxLayout: Root layout containing all UI elements
        """
        self.engine = SholoGutiEngine()
        self.is_animating = False
        self.selected_node = None
        self.highlight_move = None
        self.current_scaled_coords = {}

        # Initial board setup (37 positions)
        # Player 1 (Green) at bottom, Player 2 (Orange) at top
        self.initial_board = [
            2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0,
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2,
            2, 1, 1, 1, 1, 1, 1
        ]
        self.board = copy.deepcopy(self.initial_board)
        self.history = []

        # Board node coordinates
        self.coords = {
            0: (70, 150),  1: (140, 150), 2: (210, 150), 3: (280, 150), 4: (350, 150),
            5: (70, 200),  6: (140, 200), 7: (210, 200), 8: (280, 200), 9: (350, 200),
            10: (70, 250), 11: (140, 250), 12: (210, 250), 13: (280, 250), 14: (350, 250),
            15: (70, 300), 16: (140, 300), 17: (210, 300), 18: (280, 300), 19: (350, 300),
            20: (70, 350), 21: (140, 350), 22: (210, 350), 23: (280, 350), 24: (350, 350),
            25: (70, 50),   26: (210, 50),  27: (350, 50),
            28: (140, 100), 29: (210, 100), 30: (280, 100),
            31: (140, 400), 32: (210, 400), 33: (280, 400),
            34: (70, 450),  35: (210, 450), 36: (350, 450)
        }

        # Build UI layout
        root_layout = BoxLayout(orientation='vertical', spacing=5, padding=5)

        # Info label
        self.info_label = Label(
            text="Tap: Select/Move | Double-Tap: Edit",
            size_hint_y=0.08,
            color=(0.54, 0.6, 0.68, 1)
        )
        root_layout.add_widget(self.info_label)

        # Board widget
        self.board_widget = BoardWidget(main_app=self, size_hint_y=0.7)
        root_layout.add_widget(self.board_widget)

        # Result label
        self.result_label = Label(
            text="Select board state & Calculate",
            size_hint_y=0.07,
            color=(0.31, 0.76, 0.96, 1)
        )
        root_layout.add_widget(self.result_label)

        # Controls Row 1 - Move calculation buttons
        btn_layout1 = BoxLayout(size_hint_y=0.08, spacing=5)
        btn_p1 = Button(text="CALC P1", background_color=(0, 0.78, 0.32, 1))
        btn_p1.bind(on_press=lambda x: self.calculate(1))
        btn_p2 = Button(text="CALC P2", background_color=(1, 0.42, 0, 1))
        btn_p2.bind(on_press=lambda x: self.calculate(2))
        btn_exec = Button(text="EXECUTE", background_color=(0.16, 0.71, 0.96, 1))
        btn_exec.bind(on_press=lambda x: self.execute_suggested_move())

        btn_layout1.add_widget(btn_p1)
        btn_layout1.add_widget(btn_p2)
        btn_layout1.add_widget(btn_exec)
        root_layout.add_widget(btn_layout1)

        # Controls Row 2 - Game management buttons
        btn_layout2 = BoxLayout(size_hint_y=0.07, spacing=5)
        btn_undo = Button(text="UNDO")
        btn_undo.bind(on_press=lambda x: self.undo_move())
        btn_reset = Button(text="RESET")
        btn_reset.bind(on_press=lambda x: self.reset_board())
        btn_clear = Button(text="CLEAR")
        btn_clear.bind(on_press=lambda x: self.clear_board())

        btn_layout2.add_widget(btn_undo)
        btn_layout2.add_widget(btn_reset)
        btn_layout2.add_widget(btn_clear)
        root_layout.add_widget(btn_layout2)

        return root_layout

    def save_state(self):
        """Save current board state to history for undo functionality."""
        self.history.append(copy.deepcopy(self.board))

    def try_make_move(self, src, dst):
        """
        Attempt to make a move from source to destination.
        
        Validates the move against available legal moves and updates board if valid.
        
        Args:
            src: Source node index
            dst: Destination node index
        """
        player = self.board[src]
        if player == 0:
            return
        
        valid_moves = self.engine.get_valid_moves(self.board, player, force_capture=False)
        matched = next((m for m in valid_moves if m[0] == src and m[1] == dst), None)

        if matched:
            self.save_state()
            self.board[src] = 0
            self.board[dst] = player
            for cap in matched[2]:
                self.board[cap] = 0
            self.highlight_move = None
            self.board_widget.update_canvas()

    def calculate(self, player):
        """
        Calculate the best move for a player using AI.
        
        Args:
            player: Player number (1 or 2)
        """
        best_move = self.engine.get_best_move(self.board, player=player, depth=5)
        if best_move:
            self.highlight_move = best_move
            p_str = "P1" if player == 1 else "P2"
            self.result_label.text = f"{p_str}: Move {best_move[0]} to {best_move[1]}"
        else:
            self.highlight_move = None
            self.result_label.text = "No legal moves available!"
        self.board_widget.update_canvas()

    def execute_suggested_move(self):
        """Execute the currently highlighted suggested move."""
        if self.highlight_move:
            src, dst, captured, _ = self.highlight_move
            self.save_state()
            player = self.board[src]
            self.board[src] = 0
            self.board[dst] = player
            for cap in captured:
                self.board[cap] = 0
            self.highlight_move = None
            self.result_label.text = "Move Executed!"
            self.board_widget.update_canvas()

    def undo_move(self):
        """Undo the last move."""
        if self.history:
            self.board = self.history.pop()
            self.highlight_move = None
            self.board_widget.update_canvas()

    def reset_board(self):
        """Reset the board to initial state."""
        self.save_state()
        self.board = copy.deepcopy(self.initial_board)
        self.highlight_move = None
        self.board_widget.update_canvas()

    def clear_board(self):
        """Clear all pieces from the board."""
        self.save_state()
        self.board = [0] * 37
        self.highlight_move = None
        self.board_widget.update_canvas()


if __name__ == '__main__':
    SholoGutiApp().run()
