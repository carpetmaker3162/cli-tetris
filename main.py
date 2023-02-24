import sys
import threading
import random
import os
import termios
import time
import math
from utils import getch
from utils import Fmt
from utils import Controls as Ctrls

WINDOWS = os.name == "nt"
fd = sys.stdin.fileno()
old_settings = termios.tcgetattr(fd)

event_queue = []
BLOCK = "  "

def colored_block(ansi):
    return f"{ansi}{BLOCK}{Fmt.end}"

TEXTURE = {
    0: ". ",
    1: colored_block(Fmt.red_highlight_text),
    2: colored_block(Fmt.yellow_highlight_text),
    3: colored_block(Fmt.green_highlight_text),
    4: colored_block(Fmt.cyan_highlight_text),
    5: colored_block(Fmt.blue_highlight_text),
    6: colored_block(Fmt.magenta_highlight_text),
    7: colored_block(Fmt.light_gray_highlight_text),
    8: colored_block(Fmt.gray_highlight_text),
}

BLOCKS = { # first coordinate is centre of block
    0: [(0, 4), (0, 5), (1, 4), (1, 5)], # square
    1: [(0, 4), (0, 3), (0, 5), (0, 6)], # straight
    2: [(1, 4), (0, 4), (2, 4), (2, 5)], # L
    3: [(1, 5), (0, 4), (1, 4), (2, 5)], # skew
    4: [(0, 5), (0, 4), (0, 6), (1, 5)], # T
}

POINTS_GIVEN = {
    1: 40,
    2: 100,
    3: 300,
    4: 1200,
}

def process_keyboard_events(q):
    while True:
        q.append(getch())

class Block:
    def __init__(self, block: int, color: int) -> None:
        assert block in range(0, 5)
        assert color in range(1, 9)

        self.squares = BLOCKS[block][:]
        self.id = block
        self.color = color
        self.centre = self.squares[0]
    
    @classmethod
    def random(cls):
        return cls(random.randrange(0, 5), random.randrange(1, 9))
    
    def update_centre(self):
        self.centre = self.squares[0]

