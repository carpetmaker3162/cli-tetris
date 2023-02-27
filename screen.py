class Object:
    def __init__(self, matrix, texture: dict, pixel_size: int=1, border: bool=False) -> None:
        """An object that can be written to a `Screen`"""
        self.matrix = matrix
        self.texture = texture
        self.border = border
        self.pixel_size = pixel_size
        self.width = len(self.matrix[0])
        self.height = len(self.matrix)

class Screen:
    def __init__(self, width, height, default_fill = " ") -> None:
        """
        A simple terminal rasterizer that helps with drawing something on a certain coordinate position
        on the terminal screen
        As of now there isn't anything to handle exceptions with objects going out of bounds.
        """
        self.width = width
        self.height = height
        self.matrix = [[default_fill]*width for _ in range(height)]
    
    def display(self):
        """
        Display the screen on the terminal window
        """
        buffer = str()
        print("\033[H", end="\n\r")
        for row in self.matrix:
            buffer += "".join(row) + "\n\r"
        print(buffer, end="")
    
    def draw(self, x: int, y: int, object: Object):
        """
        Draw an `Object` on a specified `x` and `y` location.
        If the Object has a border, the top left corner of the Object itself will end up at the 
        specified `x` and `y` location, not the top left corner of the Object's border
        """
        posy = y
        while posy < y + object.height:
            posx = x
            ptrx = posx
            while posx < x + object.width:
                px = object.matrix[posy - y][posx - x]
                fill = object.texture.get(px, str(px))
                # lay out the current cell across 1 or multiple positions on the actual terminal screen.
                # in this particular program, `fill` is an instance of the `ANSI` class defined in utils.py
                self.matrix[posy + object.border][ptrx + object.border:
                                                  ptrx + object.border + object.pixel_size] = fill
                posx += 1
                ptrx += object.pixel_size
            posy += 1
        
        # draw out a border (yes there is only 1 type of border supported shut up)
        if object.border:
            posy = y
            posx = x
            actual_width = object.width * object.pixel_size
            self.matrix[posy][posx:posx + actual_width + 2] = ("┌" + "─" * actual_width + "┐")
            posy += 1
            while posy < y + object.height + 1:
                self.matrix[posy][posx] = "│"
                self.matrix[posy][posx + actual_width + 1] = "│"
                posy += 1
            self.matrix[posy][posx:posx + actual_width + 2] = ("└" + "─" * actual_width + "┘")