"""
Tic Tac Toe 3D - Edicion Online
=================================
Basado en el juego original del profesor (tablero 4x4x4, seleccion de
coordenadas X/Y/Z con Radiobutton + boton "Enter" para confirmar la
jugada). Se conserva exactamente esa misma dinamica de juego, pero:

  * Se le dio un estilo oscuro, elegante y moderno.
  * Ahora dos jugadores en computadoras distintas pueden jugar la MISMA
    partida en tiempo real, usando Firebase Realtime Database como
    "mensajero" entre ambas maquinas.

Como funciona el modo online (resumen rapido):
  1. Un jugador elige "Crear partida" -> se genera un codigo de sala
    (ej: "K3F9A") y ese jugador queda como Jugador 1 (ficha O).
  2. Se comparte el codigo por WhatsApp/Discord/lo que sea.
  3. El otro jugador elige "Unirse a partida", ingresa el codigo y
    queda como Jugador 2 (ficha X).
  4. Cada jugada se guarda en Firebase; el otro cliente la recibe casi
    al instante y el tablero se actualiza solo, en ambas pantallas.

Requisitos: ver requirements.txt y README.md que acompanan este archivo.
"""

import copy
import queue
import random
import string
import threading
import tkinter.font as tkfont
from tkinter import *
from tkinter import messagebox

import pyrebase


from firebase_config import FIREBASE_CONFIG



# ---------------------------------------------------------------------------
# PALETA "ELEGANTE Y MASCULINA" ---------------------------------------------
# ---------------------------------------------------------------------------
BG_ROOT       = "#101216"   # fondo general, casi negro
BG_HEADER     = "#171a20"   # franja superior
BG_FOOTER     = "#171a20"   # franja inferior
BG_PANEL      = "#1c1f26"

CELL_BG       = "#20242c"   # celda vacia
CELL_BORDER   = "#3a4150"   # borde de celda (acero apagado)
CELL_HOVER    = "#2a2f39"

GOLD          = "#c9a24d"   # acento principal (dorado/laton apagado)
GOLD_DIM      = "#8a7238"
STEEL         = "#6f93b3"   # acento secundario (azul acero)
STEEL_DIM     = "#3f5872"
CRIMSON       = "#9c3b3b"   # resaltado de linea ganadora
CRIMSON_TEXT  = "#f2c9a0"

TEXT_LIGHT    = "#e9e6dd"
TEXT_MUTED    = "#7d828c"
TEXT_DANGER   = "#c96a5b"

X_COLOR = GOLD     # Jugador 2 = X = dorado
O_COLOR = STEEL    # Jugador 1 = O = azul acero

PLAYER_LABELS = {0: "Jugador 1 (O)", 1: "Jugador 2 (X)"}
PLAYER_SYMBOL = {0: "O", 1: "X"}
PLAYER_COLOR  = {0: O_COLOR, 1: X_COLOR}


def pick_font(preferred="Segoe UI"):
    """Usa la fuente preferida si esta instalada; si no, cae a Helvetica."""
    try:
        families = set(tkfont.families())
    except Exception:
        return "Helvetica"
    return preferred if preferred in families else "Helvetica"


# ---------------------------------------------------------------------------
# LOGICA DEL TABLERO 4x4x4 ---------------------------------------------------
# ---------------------------------------------------------------------------
# Cada una de estas 13 funciones devuelve la lista de celdas (Z,Y,X) que
# forman una posible linea ganadora que pasa por la jugada recien hecha.
# Se derivan directamente de las sumas que usaba el codigo original del
# profesor (horizontal, vertical, profundidad y las 10 diagonales).

