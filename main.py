import random
import libtcodpy as libt
import tiles
import config

# Colours
COLOURS = {
    'bg': libt.white,
    'wall': libt.Color(160, 160, 160),
    'lit_wall': libt.Color(173, 173, 0),
    'ground': libt.Color(160, 160, 160),
    'lit_ground': libt.Color(21, 21, 21),
    'player': libt.black,
    'mob': libt.Color(255, 0, 0),
    'text': libt.Color(164, 164, 164)
}


# Classes
class Entity(object):
    def __init__(self, x, y, name, char, colour, solid=False):
        self.x = x
        self.y = y
        self.name = name
        self.char = char
        self.colour = colour
        self.solid = solid

    def move(self, dx, dy):
        if not is_solid(self.x + dx, self.y):
            self.x += dx
        if not is_solid(self.x, self.y + dy):
            self.y += dy

    def draw(self):
        if libt.map_is_in_fov(fov_map, self.x, self.y):
            libt.console_set_default_foreground(sketch1, self.colour)
            libt.console_put_char(sketch1, self.x, self.y, 
                                  self.char, libt.BKGND_NONE)

    def clear(self):
        libt.console_put_char(sketch1, self.x, self.y, " ", libt.BKGND_NONE)


class Player(Entity):
    def __init__(self, x, y, name):
        Entity.__init__(self, x, y, name, "@", COLOURS['player'], True)


class Mob(Entity):
    def __init__(self, x, y, name, char):
        Entity.__init__(self, x, y, name, char, COLOURS['mob'], True)


class Spider(Mob):
    def __init__(self, x, y):
        Mob.__init__(self, x, y, "Spider", "s")


class Skeleton(Mob):
    def __init__(self, x, y):
        Mob.__init__(self, x, y, "Skeleton", "S")


# Map creation functions
def make_map():
    """Initializes the game world."""
    global world
    world = []

    # Initialize the multi-dimensional array with unpassable tiles
    for i in range(config.MAP_WIDTH):
        world.append([])
        for j in range(config.MAP_HEIGHT):
            world[i].append(tiles.Tile(False))

    rooms = []
    num_rooms = 0

    # Fill array with passable tiles that represent up to MAX_ROOMS
    # number of rooms
    for num in range(config.MAX_ROOMS):
        w = random.randrange(config.ROOM_MIN_SIZE, config.ROOM_MAX_SIZE)
        h = random.randrange(config.ROOM_MIN_SIZE, config.ROOM_MAX_SIZE)
        x = random.randrange(config.MAP_WIDTH - w - 1)
        y = random.randrange(config.MAP_HEIGHT - h - 1)

        new = tiles.Room(x, y, w, h)
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
            add_entities(new)
        elif not intersected:
            num_rooms += 1
            rooms.append(new)
            make_room(new)
            add_entities(new)
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
    """Takes an instance of a tiles.Room and creates it on the game world."""
    global world

    for i in range(room.x1 + 1, room.x2):
        for j in range(room.y1 + 1, room.y2):
            world[i][j].passable = True
            world[i][j].fog = False


# Entity functions
def is_solid(x, y):
    """Determines if tile/entity at (x, y) is solid."""
    if not world[x][y].passable:
        return True
    
    for obj in objects:
        if obj.solid and obj.x == x and obj.y == y:
            return True

    return False


def add_entities(room):
    """Adds random entities to a room."""
    entity_x = random.randrange(room.x1 + 1, room.x2)
    entity_y = random.randrange(room.y1 + 1, room.y2)
    mob = random.randrange(10)

    if mob == 0:
        objects.append(Spider(entity_x, entity_y))
    elif mob == 1:
        objects.append(Skeleton(entity_x, entity_y))


# Other functions
def render_obj():
    """Places objects and tiles on the console display."""
    global fov_refresh
    
    if fov_refresh:
        fov_refresh = False
        libt.map_compute_fov(fov_map, player.x, player.y, 
                             config.LIGHT_RANGE, config.FOV_LIT_WALLS, 
                             config.FOV)

        for i in range(config.MAP_WIDTH):
            for j in range(config.MAP_HEIGHT):
                fog = world[i][j].fog
                visible = libt.map_is_in_fov(fov_map, i, j)

                if visible:
                    world[i][j].seen = True

                    if fog:
                        libt.console_put_char_ex(sketch1, i, j, "#",
                                                 COLOURS['lit_wall'], 
                                                 COLOURS['bg'])
                    else:
                        libt.console_put_char_ex(sketch1, i, j, ".",
                                                 COLOURS['lit_ground'], 
                                                 COLOURS['bg'])
                elif world[i][j].seen:
                    if fog:
                        libt.console_put_char_ex(sketch1, i, j, "#", 
                                                 COLOURS['wall'], 
                                                 COLOURS['bg'])
                    else:
                        libt.console_put_char_ex(sketch1, i, j, ".", 
                                                 COLOURS['ground'], 
                                                 COLOURS['bg'])

    for obj in objects:
        obj.draw()

    libt.console_blit(sketch1, 0, 0, config.SCREEN_WIDTH, 
                      config.SCREEN_HEIGHT, 0, 0, 0)


def keybinds():
    """Handles keyboard input from the user."""
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
player = Player(0, 0, "Player")

# Map objects
objects = [player]

# Set the font, initialize window
libt.console_set_custom_font("dejavu10x10_gs_tc.png", 
                             libt.FONT_TYPE_GREYSCALE 
                             | libt.FONT_LAYOUT_TCOD)
libt.console_init_root(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, 
                       "Bogey", False)

# Keypress delay
libt.console_set_keyboard_repeat(50, 100)

# Screen consoles
sketch1 = libt.console_new(config.SCREEN_WIDTH, config.SCREEN_HEIGHT)

# Begin initialization
fov_refresh = True
fov_map = libt.map_new(config.MAP_WIDTH, config.MAP_HEIGHT)
make_map()

for i in range(config.MAP_WIDTH):
    for j in range(config.MAP_HEIGHT):
        libt.map_set_properties(fov_map, i, j, 
                                not world[i][j].fog, world[i][j].passable)

# Main loop
while not libt.console_is_window_closed():
    render_obj()
    libt.console_flush()

    for obj in objects:
        obj.clear()

    if keybinds():
        break
