import random
import libtcodpy as libt

# Consts
SCREEN_WIDTH = 180
SCREEN_HEIGHT = 100
MAP_WIDTH = SCREEN_WIDTH
MAP_HEIGHT = int(0.7 * SCREEN_HEIGHT)

# Colours
COLOURS = {
    'bg': libt.white,
    'wall': libt.Color(164, 164, 164),
    'lit_wall': libt.Color(173, 173, 0),
    'ground': libt.Color(21, 21, 21),
    'lit_ground': libt.Color(160, 160, 160),
    'text': libt.Color(164, 164, 164)
}

# Room data
ROOM_MAX_SIZE = 25
ROOM_MIN_SIZE = 5
MAX_ROOMS = 50

# FOV
FOV = 0
FOV_LIT_WALLS = True
LIGHT_RANGE = 10
fov_refresh = True

# Set the fonts, initialize window
libt.console_set_custom_font("dejavu10x10_gs_tc.png", 
                             libt.FONT_TYPE_GREYSCALE 
                             | libt.FONT_LAYOUT_TCOD)
libt.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, "Bogey", False)

# Keypress delay
libt.console_set_keyboard_repeat(50, 100)

# Screen consoles
sketch1 = libt.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)


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
        if libt.map_is_in_fov(fov_map, self.x, self.y):
            libt.console_set_default_foreground(sketch1, self.colour)
            libt.console_put_char(sketch1, self.x, self.y, self.char, libt.BKGND_NONE)

    def clear(self):
        libt.console_put_char(sketch1, self.x, self.y, " ", libt.BKGND_NONE)


class Tile(object):
    def __init__(self, passable, fog=False, seen=False):
        self.passable = passable

        if not fog:
            fog = not passable

        self.fog = fog
        self.seen = seen


class Block(object):
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def centre(self):
        centre_x = (self.x1 + self.x2) / 2
        centre_y = (self.y1 + self.y2) / 2

        return (centre_x, centre_y)

    def intersect(self, block):
        return (self.x1 <= block.x2 and self.x2 >= block.x1
                and self.y1 <= block.y2 and self.y2 >= block.y1)


# Map creation functions
def make_map():
    """Initializes the game world."""
    global world
    world = []

    # Initialize the multi-dimensional array with unpassable tiles
    for i in range(MAP_WIDTH):
        world.append([])
        for j in range(MAP_HEIGHT):
            world[i].append(Tile(False))

    rooms = []
    num_rooms = 0

    # Fill array with passable tiles that represent up to MAX_ROOMS
    # number of rooms
    for num in range(MAX_ROOMS):
        w = random.randrange(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = random.randrange(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        x = random.randrange(MAP_WIDTH - w - 1)
        y = random.randrange(MAP_HEIGHT - h - 1)

        new = Block(x, y, w, h)
        intersected = False

        # Check for overlaps, stop if room overlaps old ones
        for room in rooms:
            if new.intersect(room):
                intersected = True
                break

        # Create new rooms if no intersections with previous rooms exist
        # Otherwise link rooms to each other
        if not intersected and num_rooms == 0:
            (player_x, player_y) = new.centre()
            player.x = player_x
            player.y = player_y

            num_rooms += 1
            rooms.append(new)
            make_room(new)
        elif not intersected:
            num_rooms += 1
            rooms.append(new)
            make_room(new)
            connect_rooms(rooms[num_rooms - 2], rooms[num_rooms - 1])


def make_h_tunnel(x1, x2, y):
    """Creates passable tiles between x1 and x2 on the y coordinate."""
    global world

    for x in range(min(x1, x2), max(x1, x2) + 1):
        world[x][y].passable = True
        world[x][y].fog = False


def make_v_tunnel(y1, y2, x):
    """Creates passable tiles between y1 and y2 on the x coordinate."""
    global world

    for y in range(min(y1, y2), max(y1, y2) + 1):
        world[x][y].passable = True
        world[x][y].fog = False


def connect_rooms(room1, room2):
    """Takes two rooms and connects them with tunnels."""
    (r1_x, r1_y) = room1.centre()
    (r2_x, r2_y) = room2.centre()

    # Determine which direction to begin the connection
    # 0 is vertical, 1 is horizontal
    direction = random.randrange(2)

    if direction:
        make_h_tunnel(r1_x, r2_x, r1_y)
        make_v_tunnel(r1_y, r2_y, r2_x)
    else:
        make_v_tunnel(r1_y, r2_y, r1_x)
        make_h_tunnel(r1_x, r2_x, r2_y)


def make_room(room):
    """Takes an instance of a Room and creates it on the game world."""
    global world

    for i in range(room.x1 + 1, room.x2):
        for j in range(room.y1 + 1, room.y2):
            world[i][j].passable = True
            world[i][j].fog = False


# Other functions
def render_obj():
    if fov_refresh:
        global fov_refresh
        fov_refresh = False
        libt.map_compute_fov(fov_map, player.x, player.y, 
                             LIGHT_RANGE, FOV_LIT_WALLS, FOV)

        for i in range(MAP_WIDTH):
            for j in range(MAP_HEIGHT):
                fog = world[i][j].fog
                visible = libt.map_is_in_fov(fov_map, i, j)

                if visible:
                    world[i][j].seen = True

                    if fog:
                        libt.console_put_char_ex(sketch1, i, j, "#",
                                                 COLOURS['lit_wall'], COLOURS['bg'])
                    else:
                        libt.console_put_char_ex(sketch1, i, j, ".",
                                                 COLOURS['lit_ground'], COLOURS['bg'])
                elif world[i][j].seen:
                    if fog:
                        # libt.console_put_char_ex(sketch1, i, j, "#", COLOURS['wall'], COLOURS['bg'])
                        libt.console_put_char_ex(sketch1, i, j, "#", 
                                                 COLOURS['wall'], COLOURS['bg'])
                    else:
                        # libt.console_put_char_ex(sketch1, i, j, ".", COLOURS['ground'], COLOURS['bg'])
                        libt.console_put_char_ex(sketch1, i, j, ".", 
                                                 COLOURS['ground'], COLOURS['bg'])

    for obj in objects:
        obj.draw()

    libt.console_blit(sketch1, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)


def keybinds():
    global fov_refresh
    key = libt.console_wait_for_keypress(True)

    if key.vk == libt.KEY_ENTER and key.lalt:
        libt.console_set_fullscreen(not libt.console_is_fullscreen())
    elif key.vk == libt.KEY_ESCAPE:
        return True

    if libt.console_is_key_pressed(libt.KEY_UP):
        fov_refresh = True
        player.move(0, -1)
    elif libt.console_is_key_pressed(libt.KEY_DOWN):
        fov_refresh = True
        player.move(0, 1)
    elif libt.console_is_key_pressed(libt.KEY_LEFT):
        fov_refresh = True
        player.move(-1, 0)
    elif libt.console_is_key_pressed(libt.KEY_RIGHT):
        fov_refresh = True
        player.move(1, 0)

# Class instances
player = Entity(54, 6, "@", libt.black)
npc = Entity(MAP_WIDTH / 2 + 2, MAP_HEIGHT / 2 + 2, "@", libt.yellow)
objects = [player]

make_map()
fov_map = libt.map_new(MAP_WIDTH, MAP_HEIGHT)

for i in range(MAP_WIDTH):
    for j in range(MAP_HEIGHT):
        libt.map_set_properties(fov_map, i, j, not world[i][j].fog, world[i][j].passable)

# Main loop
while not libt.console_is_window_closed():
    render_obj()
    libt.console_flush()

    for obj in objects:
        obj.clear()

    if keybinds():
        break
