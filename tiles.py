class Tile(object):
    def __init__(self, passable, fog=False, seen=False):
        self.passable = passable

        if not fog:
            fog = not passable

        self.fog = fog
        self.seen = seen


class Room(object):
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def centre(self):
        centre_x = (self.x1 + self.x2) / 2
        centre_y = (self.y1 + self.y2) / 2

        return centre_x, centre_y

    def intersect(self, block):
        return (self.x1 <= block.x2 and self.x2 >= block.x1
                and self.y1 <= block.y2 and self.y2 >= block.y1)
