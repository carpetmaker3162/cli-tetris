class Object:
    def __init__(self, matrix, texture: dict, pixel_size: int=1, border: bool=False) -> None:
        self.matrix = matrix
        self.texture = texture
        self.border = border
        self.pixel_size = pixel_size
        self.width = len(self.matrix[0])
        self.height = len(self.matrix)

class Screen:
    def __init__(self, width, height, default_fill = " ") -> None:
        self.width = width
        self.height = height
        self.matrix = [[default_fill]*width for _ in range(height)]
    
    def display(self):
        buffer = str()
        print("\033[H", end="\n\r")
        for row in self.matrix:
            buffer += "".join(row) + "\n\r"
        print(buffer, end="")
    
    def draw(self, x: int, y: int, object: Object):
        posy = y
        while posy < y + len(object.matrix):
            posx = x
            ptrx = posx
            while posx < x + len(object.matrix[posy - y]):
                px = object.matrix[posy - y][posx - x]
                fill = object.texture.get(px, "?")
                self.matrix[posy + object.border][ptrx + object.border : ptrx + object.pixel_size + object.border] = fill
                posx += 1
                ptrx += object.pixel_size
            posy += 1
        posy = y
        posx = x
        actual_width = object.width * object.pixel_size
        if object.border:
            self.matrix[posy][posx:posx + actual_width + 2] = ("┌" + "─" * actual_width + "┐")
            posy += 1
            while posy < y + object.height + 1:
                self.matrix[posy][posx] = "│"
                self.matrix[posy][posx + actual_width + 1] = "│"
                posy += 1
            self.matrix[posy][posx:posx + actual_width + 2] = ("└" + "─" * actual_width + "┘")