LINE_DEFS = [
    lambda Z, Y, X: [(Z, Y, x) for x in range(4)],                # horizontal
    lambda Z, Y, X: [(Z, y, X) for y in range(4)],                # vertical
    lambda Z, Y, X: [(z, Y, X) for z in range(4)],                # profundidad
    lambda Z, Y, X: [(Z, y, y) for y in range(4)],                # diag frontal 1
    lambda Z, Y, X: [(Z, y, 3 - y) for y in range(4)],            # diag frontal 2
    lambda Z, Y, X: [(z, Y, z) for z in range(4)],                # diag horizontal 1
    lambda Z, Y, X: [(3 - z, Y, z) for z in range(4)],            # diag horizontal 2
    lambda Z, Y, X: [(z, z, X) for z in range(4)],                # diag vertical 1
    lambda Z, Y, X: [(3 - z, z, X) for z in range(4)],            # diag vertical 2
    lambda Z, Y, X: [(3 - x, x, x) for x in range(4)],            # diag cruzada 1
    lambda Z, Y, X: [(x, 3 - x, x) for x in range(4)],            # diag cruzada 2
    lambda Z, Y, X: [(3 - y, 3 - y, y) for y in range(4)],        # diag cruzada 3
    lambda Z, Y, X: [(z, z, z) for z in range(4)],                # diag cruzada 4
]


def new_empty_board():
    return [[[0, 0, 0, 0] for _ in range(4)] for _ in range(4)]


def find_winning_line(board, Z, Y, X):
    """Devuelve la lista de coordenadas de la linea ganadora, o None."""
    for line_fn in LINE_DEFS:
        coords = line_fn(Z, Y, X)
        total = sum(board[z][y][x] for (z, y, x) in coords)
        if total == 4 or total == -4:
            return coords
    return None


def board_is_full(board):
    return all(
        board[z][y][x] != 0
        for z in range(4)
        for y in range(4)
        for x in range(4)
    )


def generate_room_code(length=5):
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


# ---------------------------------------------------------------------------
# VENTANA DE ENTRADA (LOBBY) --------------------------------------------------
# ---------------------------------------------------------------------------
class Lobby:
    """Pantalla inicial: crear partida o unirse con un codigo."""

    def __init__(self, on_ready):
        self.on_ready = on_ready
        self.font = pick_font()

        self.root = Tk()
        self.root.title("Tic Tac Toe 3D - Online")
        self.root.configure(bg=BG_ROOT)
        self.root.resizable(0, 0)
        self.root.geometry("480x360")

        Label(self.root, text="TIC TAC TOE 3D", bg=BG_ROOT, fg=GOLD,
              font=(self.font, 26, "bold")).pack(pady=(36, 0))
        Label(self.root, text="EDICION ONLINE", bg=BG_ROOT, fg=TEXT_MUTED,
              font=(self.font, 12), ).pack(pady=(0, 30))

        Button(self.root, text="CREAR PARTIDA", command=self.create_room,
               bg=GOLD, fg="#14161a", activebackground=GOLD_DIM,
               activeforeground="#14161a", relief=FLAT, bd=0,
               font=(self.font, 13, "bold"), width=24, height=2,
               cursor="hand2").pack(pady=8)

        Button(self.root, text="UNIRSE A PARTIDA", command=self.join_room,
               bg=BG_PANEL, fg=STEEL, activebackground=STEEL_DIM,
               activeforeground=TEXT_LIGHT, relief=FLAT, bd=0,
               font=(self.font, 13, "bold"), width=24, height=2,
               cursor="hand2", highlightbackground=STEEL_DIM,
               highlightthickness=1).pack(pady=8)

        self.status = Label(self.root, text="", bg=BG_ROOT, fg=TEXT_DANGER,
                             font=(self.font, 10))
        self.status.pack(pady=(20, 0))

        self.db = None
        self.firebase_app = None
        self._connect_firebase()

        self.root.mainloop()

    def _connect_firebase(self):
        try:
            self.firebase_app = pyrebase.initialize_app(FIREBASE_CONFIG)
            self.db = self.firebase_app.database()
        except Exception as exc:
            messagebox.showerror(
                "Error de configuracion",
                "No se pudo conectar con Firebase.\n\n"
                "Revisa firebase_config.py con tus credenciales.\n\n"
                f"Detalle: {exc}",
            )
            self.root.destroy()

    def create_room(self):
        code = generate_room_code()
        data = {
            "board": new_empty_board(),
            "turn": 0,
            "status": "waiting",
            "winner": None,
            "winLine": None,
            "players": {"0": True},
        }
        try:
            self.db.child("games").child(code).set(data)
        except Exception as exc:
            self.status.config(text=f"No se pudo crear la sala: {exc}")
            return
        self.root.destroy()
        self.on_ready(self.firebase_app, self.db, code, player_index=0)

    def join_room(self):
        code = self._ask_code()
        if not code:
            return
        code = code.strip().upper()
        try:
            room = self.db.child("games").child(code).get().val()
        except Exception as exc:
            self.status.config(text=f"Error de conexion: {exc}")
            return
        if not room:
            self.status.config(text="Ese codigo de sala no existe.")
            return
        players = room.get("players") or {}
        if "1" in players and room.get("status") != "waiting":
            self.status.config(text="Esa partida ya tiene 2 jugadores.")
            return
        try:
            self.db.child("games").child(code).update({
                "players/1": True,
                "status": "playing",
            })
        except Exception as exc:
            self.status.config(text=f"No se pudo unir a la sala: {exc}")
            return
        self.root.destroy()
        self.on_ready(self.firebase_app, self.db, code, player_index=1)

    def _ask_code(self):
        dialog = Toplevel(self.root, bg=BG_PANEL)
        dialog.title("Unirse a partida")
        dialog.resizable(0, 0)
        dialog.geometry("340x170")
        dialog.transient(self.root)
        dialog.grab_set()

        Label(dialog, text="Codigo de la sala", bg=BG_PANEL, fg=TEXT_LIGHT,
              font=(self.font, 12)).pack(pady=(20, 8))
        entry = Entry(dialog, font=(self.font, 16, "bold"), justify="center",
                      bg=CELL_BG, fg=GOLD, insertbackground=GOLD,
                      relief=FLAT)
        entry.pack(ipady=6, padx=30, fill=X)
        entry.focus_set()

        result = {"code": None}

        def confirm(event=None):
            result["code"] = entry.get()
            dialog.destroy()

        Button(dialog, text="ENTRAR", command=confirm, bg=STEEL,
               fg="#14161a", activebackground=STEEL_DIM, relief=FLAT,
               font=(self.font, 11, "bold"), cursor="hand2").pack(pady=16)
        dialog.bind("<Return>", confirm)
        dialog.wait_window()
        return result["code"]


