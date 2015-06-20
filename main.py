import math
import random
import libtcodpy as libt
import tiles
import config

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

# Entity states
HOLD = 0
CHASE = 1
RUN = 2
DEAD = "dead"


# Classes
class Entity(object):
    """
    Base entity class for items, player, NPCs, mobs, etc.

    x: x-coordinate of entity
    y: y-coordinate of entity
    name: name of entity
    char: character representation of entity on world map
    colour: colour of entity on map
    solid: true if player can walk through entity
    """
    def __init__(self, x, y, name, char, colour, solid=False):
        self.x = x
        self.y = y
        self.name = name
        self.char = char
        self.colour = colour
        self.solid = solid

    def move(self, dx, dy):
        """Moves the entity."""
        if not is_solid(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy

    def draw(self):
        """Draws entity on console."""
        if libt.map_is_in_fov(fov_map, self.x, self.y):
            libt.console_set_default_foreground(sketch1, self.colour)
            libt.console_put_char(sketch1, self.x, self.y, 
                                  self.char, libt.BKGND_NONE)

    def clear(self):
        """Clears entity from console."""
        if libt.map_is_in_fov(fov_map, self.x, self.y):
            libt.console_put_char(sketch1, self.x, self.y, 
                                  " ", libt.BKGND_NONE)


class CombatEntity(Entity):
    """
    Class for entities that engage in combat.

    hp: hitpoints for entity
    atk: attack strength of entity
    """
    def __init__(self, x, y, name, char, colour, solid, hp, atk,):
        Entity.__init__(self, x, y, name, char, colour, True)
        self.hp = hp
        self.max_hp = hp
        self.atk = atk

    def take_damage(self, damage):
        """Deals damage to current entity."""
        if self.hp - damage <= 0:
            self.hp = 0
            self.die()
        else:
            self.hp -= damage

    def deal_damage(self, target, damage):
        """Deals damage to target entity."""
        target.take_damage(damage)

    # Placeholder method to be overwitten in child classes
    def die(self):
        """Handles death of the entity."""
        return


class Player(CombatEntity):
    """Player class."""
    def __init__(self, x, y, name):
        CombatEntity.__init__(self, x, y, name, "@", 
                              COLOURS['player'], True, 300, 30)

    def move_or_attack(self, dx, dy):
        """Makes a move or attack, depending on surroundings."""
        global fov_refresh

        for mob in map_objects['mobs']:
            if (mob.x == self.x + dx and 
                mob.y == self.y + dy and mob.solid):
                mob.take_damage(self.atk)
                print("You attack the %s for %d hp!" % (mob.name, self.atk))
        else:
            fov_refresh = True
            self.move(dx, dy)

    def die(self):
        global game_state
        game_state = "dead"
        self.char = "%"


class Mob(CombatEntity):
    """
    Hostile mob class.

    state: defines AI behaviour of entity
    """
    def __init__(self, x, y, name, char, hp, atk, state=HOLD):
        CombatEntity.__init__(self, x, y, name, char, 
                              COLOURS['mob'], True, hp, atk)
        self.state = state
        self.state_chart = [[None, self.in_sight_and_healthy, self.in_sight_and_not_healthy],
                            [self.not_in_sight, None, self.in_sight_and_not_healthy],
                            [self.not_in_sight, self.in_sight_and_healthy, None]]

    def die(self):
        self.char = "X"
        self.solid = False
        self.state = DEAD

    # Behavioural checks to switch between states
    def in_sight(self):
        return libt.map_is_in_fov(fov_map, self.x, self.y)

    def not_in_sight(self):
        return not self.in_sight()

    def healthy(self):
        return self.hp >= 0.8*self.max_hp

    def in_sight_and_healthy(self):
        return self.in_sight() and self.healthy()

    def in_sight_and_not_healthy(self):
        return False
        # return self.in_sight() and not self.healthy()

    # Default state methods
    def chase(self, target):
        """Moves entity towards the target and attacks if possible."""
        x_diff = self.x - target.x
        y_diff = self.y - target.y
        dx = 0 if x_diff == 0 else -x_diff / abs(x_diff)
        dy = 0 if y_diff == 0 else -y_diff / abs(y_diff)
        direction = random.randrange(2)

        # Random direction in which to approach
        # 0 is vertical, 1 is horizontal
        if direction:
            if self.x + dx == player.x and self.y == player.y:
                player.take_damage(self.atk)
            elif not is_solid(self.x + dx, self.y):
                self.move(dx, 0)
            else:
                self.move(0, dy)
        else:
            if self.x == player.x and self.y + dy == player.y:
                player.take_damage(self.atk)
            elif not is_solid(self.x, self.y + dy):
                self.move(0, dy)
            else:
                self.move(dx, 0)

    def run(self, target):
        """Moves entity away from target."""
        linear_dist = lambda x1, x2, y1, y2: math.sqrt((x1 - x2)**2 + 
                                                       (y1 - y2)**2)
        max_dist_to_target = linear_dist(self.x, target.x, 
                                         self.y, target.y)
        possible_posn = [[1, 0], [-1, 0], [0, 1], [0, -1]]
        move_to_make = None

        for posn in possible_posn:
            if not is_solid(self.x + posn[0], self.y + posn[1]):
                new_dist = linear_dist(self.x + posn[0], target.x, 
                                       self.y + posn[1], target.y)
                if new_dist > max_dist_to_target:
                    max_dist_to_target = new_dist
                    move_to_make = posn

        if move_to_make:
            self.move(move_to_make[0], move_to_make[1])

    def action_handler(self):
        """
        Checks for changes in state for the entity 
        and calls appropriate methods.
        """
        if self.state == DEAD:
            return

        x = 0
        for check in self.state_chart[self.state]:
            if not check:
                x += 1
                continue
            elif check():
                self.state = x

            x += 1

        if self.state == HOLD:
            return
        elif self.state == CHASE:
            self.chase(player)
        # elif self.state == RUN:
        #     self.run(player)


class Spider(Mob):
    def __init__(self, x, y):
        Mob.__init__(self, x, y, "Spider", "s", 200, 15)


class Skeleton(Mob):
    def __init__(self, x, y):
        Mob.__init__(self, x, y, "Skeleton", "S", 235, 20)


# Map creation functions
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


# Entity functions
def is_solid(x, y):
    """Determines if tile/entity at (x, y) is solid."""
    if not world[x][y].passable:
        return True
    
    for lst in map_objects:
        for obj in map_objects[lst]:
            if obj.solid and obj.x == x and obj.y == y:
                return True

    return False


def add_entities(room):
    """Adds random entities to a room."""
    entity_x = random.randrange(room.x1 + 1, room.x2)
    entity_y = random.randrange(room.y1 + 1, room.y2)
    mob = random.randrange(3)

    if mob == 0:
        map_objects['mobs'].append(Spider(entity_x, entity_y))
    elif mob == 1:
        map_objects['mobs'].append(Skeleton(entity_x, entity_y))


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


# Other functions
def draw_obj(lst):
    """Takes a list of objects and draws them on the map."""
    for obj in lst:
        obj.draw()


def clear_obj(lst):
    """Takes a list of objects and clears them from the map."""
    for obj in lst:
        obj.clear()


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

    for lst in map_objects:
        draw_obj(map_objects[lst])

    libt.console_blit(sketch1, 0, 0, config.SCREEN_WIDTH, 
                      config.SCREEN_HEIGHT, 0, 0, 0)


def keybinds():
    """Handles keyboard input from the user."""
    global fov_refresh
    key = libt.console_wait_for_keypress(True)

    if key.vk == libt.KEY_ENTER and key.lalt:
        libt.console_set_fullscreen(not libt.console_is_fullscreen())
    elif key.vk == libt.KEY_ESCAPE:
        return "exit"

    if game_state == "play":
        if libt.console_is_key_pressed(libt.KEY_UP):
            player.move_or_attack(0, -1)
        elif libt.console_is_key_pressed(libt.KEY_DOWN):
            player.move_or_attack(0, 1)
        elif libt.console_is_key_pressed(libt.KEY_LEFT):
            player.move_or_attack(-1, 0)
        elif libt.console_is_key_pressed(libt.KEY_RIGHT):
            player.move_or_attack(1, 0)
        else:
            return "no_move"

# Class instances
player = Player(0, 0, "Player")

# Map objects
map_objects = {
    'characters': [player],
    'mobs': []
}

# Begin initialization
fov_refresh = True
fov_map = libt.map_new(config.MAP_WIDTH, config.MAP_HEIGHT)
make_map()

for i in range(config.MAP_WIDTH):
    for j in range(config.MAP_HEIGHT):
        libt.map_set_properties(fov_map, i, j, 
                                not world[i][j].fog, world[i][j].passable)

game_state = "play"
player_action = None

# Main loop
while not libt.console_is_window_closed():
    render_obj()
    libt.console_flush()

    for lst in map_objects:
        clear_obj(map_objects[lst])

    player_action = keybinds()
    if player_action == "exit":
        break
    elif game_state == "play" and player_action != "no_move":
        for mob in map_objects['mobs']:
            mob.action_handler()
