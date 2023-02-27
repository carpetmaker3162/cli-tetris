import sys
import threading
import random
import os
import time
from utils import getch, log
from utils import Fmt, Controls, ANSI
from screen import Screen, Object

WINDOWS = os.name == "nt"

if not WINDOWS:
    import termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

event_queue = []

BLOCK = "  "
LEFT = Controls.LEFT
RIGHT = Controls.RIGHT
DOWN = Controls.DOWN
DROP = Controls.DROP
ROTATE_CW = Controls.ROTATE_CW
ROTATE_CCW = Controls.ROTATE_CCW
PAUSE = Controls.PAUSE

ACTIONS = [LEFT, RIGHT, DOWN, DROP, ROTATE_CW, ROTATE_CCW]

def colored_block(ansi):
    return ANSI(ansi, BLOCK)

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

# initial positions that the blocks occupy
BLOCKS = { # first coordinate is centre of block
    0: [(0, 4), (0, 5), (1, 4), (1, 5)], # square
    1: [(0, 4), (0, 3), (0, 5), (0, 6)], # straight
    2: [(1, 4), (0, 4), (2, 4), (2, 5)], # L
    3: [(1, 5), (0, 4), (1, 4), (2, 5)], # skew
    4: [(0, 5), (0, 4), (0, 6), (1, 5)], # T
}

# amount of points given for # of new rows cleared after a block is placed
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

        self.squares = BLOCKS[block][:] # squares that the block occupies
        self.type = block
        self.color = color
        self.centre = self.squares[0]
    
    @classmethod
    def random(cls):
        return cls(random.randrange(0, 5), random.randrange(1, 9))
    
    def update_centre(self):
        self.centre = self.squares[0]
    
    def as_matrix(self):
        # draw the block onto a small 5x5 matrix and return it
        minx = min([x[1] for x in self.squares])
        miny = min([x[0] for x in self.squares])
        self.localspace_squares = self.squares[:]
        for i, sq in enumerate(self.localspace_squares):
            y, x = sq
            self.localspace_squares[i] = (x - minx, y - miny)
        matrix = [[0 for i in range(5)] for i in range(5)]
        for y, x in self.localspace_squares:
            matrix[x+1][y+1] = self.color
        return matrix

class Game:
    def __init__(self) -> None:
        self.width = 10
        self.height = 20
        self.grid = [[0 for i in range(self.width)] for i in range(self.height)]
        self.active_block = Block.random()
        self.next_block = Block.random()
        self.score = 0
        
        # draw the first block
        for br, bc in self.active_block.squares:
            self.grid[br][bc] = self.active_block.color
        
        w, h = os.get_terminal_size()
        # h-2 to leave space for terminal bottom and the invokation line
        self.screen = Screen(w, h-2, default_fill=" ")

    def refresh_scene(self, apply_grav: bool=True):
        if not self.block_can_fall(self.grid, self.active_block):
            # check for filled rows
            r = self.height - 1
            rows_cleared = 0
            while r > 0:
                # if entire row is filled
                if all([x != 0 for x in self.grid[r]]):
                    rows_cleared += 1
                    self.remove_row(r)
                    continue
                r -= 1
            self.score += POINTS_GIVEN.get(rows_cleared, 0)
            # the active block is now what was previously the next block
            self.active_block = Block(self.next_block.type, self.next_block.color)
            self.next_block = Block.random()
            # check for game end (if the spawned block's position is already occupied by another 
            # square, it means the game is over as blocks have reached the ceiling)
            for br, bc in self.active_block.squares:
                if self.grid[br][bc] != 0:
                    return -1
        else:
            # erase the current block (and re-draw it later)
            for br, bc in self.active_block.squares:
                self.grid[br][bc] = 0
            # apply gravity if the block can fall
            if apply_grav:
                self.grid = self.apply_gravity(self.grid, self.active_block)
        self.draw_block(self.active_block)
        return 0
    
    def remove_row(self, r: int):
        # clear the row
        for i in range(self.width):
            self.grid[r][i] = 0
        # shift everything above down by 1
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
        # update the objects on the screen
        self.next_block_obj = Object(
            self.next_block.as_matrix(),
            TEXTURE,
            pixel_size=2,
            border=True)
        
        self.grid_obj = Object(
            self.grid,
            TEXTURE,
            pixel_size=2,
            border=True)
        
        self.score_obj = Object(
            [[*str(self.score)]], # quick and lazy and unreadable way of converting a string into "matrix" format
            {},
            pixel_size=1)
        
        # draw the block on the grid
        for br, bc in block.squares:
            self.grid[br][bc] = block.color
    
    def block_can_fall(self, grid, block: Block):
        for br, bc in block.squares:
            on_bottom_of_block = all([br > r for r, c in block.squares if c == bc and r != br])
            # if block has reached the bottom of the screen
            if br == self.height - 1:
                return False
            # if block below square is occupied and the square is on the bottom of the block
            elif grid[br+1][bc] != 0 and on_bottom_of_block:
                return False
        return True

    def apply_gravity(self, grid, block: Block): # apply gravity to a grid
        new_grid = [x[:] for x in grid[:]]
        for i, _ in enumerate(block.squares):
            block.squares[i] = (block.squares[i][0] + 1, block.squares[i][1])
        block.update_centre()
        return new_grid
    
    def print(self):
        self.next_block_label = Object([[*"Next"]], {}, pixel_size=1)
        self.screen.draw(0, 0, self.score_obj)
        self.screen.draw(0, 1, self.grid_obj)
        # self.width * 2 because each block is 2 chars long on the screen
        self.screen.draw(self.width * 2 + 3, 2, self.next_block_obj)
        self.screen.draw(self.width * 2 + 7, 1, self.next_block_label)
        self.screen.display()
        
if __name__ == "__main__":
    try:
        last_update = 0

        # start a separate thread for processing keyboard events
        thread = threading.Thread(target=process_keyboard_events, args=(event_queue,), daemon=True)
        thread.start()

        tetris = Game()
        while True:
            if event_queue:
                key = event_queue.pop(0)
                if key == PAUSE:
                    while True:
                        if event_queue:
                            k = event_queue.pop(0)
                            if k == PAUSE:
                                break
                            elif ord(k) == 3:
                                key = "\x03" # lmao
                                break
                if ord(key) == 3:
                    break 
                elif key == LEFT:
                    tetris.move_block(tetris.active_block, displacement=(0, -1))
                elif key == RIGHT:
                    tetris.move_block(tetris.active_block, displacement=(0, 1))
                elif key == DOWN:
                    tetris.move_block(tetris.active_block, displacement=(1, 0))
                elif key == DROP:
                    while tetris.move_block(tetris.active_block, displacement=(1, 0)) != -1:
                        pass
                elif key == ROTATE_CW:
                    for i in range(3):
                        tetris.rotate_block(tetris.active_block)
                elif key == ROTATE_CCW:
                    tetris.rotate_block(tetris.active_block)
                
                # re-print the screen right after a keyboard event is registered
                if key in ACTIONS:
                    status = tetris.refresh_scene(apply_grav=False)
                    tetris.print()
                    if status == -1:
                        break
                
                sys.stdout.flush()
            
            # apply gravity every 0.4 seconds
            if time.time() - last_update > 0.4:
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
