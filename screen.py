class Object:
    def __init__(self, matrix, texture: dict) -> None:
        self.matrix = matrix
        self.texture = texture

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
                pxwidth = len(fill)
                self.matrix[posy][ptrx:ptrx+pxwidth] = fill
                posx += 1
                ptrx += pxwidth
            posy += 1
