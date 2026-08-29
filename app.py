import tkinter as tk
from tkinter import messagebox, filedialog
import copy
import math
import json
import os
from engine import SholoGutiEngine

class SholoGutiVisualApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sholo Guti Board & Engine")
        self.root.geometry("460x820")
        self.root.configure(bg="#12121e")

        self.engine = SholoGutiEngine()
        self.current_player = 1 
        self.is_animating = False

        self.initial_board = [
            2, 2, 2, 2, 2,
            2, 2, 2, 2, 2,
            0, 0, 0, 0, 0,
            1, 1, 1, 1, 1,
            1, 1, 1, 1, 1,
            2, 2, 2,
            2, 2, 2,
            1, 1, 1,
            1, 1, 1
        ]
        
        self.board = copy.deepcopy(self.initial_board)
        self.history = []     
        self.move_log = []    

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

        self.selected_node = None
        self.highlight_move = None
        self.animating_piece = None

        self.drag_node = None
        self.drag_pos = None
        self.drag_start_pos = None

        self.info = tk.Label(root, text="Click/Drag: Move | Right Click: Edit Node\n🟢 Player 1 (Green) | 🟠 Player 2 (Orange)", fg="#8a99ad", bg="#12121e", font=("Segoe UI", 9, "bold"))
        self.info.pack(pady=6)

        self.canvas = tk.Canvas(root, width=420, height=480, bg="#12121e", highlightthickness=0)
        self.canvas.pack()
        
        self.canvas.bind("<ButtonPress-1>", self.on_left_press)
        self.canvas.bind("<B1-Motion>", self.on_left_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_left_release)
        self.canvas.bind("<Button-3>", self.on_right_click)

        btn_frame1 = tk.Frame(root, bg="#12121e")
        btn_frame1.pack(pady=3)

        self.calc_p1_btn = tk.Button(btn_frame1, text="CALC P1 (🟢)", font=("Segoe UI", 9, "bold"), bg="#00c853", fg="white", activebackground="#00e676", relief=tk.FLAT, padx=6, pady=4, command=lambda: self.calculate(player=1))
        self.calc_p1_btn.pack(side=tk.LEFT, padx=3)

        self.calc_p2_btn = tk.Button(btn_frame1, text="CALC P2 (🟠)", font=("Segoe UI", 9, "bold"), bg="#ff6d00", fg="white", activebackground="#ff9100", relief=tk.FLAT, padx=6, pady=4, command=lambda: self.calculate(player=2))
        self.calc_p2_btn.pack(side=tk.LEFT, padx=3)

        self.exec_btn = tk.Button(btn_frame1, text="EXECUTE MOVE", font=("Segoe UI", 9, "bold"), bg="#29b6f6", fg="white", activebackground="#4fc3f7", relief=tk.FLAT, padx=8, pady=4, command=self.execute_suggested_move)
        self.exec_btn.pack(side=tk.LEFT, padx=3)

        btn_frame2 = tk.Frame(root, bg="#12121e")
        btn_frame2.pack(pady=3)

        self.undo_btn = tk.Button(btn_frame2, text="↺ UNDO", font=("Segoe UI", 9, "bold"), bg="#7e57c2", fg="white", relief=tk.FLAT, padx=6, pady=3, command=self.undo_move)
        self.undo_btn.pack(side=tk.LEFT, padx=3)

        self.log_btn = tk.Button(btn_frame2, text="💾 SAVE LOG", font=("Segoe UI", 9, "bold"), bg="#5c6bc0", fg="white", relief=tk.FLAT, padx=6, pady=3, command=self.export_log)
        self.log_btn.pack(side=tk.LEFT, padx=3)

        self.reset_btn = tk.Button(btn_frame2, text="🔄 RESET", font=("Segoe UI", 9, "bold"), bg="#ab47bc", fg="white", relief=tk.FLAT, padx=6, pady=3, command=self.reset_board)
        self.reset_btn.pack(side=tk.LEFT, padx=3)

        self.clear_btn = tk.Button(btn_frame2, text="🧹 CLEAR", font=("Segoe UI", 9, "bold"), bg="#ef5350", fg="white", relief=tk.FLAT, padx=6, pady=3, command=self.clear_board)
        self.clear_btn.pack(side=tk.LEFT, padx=3)

        self.result_label = tk.Label(root, text="Set board state and press calculate", font=("Segoe UI", 9, "bold"), fg="#4fc3f7", bg="#12121e")
        self.result_label.pack(pady=6)

        self.draw_board()

    def save_state(self):
        self.history.append((copy.deepcopy(self.board), copy.deepcopy(self.move_log)))

    def record_move_log(self, player, src, dst, captured):
        log_entry = {
            "step": len(self.move_log) + 1,
            "player": "Player 1 (Green)" if player == 1 else "Player 2 (Orange)",
            "from": src,
            "to": dst,
            "captured": list(captured) if captured else []
        }
        self.move_log.append(log_entry)
        
        try:
            with open("latest_match_log.json", "w", encoding="utf-8") as f:
                json.dump(self.move_log, f, indent=2)
        except Exception:
            pass

    def export_log(self):
        if not self.move_log:
            messagebox.showinfo("Export Log", "No moves recorded yet in this match!")
            return

        filepath = filedialog.asksaveasfilename(
            initialfile="sholo_guti_log.json",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        
        if filepath:
            log_json_str = json.dumps(self.move_log, indent=2)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(log_json_str)
            messagebox.showinfo("Success!", f"Log file saved successfully!\n\nLocation: {filepath}")

    def get_node_at(self, x, y):
        for node, (nx, ny) in self.coords.items():
            if (x - nx)**2 + (y - ny)**2 <= 18**2:
                return node
        return None

    def draw_glossy_piece(self, x, y, player, is_selected=False):
        r = 14
        self.canvas.create_oval(x - r + 2, y - r + 4, x + r + 3, y + r + 4, fill="#08080d", outline="")
        
        if player == 1:
            base_color = "#00c853"
            border_color = "#69f0ae"
            gloss_color = "#b9f6ca"
        elif player == 2:
            base_color = "#ff6d00"
            border_color = "#ffd180"
            gloss_color = "#ffe0b2"

        if is_selected:
            self.canvas.create_oval(x - r - 6, y - r - 6, x + r + 6, y + r + 6, outline="#ffeb3b", width=3)

        self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=base_color, outline=border_color, width=1.5)
        self.canvas.create_oval(x - r + 3, y - r + 3, x + r - 6, y + r - 8, fill=gloss_color, outline="")
        self.canvas.create_oval(x - r + 5, y - r + 4, x - r + 9, y - r + 8, fill="#ffffff", outline="")

    def draw_board(self):
        self.canvas.delete("all")

        for line in self.engine.STRAIGHT_LINES:
            for i in range(len(line) - 1):
                x1, y1 = self.coords[line[i]]
                x2, y2 = self.coords[line[i+1]]
                self.canvas.create_line(x1, y1, x2, y2, fill="#2c2c44", width=5)
                self.canvas.create_line(x1, y1, x2, y2, fill="#5c5c8a", width=2)

        if self.highlight_move and not self.is_animating:
            path = self.highlight_move[3]
            for i in range(len(path) - 1):
                p1, p2 = path[i], path[i+1]
                x1, y1 = self.coords[p1]
                x2, y2 = self.coords[p2]
                self.canvas.create_line(x1, y1, x2, y2, fill="#ff1744", width=4, arrow=tk.LAST, arrowshape=(10,12,5))

        for node, (x, y) in self.coords.items():
            val = self.board[node]

            if val == 0:
                self.canvas.create_oval(x-12, y-12, x+12, y+12, fill="#181828", outline="#30304a", width=2)
                self.canvas.create_text(x, y, text=str(node), fill="#62628a", font=("Segoe UI", 8, "bold"))
            else:
                if node == self.drag_node:
                    self.canvas.create_oval(x-12, y-12, x+12, y+12, fill="#181828", outline="#30304a", width=2)
                    self.canvas.create_text(x, y, text=str(node), fill="#62628a", font=("Segoe UI", 8, "bold"))
                    continue

                is_sel = (node == self.selected_node)
                self.draw_glossy_piece(x, y, val, is_selected=is_sel)
                self.canvas.create_text(x, y, text=str(node), fill="#000000", font=("Segoe UI", 8, "bold"))

        if self.drag_node is not None and self.drag_pos:
            dx, dy = self.drag_pos
            drag_player = self.board[self.drag_node]
            self.draw_glossy_piece(dx, dy, drag_player, is_selected=True)

        if self.animating_piece:
            ax, ay, a_player = self.animating_piece
            self.draw_glossy_piece(ax, ay, a_player)

    def animate_move(self, move, on_complete_callback=None):
        if self.is_animating:
            return

        self.is_animating = True
        src, dst, captured_tuple, path = move
        player_piece = self.board[src]
        
        self.record_move_log(player_piece, src, dst, captured_tuple)

        self.board[src] = 0
        caps_to_remove = list(captured_tuple) if captured_tuple else []
        segments = [(path[i], path[i+1]) for i in range(len(path) - 1)]

        def animate_segment(seg_idx):
            if seg_idx >= len(segments):
                self.board[dst] = player_piece
                self.animating_piece = None
                self.is_animating = False
                self.draw_board()
                if on_complete_callback:
                    on_complete_callback()
                return

            u, v = segments[seg_idx]
            x1, y1 = self.coords[u]
            x2, y2 = self.coords[v]

            over_node = None
            for cap in caps_to_remove:
                ux, uy = self.coords[u]
                vx, vy = self.coords[v]
                cx, cy = self.coords[cap]
                if min(ux, vx) <= cx <= max(ux, vx) and min(uy, vy) <= cy <= max(uy, vy):
                    over_node = cap
                    break

            frames = 10
            delay = 10

            def step_frame(f):
                if f > frames:
                    if over_node and over_node in caps_to_remove:
                        self.board[over_node] = 0
                        caps_to_remove.remove(over_node)
                    animate_segment(seg_idx + 1)
                    return

                t = f / frames
                t_smooth = t * t * (3 - 2 * t)
                
                curr_x = x1 + (x2 - x1) * t_smooth
                curr_y = y1 + (y2 - y1) * t_smooth

                self.animating_piece = (curr_x, curr_y, player_piece)
                self.draw_board()
                self.root.after(delay, lambda: step_frame(f + 1))

            step_frame(0)

        animate_segment(0)

    def try_make_move(self, src, dst):
        player = self.board[src]
        if player == 0:
            return False

        # force_capture=False করে দেওয়া হয়েছে যাতে সাধারণ চাল দিতে কোনো লক বা বাধা না থাকে
        valid_moves = self.engine.get_valid_moves(self.board, player, force_capture=False)
        matched_move = None
        for move in valid_moves:
            s, d, _, _ = move
            if s == src and d == dst:
                matched_move = move
                break

        if matched_move:
            self.save_state()
            self.selected_node = None
            self.highlight_move = None
            self.animate_move(matched_move)
            return True
        else:
            self.draw_board()
            return False

    def on_left_press(self, event):
        if self.is_animating:
            return

        clicked = self.get_node_at(event.x, event.y)
        self.drag_start_pos = (event.x, event.y)

        if clicked is not None and self.board[clicked] != 0:
            self.drag_node = clicked
            self.drag_pos = (event.x, event.y)

    def on_left_drag(self, event):
        if self.is_animating or self.drag_node is None:
            return
        self.drag_pos = (event.x, event.y)
        self.draw_board()

    def on_left_release(self, event):
        if self.is_animating:
            return

        clicked = self.get_node_at(event.x, event.y)
        dist_moved = 0
        if self.drag_start_pos:
            dist_moved = math.hypot(event.x - self.drag_start_pos[0], event.y - self.drag_start_pos[1])

        if dist_moved > 8 and self.drag_node is not None:
            src = self.drag_node
            dst = clicked
            self.drag_node = None
            self.drag_pos = None

            if dst is not None and dst != src:
                self.try_make_move(src, dst)
            else:
                self.draw_board()

        else:
            self.drag_node = None
            self.drag_pos = None

            if clicked is not None:
                if self.selected_node is None:
                    if self.board[clicked] != 0:
                        self.selected_node = clicked
                else:
                    if clicked == self.selected_node:
                        self.selected_node = None
                    elif self.board[clicked] != 0:
                        self.selected_node = clicked
                    else:
                        src = self.selected_node
                        dst = clicked
                        self.selected_node = None
                        self.try_make_move(src, dst)
            
            self.draw_board()

    def on_right_click(self, event):
        if self.is_animating:
            return

        clicked = self.get_node_at(event.x, event.y)
        if clicked is not None:
            self.save_state()
            self.board[clicked] = (self.board[clicked] + 1) % 3
            self.selected_node = None
            self.highlight_move = None
            self.draw_board()

    def calculate(self, player=1):
        if self.is_animating:
            return

        best_move = self.engine.get_best_move(self.board, player=player, depth=6)
        if best_move:
            self.highlight_move = best_move
            src, dst, captured_tuple, _ = best_move
            p_str = "P1 (Green)" if player == 1 else "P2 (Orange)"
            res_text = f"👉 [{p_str}] Move Node {src} to Node {dst}"
            if captured_tuple:
                caps_str = ", ".join(map(str, captured_tuple))
                res_text += f" (Captures: {caps_str})"
            color = "#00e676" if player == 1 else "#ff9100"
            self.result_label.config(text=res_text, fg=color)
        else:
            self.highlight_move = None
            self.result_label.config(text="⚠️ No legal moves available!", fg="#ff5252")
        
        self.draw_board()

    def execute_suggested_move(self):
        if self.is_animating:
            return

        if self.highlight_move:
            move_to_exec = self.highlight_move
            self.save_state()
            self.highlight_move = None
            
            def on_done():
                self.result_label.config(text="Move Executed! Recalculate for next move.", fg="#4fc3f7")

            self.animate_move(move_to_exec, on_complete_callback=on_done)

    def undo_move(self):
        if self.is_animating:
            return

        if self.history:
            self.board, self.move_log = self.history.pop()
            self.selected_node = None
            self.highlight_move = None
            self.result_label.config(text="Reverted to previous state", fg="#4fc3f7")
            self.draw_board()

    def reset_board(self):
        if self.is_animating:
            return

        self.save_state()
        self.board = copy.deepcopy(self.initial_board)
        self.move_log = []
        self.selected_node = None
        self.highlight_move = None
        self.result_label.config(text="Board & Log Reset to Default Setup", fg="#ab47bc")
        self.draw_board()

    def clear_board(self):
        if self.is_animating:
            return

        self.save_state()
        self.board = [0] * 37
        self.move_log = []
        self.selected_node = None
        self.highlight_move = None
        self.result_label.config(text="Board & Log Cleared", fg="#ef5350")
        self.draw_board()

if __name__ == "__main__":
    root = tk.Tk()
    app = SholoGutiVisualApp(root)
    root.mainloop()