class Game:
    def __init__(self) -> None:
        self.width = 10
        self.height = 20
        self.grid = [[0 for i in range(self.width)] for i in range(self.height)]
        self.active_block = Block.random() # collection of row #'s and col #'s
        self.next_block = Block.random()
        self.score = 0
        for br, bc in self.active_block.squares:
            self.grid[br][bc] = self.active_block.color

    def refresh_scene(self):
        if not self.block_can_fall(self.grid, self.active_block):
            # check for filled rows
            r = self.height - 1
            rows_cleared = 0
            while r > 0:
                if all([x != 0 for x in self.grid[r]]):
                    rows_cleared += 1
                    self.remove_row(r)
                    continue
                r -= 1 
            self.score += POINTS_GIVEN.get(rows_cleared, 0)
            self.active_block = Block(self.next_block.id, self.next_block.color)
            self.next_block = Block.random()
            for br, bc in self.active_block.squares:
                if self.grid[br][bc] != 0:
                    return -1
            self.draw_block(self.active_block)
        else:
            for br, bc in self.active_block.squares:
                self.grid[br][bc] = 0
            self.grid = self.apply_gravity(self.grid, self.active_block)
            self.draw_block(self.active_block)
        return 0
    
    def remove_row(self, r: int):
        for i in range(self.width): # clear the row
            self.grid[r][i] = 0
        for i in range(r, 0, -1):
            self.grid[i] = self.grid[i-1][:]

    def move_block(self, block: Block, newpos: list=None, displacement: tuple=(0, 0)):
        dy, dx = displacement
        
        if newpos is None:
            new_position = block.squares[:]
        else:
            new_position = newpos[:]
        
        for i in range(len(new_position)):
            r, c = new_position[i]
            new_position[i] = (r+dy, c+dx)
        
        for r, c in new_position:
            if not (0<=r<self.height and 0<=c<self.width):
                return -1
            elif self.grid[r][c] != 0 and (r, c) not in block.squares:
                return -1
        
        for r, c in block.squares:
            self.grid[r][c] = 0
        
        block.squares = new_position[:]
        return 0
    
    def rotate_block(self, block: Block): # times cw
        block.update_centre()
        oy, ox = block.centre
        localspace_squares = block.squares[:]
        globalspace_squares = []
        for i, sq in enumerate(localspace_squares): # convert to localspace
            y, x = sq
            localspace_squares[i] = (y-oy, x-ox)
        for bx, by in localspace_squares: # calculate new positions in localspace
            nx = -by
            ny = bx
            globalspace_squares.append((nx, ny))
        for i, sq in enumerate(globalspace_squares): # convert to globalspace and check
            y, x = sq
            ny, nx = y+oy, x+ox
            if not (0<=ny<self.height and 0<=nx<self.width):
                return -1
            elif self.grid[ny][nx] != 0 and (ny, nx) not in block.squares:
                return -1
            globalspace_squares[i] = (ny, nx)
        for r, c in block.squares:
            self.grid[r][c] = 0
        
        block.squares = globalspace_squares[:]
        block.update_centre()
        return 0
    
    def draw_block(self, block: Block):
        for br, bc in block.squares:
            self.grid[br][bc] = block.color
    
    def block_can_fall(self, grid, block: Block):
        for br, bc in block.squares:
            if br == self.height - 1:
                return False
            elif grid[br+1][bc] != 0 and all([br > r for r, c in block.squares if c == bc and r != br]):
                return False
        return True

    def apply_gravity(self, grid, block: Block): # apply gravity to a grid
        new_grid = [x[:] for x in grid[:]]
        # new_block = [x[:] for x in active_block.squares[:]]
        for i, _ in enumerate(block.squares):
            block.squares[i] = (block.squares[i][0] + 1, block.squares[i][1])
        block.update_centre()
        return new_grid
    
    def print(self):
        # ┌────┐
        # │    │
        # └────┘
        print("\033[H", end="\n\r")
        print(self.score, end="\n\r")
        buf = str()
        buf += "┌" + "─" * self.width * 2 + "┐\n\r"
        for r, row in enumerate(self.grid):
            buf += "│"
            
            for c, cell in enumerate(row):
                buf += TEXTURE[cell]
            
            buf += "│"
            buf += "\n\r"
        buf += "└" + "─" * self.width * 2 + "┘"
        print(buf, end="")

if __name__ == "__main__":
    try:
        last_update = 0
        thread = threading.Thread(target=process_keyboard_events, args=(event_queue,), daemon=True)
        thread.start()

        tetris = Game()

        while True:
            if event_queue:
                key = event_queue.pop(0)
                if ord(key) == 3:
                    break
                elif key == Ctrls.LEFT:
                    tetris.move_block(tetris.active_block, displacement=(0, -1))
                elif key == Ctrls.RIGHT:
                    tetris.move_block(tetris.active_block, displacement=(0, 1))
                elif key == Ctrls.DOWN:
                    tetris.move_block(tetris.active_block, displacement=(1, 0))
                elif key == Ctrls.DROP:
                    while tetris.move_block(tetris.active_block, displacement=(1, 0)) != -1:
                        pass
                elif key == Ctrls.ROTATE_CW:
                    for i in range(3):
                        tetris.rotate_block(tetris.active_block)
                elif key == Ctrls.ROTATE_CCW:
                    tetris.rotate_block(tetris.active_block)
                tetris.draw_block(tetris.active_block)
                
                sys.stdout.flush()
            
            if time.time() - last_update > 0.2:
                status = tetris.refresh_scene()
                tetris.print()
                last_update = time.time()
                if status == -1:
                    break

    except Exception as e:
        raise e
    finally:
        print("\r")
        if not WINDOWS:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