# ---------------------------------------------------------------------------
# VENTANA PRINCIPAL DEL JUEGO -------------------------------------------------
# ---------------------------------------------------------------------------
class Game:
    CELL_W, CELL_H = 65, 40
    SLICE_W, SLICE_H = 260, 160
    CANVAS_W, CANVAS_H = 1040, 640

    def __init__(self, firebase_app, db, room_id, player_index):
        self.firebase_app = firebase_app
        self.db = db
        self.room_id = room_id
        self.player_index = player_index

        self.board = new_empty_board()
        self.turn = 0
        self.status = "waiting"
        self.winner = None
        self.win_line = None

        self.selected = {"X": None, "Y": None, "Z": None}

        self.msg_queue = queue.Queue()
        self.font = pick_font()

        self._build_window()
        self._start_stream()
        self.root.after(150, self._poll_queue)
        self.root.after(400, self.refresh_from_server)
        self.root.mainloop()

    # -- construccion de la interfaz -----------------------------------
    def _build_window(self):
        self.root = Tk()
        self.root.title("Tic Tac Toe 3D - Online")
        self.root.configure(bg=BG_ROOT)
        self.root.resizable(0, 0)
        try:
            self.root.iconbitmap("cubo.ico")
        except Exception:
            pass
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # ---- header ----
        header = Frame(self.root, bg=BG_HEADER, height=90)
        header.pack(fill=X)
        header.pack_propagate(False)

        left = Frame(header, bg=BG_HEADER)
        left.pack(side=LEFT, padx=24, pady=10)
        Label(left, text="TIC TAC TOE 3D", bg=BG_HEADER, fg=GOLD,
              font=(self.font, 16, "bold")).pack(anchor="w")
        Label(left, text=f"Sala: {self.room_id}", bg=BG_HEADER, fg=TEXT_MUTED,
              font=(self.font, 10)).pack(anchor="w")

        Button(left, text="Copiar codigo", command=self._copy_code,
               bg=BG_PANEL, fg=STEEL, relief=FLAT, bd=0,
               font=(self.font, 9), cursor="hand2").pack(anchor="w", pady=(4, 0))

        right = Frame(header, bg=BG_HEADER)
        right.pack(side=RIGHT, padx=24, pady=10)
        me_color = PLAYER_COLOR[self.player_index]
        Label(right, text=f"Tu eres: {PLAYER_LABELS[self.player_index]}",
              bg=BG_HEADER, fg=me_color,
              font=(self.font, 12, "bold")).pack(anchor="e")
        self.turn_label = Label(right, text="Conectando...", bg=BG_HEADER,
                                 fg=TEXT_MUTED, font=(self.font, 11))
        self.turn_label.pack(anchor="e")

        # ---- tablero ----
        canvas_wrap = Frame(self.root, bg=BG_ROOT)
        canvas_wrap.pack()
        self.canvas = Canvas(canvas_wrap, width=self.CANVAS_W,
                              height=self.CANVAS_H, bg=BG_ROOT,
                              highlightthickness=0)
        self.canvas.pack()

        # ---- footer ----
        footer = Frame(self.root, bg=BG_FOOTER)
        footer.pack(fill=X)

        coord_row = Frame(footer, bg=BG_FOOTER)
        coord_row.pack(pady=(14, 4))

        self.selected_labels = {}
        self.radio_vars = {}
        for axis in ("X", "Y", "Z"):
            group = Frame(coord_row, bg=BG_FOOTER)
            group.pack(side=LEFT, padx=18)
            top = Frame(group, bg=BG_FOOTER)
            top.pack()
            Label(top, text=axis, bg=BG_FOOTER, fg=STEEL,
                  font=(self.font, 13, "bold")).pack(side=LEFT, padx=(0, 8))
            val_lbl = Label(top, text="-", bg=BG_FOOTER, fg=TEXT_MUTED,
                             font=(self.font, 13, "bold"))
            val_lbl.pack(side=LEFT)
            self.selected_labels[axis] = val_lbl

            var = IntVar(value=-1)
            self.radio_vars[axis] = var
            btn_row = Frame(group, bg=BG_FOOTER)
            btn_row.pack(pady=(6, 0))
            for v in range(4):
                rb = Radiobutton(
                    btn_row, text=str(v), variable=var, value=v,
                    indicatoron=False, width=2, font=(self.font, 10, "bold"),
                    bg=CELL_BG, fg=TEXT_LIGHT, selectcolor=GOLD,
                    activebackground=CELL_HOVER, relief=FLAT, bd=1,
                    highlightthickness=0, cursor="hand2",
                    command=lambda a=axis, v=v: self._select_axis(a, v),
                )
                rb.pack(side=LEFT, padx=1)

        btn_row2 = Frame(footer, bg=BG_FOOTER)
        btn_row2.pack(pady=(10, 6))

        self.enter_btn = Button(
            btn_row2, text="CONFIRMAR JUGADA", command=self.make_move,
            bg=GOLD, fg="#14161a", activebackground=GOLD_DIM,
            relief=FLAT, bd=0, font=(self.font, 11, "bold"),
            width=20, height=1, cursor="hand2",
        )
        self.enter_btn.pack(side=LEFT, padx=6)

        self.new_game_btn = Button(
            btn_row2, text="NUEVA PARTIDA", command=self.request_rematch,
            bg=BG_PANEL, fg=STEEL, activebackground=STEEL_DIM,
            relief=FLAT, bd=0, font=(self.font, 11, "bold"),
            width=16, height=1, cursor="hand2", state=DISABLED,
        )
        self.new_game_btn.pack(side=LEFT, padx=6)

        Button(
            btn_row2, text="SALIR", command=self.on_close,
            bg=BG_PANEL, fg=TEXT_DANGER, activebackground="#3a2323",
            relief=FLAT, bd=0, font=(self.font, 11, "bold"),
            width=10, height=1, cursor="hand2",
        ).pack(side=LEFT, padx=6)

        self.msg_label = Label(footer, text="Esperando al otro jugador...",
                                bg=BG_FOOTER, fg=TEXT_MUTED,
                                font=(self.font, 10))
        self.msg_label.pack(pady=(0, 12))

        self._draw_empty_grid()

    def _copy_code(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.room_id)

    def _select_axis(self, axis, value):
        self.selected[axis] = value
        self.selected_labels[axis].config(text=str(value), fg=GOLD)

    # -- coordenadas de celda -> coordenadas de canvas -------------------
    def _cell_coords(self, Z, Y, X):
        x0 = Z * self.SLICE_W + X * self.CELL_W
        y0 = (3 - Z) * self.SLICE_H + Y * self.CELL_H
        return x0, y0, x0 + self.CELL_W, y0 + self.CELL_H

    def _draw_empty_grid(self):
        self.canvas.delete("all")
        for Z in range(4):
            for Y in range(4):
                for X in range(4):
                    x0, y0, x1, y1 = self._cell_coords(Z, Y, X)
                    self.canvas.create_rectangle(
                        x0 + 1, y0 + 1, x1, y1,
                        outline=CELL_BORDER, width=2, fill=CELL_BG,
                    )
            # etiqueta de cada "rebanada" (slice) Z
            self.canvas.create_text(
                Z * self.SLICE_W + 8, (3 - Z) * self.SLICE_H + 12,
                text=f"Z{Z}", anchor="w", fill=TEXT_MUTED,
                font=(self.font, 9, "bold"),
            )

    def _render_board(self):
        self.canvas.delete("all")
        for Z in range(4):
            for Y in range(4):
                for X in range(4):
                    x0, y0, x1, y1 = self._cell_coords(Z, Y, X)
                    val = self.board[Z][Y][X]
                    fill = CELL_BG
                    outline = CELL_BORDER
                    self.canvas.create_rectangle(
                        x0 + 1, y0 + 1, x1, y1,
                        outline=outline, width=2, fill=fill,
                    )
                    if val != 0:
                        symbol = "O" if val == -1 else "X"
                        color = O_COLOR if val == -1 else X_COLOR
                        self.canvas.create_text(
                            (x0 + x1) / 2, (y0 + y1) / 2,
                            text=symbol, font=(self.font, 20, "bold"),
                            fill=color,
                        )
            self.canvas.create_text(
                Z * self.SLICE_W + 8, (3 - Z) * self.SLICE_H + 12,
                text=f"Z{Z}", anchor="w", fill=TEXT_MUTED,
                font=(self.font, 9, "bold"),
            )

        if self.win_line:
            for (Z, Y, X) in self.win_line:
                x0, y0, x1, y1 = self._cell_coords(Z, Y, X)
                self.canvas.create_rectangle(
                    x0 + 1, y0 + 1, x1, y1, outline=GOLD, width=3,
                    fill=CRIMSON,
                )
                val = self.board[Z][Y][X]
                symbol = "O" if val == -1 else "X"
                self.canvas.create_text(
                    (x0 + x1) / 2, (y0 + y1) / 2, text=symbol,
                    font=(self.font, 20, "bold"), fill=CRIMSON_TEXT,
                )

    # -- Firebase: escuchar cambios --------------------------------------
    def _start_stream(self):
        def handler(message):
            self.msg_queue.put(message)

        self.stream = self.db.child("games").child(self.room_id).stream(handler)

    def _poll_queue(self):
        got_update = False
        try:
            while True:
                self.msg_queue.get_nowait()
                got_update = True
        except queue.Empty:
            pass
        if got_update:
            self.refresh_from_server()
        self.root.after(150, self._poll_queue)

    def refresh_from_server(self):
        try:
            data = self.db.child("games").child(self.room_id).get().val()
        except Exception:
            return
        if not data:
            return
        self.board = data.get("board") or new_empty_board()
        self.turn = data.get("turn", 0)
        self.status = data.get("status", "waiting")
        self.winner = data.get("winner")
        win_line = data.get("winLine")
        self.win_line = [tuple(c) for c in win_line] if win_line else None
        self._render_board()
        self._update_status_labels(data)

    def _update_status_labels(self, data):
        players = data.get("players") or {}
        my_turn = (self.status == "playing" and self.turn == self.player_index)

        if self.status == "waiting":
            self.turn_label.config(text="Esperando al Jugador 2...", fg=TEXT_MUTED)
            self.msg_label.config(text=f"Comparte el codigo '{self.room_id}' con tu rival.")
            state = DISABLED
        elif self.status == "playing":
            turn_name = PLAYER_LABELS[self.turn]
            turn_color = PLAYER_COLOR[self.turn]
            self.turn_label.config(text=f"Turno de: {turn_name}", fg=turn_color)
            self.msg_label.config(
                text="Es tu turno: elige X, Y, Z y confirma." if my_turn
                else "Esperando la jugada del rival...",
                fg=GOLD if my_turn else TEXT_MUTED,
            )
            state = NORMAL if my_turn else DISABLED
        else:  # finished
            if self.winner is None:
                self.turn_label.config(text="Empate", fg=TEXT_MUTED)
                self.msg_label.config(text="Tablero completo, sin ganador.", fg=TEXT_MUTED)
            else:
                winner_name = PLAYER_LABELS[self.winner]
                winner_color = PLAYER_COLOR[self.winner]
                self.turn_label.config(text=f"Gano: {winner_name}", fg=winner_color)
                if self.winner == self.player_index:
                    self.msg_label.config(text="Ganaste la partida.", fg=GOLD)
                else:
                    self.msg_label.config(text="Tu rival gano esta partida.", fg=TEXT_DANGER)
            state = DISABLED

        self.enter_btn.config(state=state)
        for var_group in self.radio_vars.values():
            pass  # los radiobuttons quedan visibles; solo bloqueamos Enter
        self.new_game_btn.config(
            state=NORMAL if self.status == "finished" else DISABLED
        )

    # -- jugar -------------------------------------------------------------
    def make_move(self):
        if self.status != "playing" or self.turn != self.player_index:
            return
        Z, Y, X = self.selected["Z"], self.selected["Y"], self.selected["X"]
        if Z is None or Y is None or X is None:
            self.msg_label.config(text="Selecciona X, Y y Z antes de confirmar.",
                                   fg=TEXT_DANGER)
            return
        if self.board[Z][Y][X] != 0:
            self.msg_label.config(text="Esa celda ya esta ocupada.", fg=TEXT_DANGER)
            return

        new_board = copy.deepcopy(self.board)
        value = -1 if self.player_index == 0 else 1
        new_board[Z][Y][X] = value

        win_line = find_winning_line(new_board, Z, Y, X)
        if win_line:
            update = {
                "board": new_board,
                "status": "finished",
                "winner": self.player_index,
                "winLine": [list(c) for c in win_line],
            }
        elif board_is_full(new_board):
            update = {
                "board": new_board,
                "status": "finished",
                "winner": None,
                "winLine": None,
            }
        else:
            update = {
                "board": new_board,
                "turn": 1 - self.turn,
                "status": "playing",
            }

        try:
            self.db.child("games").child(self.room_id).update(update)
        except Exception as exc:
            self.msg_label.config(text=f"Error de red: {exc}", fg=TEXT_DANGER)
            return

        # respuesta inmediata en pantalla, sin esperar el eco del servidor
        self.board = new_board
        self.turn = update.get("turn", self.turn)
        self.status = update["status"]
        self.winner = update.get("winner", self.winner)
        self.win_line = win_line
        self._render_board()

    def request_rematch(self):
        if self.status != "finished":
            return
        update = {
            "board": new_empty_board(),
            "turn": 0,
            "status": "playing",
            "winner": None,
            "winLine": None,
        }
        try:
            self.db.child("games").child(self.room_id).update(update)
        except Exception as exc:
            self.msg_label.config(text=f"Error de red: {exc}", fg=TEXT_DANGER)

    def on_close(self):
        if messagebox.askyesno("Salir", "Quieres salir de la partida?"):
            try:
                if self.stream:
                    self.stream.close()
            except Exception:
                pass
            self.root.destroy()


# ---------------------------------------------------------------------------
def launch_game(firebase_app, db, room_id, player_index):
    Game(firebase_app, db, room_id, player_index)


if __name__ == "__main__":
    Lobby(on_ready=launch_game)
