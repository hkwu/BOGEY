import random
import libtcodpy as libt

# Consts
SCREEN_WIDTH = 150
SCREEN_HEIGHT = 20
MAP_WIDTH = int(0.7 * SCREEN_WIDTH)
MAP_HEIGHT = SCREEN_HEIGHT

# Colours
COLOUR_WALL = libt.Color(0, 0, 100)
COLOUR_GROUND = libt.black

# Room data
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 2
MAX_ROOMS = 30

# Set the fonts, initialize window
libt.console_set_custom_font("terminal16x16_gs_ro.png", 
                                  libt.FONT_TYPE_GREYSCALE 
                                  | libt.FONT_LAYOUT_TCOD)
libt.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, "Bogue", False)

# scrn-screen consoles
scrn = libt.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)


# Classes
class Entity(object):
    def __init__(self, x, y, char, colour):
        self.x = x
        self.y = y
        self.char = char
        self.colour = colour

    def move(self, dx, dy):
        if self.x + dx >= 0 and self.x + dx < MAP_WIDTH \
           and world[self.x + dx][self.y].passable:
            self.x += dx
        if self.y + dy >= 0 and self.y + dy < MAP_HEIGHT \
           and world[self.x][self.y + dy].passable:
            self.y += dy

    def draw(self):
        libt.console_set_default_foreground(scrn, self.colour)
        libt.console_put_char(scrn, self.x, self.y, self.char, libt.BKGND_NONE)

    def clear(self):
        libt.console_put_char(scrn, self.x, self.y, " ", libt.BKGND_NONE)


class Tile(object):
    def __init__(self, passable, fog=False):
        self.passable = passable

        if not fog:
            fog = not passable

        self.fog = fog


class Block(object):
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.x2 = x + w
        self.y2 = y + h

    def centre(self):
        centre_x = (self.x + self.x2) / 2
        centre_y = (self.y + self.y2) / 2

        return (centre_x, centre_y)

    def intersect(self, block):
        return (self.x1 <= block.x2 and self.x2 >= block.x1
                and self.y1 <= block.y2 and self.y2 >= block.y1)


# Map creation functions
def make_map():
    global world
    world = []

    for i in range(MAP_WIDTH):
        world.append([])
        for j in range(MAP_HEIGHT):
            world[i].append(Tile(False))

    rooms = []
    num_rooms = 0

    for num in range(MAX_ROOMS):
        w = random.randrange(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = random.randrange(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        x = random.randrange(MAP_WIDTH - w - 1)
        y = random.randrange(MAP_HEIGHT - h - 1)

        new = Block(x, y, w, h)
        intersected = False

        for room in rooms:
            if new.intersect(room):
                intersected = True
                break

        if not intersected and num_rooms == 0:
            (player_x, player_y) = new.centre()
            player.x = player_x
            player.y = player_y
            make_room(new)
        elif not intersected:
            make_room(new)


def make_h_tunnel(x1, x2, y):
    global world

    for x in range(min(x1, x2), max(x1, x2) + 1):
        world[x][y].passable = True
        world[x][y].fog = False


def make_v_tunnel(y1, y2, x):
    global world

    for y in range(min(y1, y2), max(y1, y2) + 1):
        world[x][y].passable = True
        world[x][y].fog = False


def make_room(room):
    global world

    for i in range(room.x + 1, room.x2):
        for j in range(room.y + 1, room.y2):
            world[i][j].passable = True
            world[i][j].fog = False


# Other functions
def render_obj():
    for i in range(MAP_WIDTH):
        for j in range(MAP_HEIGHT):
            fog = world[i][j].fog

            if fog:
                libt.console_set_char_background(scrn, i, j, COLOUR_WALL, libt.BKGND_SET)
            else:
                libt.console_set_char_background(scrn, i, j, COLOUR_GROUND, libt.BKGND_SET)

    for obj in objects:
        obj.draw()

    libt.console_blit(scrn, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)


def keybinds():
    key = libt.console_wait_for_keypress(True)

    if key.vk == libt.KEY_ENTER and key.lalt:
        libt.console_set_fullscreen(not libt.console_is_fullscreen())
    elif key.vk == libt.KEY_ESCAPE:
        return True

    if libt.console_is_key_pressed(libt.KEY_UP):
        player.move(0, -1)
    elif libt.console_is_key_pressed(libt.KEY_DOWN):
        player.move(0, 1)
    elif libt.console_is_key_pressed(libt.KEY_LEFT):
        player.move(-1, 0)
    elif libt.console_is_key_pressed(libt.KEY_RIGHT):
        player.move(1, 0)

# Class instances
player = Entity(54, 6, "@", libt.white)
npc = Entity(MAP_WIDTH / 2 + 2, MAP_HEIGHT / 2 + 2, "@", libt.yellow)
objects = [player]

make_map()

# Main loop
while not libt.console_is_window_closed():
    render_obj()
    libt.console_flush()

    for obj in objects:
        obj.clear()

    if keybinds():
        break
