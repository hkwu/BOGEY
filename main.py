##############################################
# BOGEY
# Created by Kelvin Wu
# Initial commit 2015-06-13
# Based on Jotaf's Complete Roguelike Tutorial
##############################################

import math
import random
import textwrap
import libtcodpy as libt
import tiles
import config

# Set the font, initialize window
libt.console_set_custom_font("dejavu10x10_gs_tc.png", 
                             libt.FONT_TYPE_GREYSCALE 
                             | libt.FONT_LAYOUT_TCOD)
libt.console_init_root(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, 
                       "BOGEY", False)
libt.console_credits()

# Keypress delay
libt.console_set_keyboard_repeat(50, 100)

# Screen consoles
game_map = libt.console_new(config.MAP_WIDTH, config.MAP_HEIGHT)
gui = libt.console_new(config.GUI_WIDTH, config.GUI_HEIGHT)

# Colours
COLOURS = {
    'bg': libt.white,
    'wall': libt.light_grey,
    'lit_wall': libt.Color(173, 173, 0),
    'ground': libt.light_grey,
    'lit_ground': libt.Color(21, 21, 21),
    'player': libt.black,
    'mob': libt.red,
    'gui_bg': libt.black,
    'gui_border': libt.darkest_grey,
    'bar_hp': libt.dark_red,
    'bar_hp_unfilled': libt.darker_red,
    'text': libt.lightest_grey,
    'mob_behaviour_text': libt.amber,
    'player_atk_text': libt.grey,
    'mob_atk_text': libt.flame,
    'player_kill_text': libt.green,
    'player_die_text': libt.white
}

# Entity states
HOLD = 0
CHASE = 1
RUN = 2
DEAD = "dead"


######################################

# Classes

######################################
class Entity(object):
    """
    Base entity class for items, player, NPCs, mobs, etc.

    x: x-coordinate of entity
    y: y-coordinate of entity
    name: name of entity
    char: character representation of entity on world map
    colour: colour of entity on map
    solid: true if player can't walk through entity
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
            libt.console_set_default_foreground(game_map, self.colour)
            libt.console_put_char(game_map, self.x, self.y, 
                                  self.char, libt.BKGND_NONE)

    def clear(self):
        """Clears entity from console."""
        if libt.map_is_in_fov(fov_map, self.x, self.y):
            libt.console_put_char(game_map, self.x, self.y, 
                                  " ", libt.BKGND_NONE)


class CombatEntity(Entity):
    """
    Class for entities that engage in combat.

    hp: hitpoints for entity
    atk: attack strength of entity
    """
    def __init__(self, x, y, name, char, colour, solid, hp, atk):
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

    def deal_damage(self, target):
        """Deals damage to target entity."""
        if hasattr(target, "hp"):
            dmg = random.randrange(self.atk + 1)
            target.take_damage(dmg)
            return dmg

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
                dmg = self.deal_damage(mob)

                if dmg:
                    add_msg("You attack %s for %d damage!" % (mob.name, dmg), 
                            COLOURS['player_atk_text'])
                else:
                    add_msg("You missed!", COLOURS['player_atk_text'])

                if mob.state == DEAD:
                    add_msg("You killed %s!" % mob.name, 
                            COLOURS['player_kill_text'])
                    mob.name += "'s remains"
        else:
            fov_refresh = True
            self.move(dx, dy)

    def die(self):
        global game_state

        if game_state != DEAD:
            game_state = DEAD
            self.char = "%"


class Mob(CombatEntity):
    """
    Hostile mob class.

    morale: probability for entity to stand its ground in ground
    state: defines AI behaviour of entity
    """
    def __init__(self, x, y, name, char, hp, atk, morale, state=HOLD):
        CombatEntity.__init__(self, x, y, name, char, 
                              COLOURS['mob'], True, hp, atk)
        self.morale = morale
        self.state = state
        self.state_chart = [[None, self.in_sight_and_healthy, self.in_sight_and_not_healthy],
                            [self.not_in_sight, None, self.in_sight_and_not_healthy],
                            [self.not_in_sight, self.in_sight_and_healthy, None]]

    def send_to_back(self):
        """Moves mob to first index in mobs list."""
        global map_objects
        map_objects['mobs'].remove(self)
        map_objects['mobs'].insert(0, self)

    def die(self):
        self.char = "X"
        self.solid = False
        self.state = DEAD
        self.send_to_back()

    # Behavioural checks to switch between states
    def in_sight(self):
        return libt.map_is_in_fov(fov_map, self.x, self.y)

    def not_in_sight(self):
        return not self.in_sight()

    def healthy(self):
        return self.hp >= 0.4*self.max_hp

    def in_sight_and_healthy(self):
        return self.in_sight() and self.healthy()

    def in_sight_and_not_healthy(self):
        if random.randrange(101) > self.morale:
            return self.in_sight() and not self.healthy()

        return False

    # Default state methods
    def chase(self, target):
        """Moves entity towards the target and attacks if possible."""
        linear_dist = lambda x1, x2, y1, y2: math.sqrt((x1 - x2)**2 + 
                                                       (y1 - y2)**2)
        min_dist_to_target = linear_dist(self.x, target.x, 
                                         self.y, target.y)
        possible_posn = [[1, 0], [-1, 0], [0, 1], [0, -1]]
        move_to_make = None

        for posn in possible_posn:
            if (self.x + posn[0] == player.x and 
                self.y + posn[1] == player.y and 
                game_state != DEAD):
                dmg = self.deal_damage(player)

                if dmg:
                    add_msg("%s attacks you for %d damage!" % (self.name, dmg), 
                            COLOURS['mob_atk_text'])
                else:
                    add_msg("%s missed!" % self.name, COLOURS['mob_atk_text'])

                if game_state == DEAD:
                    add_msg("%s killed you!" % self.name, 
                            COLOURS['player_die_text'])
            elif not is_solid(self.x + posn[0], self.y + posn[1]):
                new_dist = linear_dist(self.x + posn[0], target.x, 
                                       self.y + posn[1], target.y)
                if new_dist < min_dist_to_target:
                    min_dist_to_target = new_dist
                    move_to_make = posn

        if move_to_make:
            self.move(move_to_make[0], move_to_make[1])

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

                # Some messages when state changes
                if self.state == CHASE:
                    add_msg("%s sees you!" % self.name, COLOURS['mob_behaviour_text'])
                elif self.state == RUN:
                    add_msg("%s runs away!" % self.name, COLOURS['mob_behaviour_text'])

            x += 1

        if self.state == HOLD:
            return
        elif self.state == CHASE:
            self.chase(player)
        elif self.state == RUN:
            self.run(player)


class Spider(Mob):
    def __init__(self, x, y):
        Mob.__init__(self, x, y, "Spider", "s", 200, 15, 50)


class Skeleton(Mob):
    def __init__(self, x, y):
        Mob.__init__(self, x, y, "Skeleton", "S", 235, 20, 100)


######################################

# Map creation functions

######################################
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


######################################

# Entity functions

######################################
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
    count = config.MAX_MOBS

    while count > 0:
        entity_x = random.randrange(room.x1 + 1, room.x2)
        entity_y = random.randrange(room.y1 + 1, room.y2)
        mob = random.randrange(3)

        if mob == 0:
            map_objects['mobs'].append(Spider(entity_x, entity_y))
        elif mob == 1:
            map_objects['mobs'].append(Skeleton(entity_x, entity_y))

        count -= 1


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


######################################

# GUI functions

######################################
def borders():
    """Draws borders around the info panel."""
    libt.console_set_default_background(gui, COLOURS['gui_bg'])
    libt.console_clear(gui)

    upper_height = config.BORDER_WIDTH / 2
    left_height = config.GUI_HEIGHT - upper_height*2

    libt.console_set_default_background(gui, COLOURS['gui_border'])
    # Upper border
    libt.console_rect(gui, 0, 0, config.GUI_WIDTH, upper_height, 
                      False, libt.BKGND_SCREEN)
    # Lower border
    libt.console_rect(gui, 0, config.GUI_HEIGHT - config.BORDER_WIDTH/2,  
                      config.GUI_WIDTH, upper_height, False, libt.BKGND_SCREEN)
    # Left border
    libt.console_rect(gui, 0, upper_height, config.BORDER_WIDTH / 2, 
                      left_height, False, libt.BKGND_SCREEN)
    # Right border
    libt.console_rect(gui, config.GUI_WIDTH - config.BORDER_WIDTH/2, upper_height, 
                      config.BORDER_WIDTH / 2, left_height, False, libt.BKGND_SCREEN)
    # Middle border
    libt.console_rect(gui, config.GUI_WIDTH/2 - config.BORDER_WIDTH/2, upper_height, 
                      config.BORDER_WIDTH, left_height, False, libt.BKGND_SCREEN)


def fillup_bar(x, y, name, val, max_val, bar_colour, back_colour):
    """
    Creates a bar that shows the current value 
    out of the given maximum.
    """
    filled_width = int(float(val) / max_val * config.BAR_WIDTH)

    libt.console_set_default_background(gui, back_colour)
    libt.console_rect(gui, x, y, config.BAR_WIDTH, config.BAR_HEIGHT, 
                      False, libt.BKGND_SCREEN)

    libt.console_set_default_background(gui, bar_colour)
    if filled_width > 0:
        libt.console_rect(gui, x, y, filled_width, config.BAR_HEIGHT, 
                          False, libt.BKGND_SCREEN)

    bar_midpoint = (int(config.BAR_WIDTH/2 + x), int(config.BAR_HEIGHT/2 + y))

    libt.console_set_default_foreground(gui, COLOURS['text'])
    libt.console_print_ex(gui, bar_midpoint[0], bar_midpoint[1], 
                          libt.BKGND_NONE, libt.CENTER,
                          "%s: %d/%d" % (name, val, max_val))


def stat_bars():
    """Creates the status bars."""
    # HP bar
    fillup_bar(config.BORDER_WIDTH, config.BORDER_WIDTH, "HP", player.hp, 
               player.max_hp, COLOURS['bar_hp'], COLOURS['bar_hp_unfilled'])
    libt.console_set_default_foreground(gui, COLOURS['text'])


def add_msg(msg, colour=COLOURS['text']):
    """Adds a message to the message box."""
    wrapped = textwrap.wrap(msg, config.MSG_WIDTH - config.BORDER_WIDTH*2)

    for line in wrapped:
        if len(game_msgs) == config.MSG_HEIGHT - config.BORDER_WIDTH:
            del game_msgs[0]
        game_msgs.append((line, colour))


def msg_box():
    """Draws messages in the message box."""
    y = config.BORDER_WIDTH
    for (msg, colour) in game_msgs:
        libt.console_set_default_foreground(gui, colour)
        libt.console_print_ex(gui, config.MSG_WIDTH + config.BORDER_WIDTH, y, 
                              libt.BKGND_NONE, libt.LEFT, msg)
        y += 1


def objects_under_mouse():
    """Returns list of entities that mouse is hovering over."""
    x = mouse.cx
    y = mouse.cy
    names = []

    for entity in map_objects['mobs']:
        if (entity.x == x and entity.y == y and 
            libt.map_is_in_fov(fov_map, entity.x, entity.y)):
            if entity.state == DEAD:
                names.append("%s" % entity.name)
            else:
                names.append("%s [%d/%d]" % (entity.name, entity.hp, entity.max_hp))

    names = ", ".join(names)
    return names.capitalize()


######################################

# Other functions

######################################
def draw_obj(lst):
    """Takes a list of objects and draws them on the map."""
    for obj in lst:
        obj.draw()


def clear_obj(lst):
    """Takes a list of objects and clears them from the map."""
    for obj in lst:
        obj.clear()


def render_all():
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
                        libt.console_put_char_ex(game_map, i, j, "#",
                                                 COLOURS['lit_wall'], 
                                                 COLOURS['bg'])
                    else:
                        libt.console_put_char_ex(game_map, i, j, ".",
                                                 COLOURS['lit_ground'], 
                                                 COLOURS['bg'])
                elif world[i][j].seen:
                    if fog:
                        libt.console_put_char_ex(game_map, i, j, "#", 
                                                 COLOURS['wall'], 
                                                 COLOURS['bg'])
                    else:
                        libt.console_put_char_ex(game_map, i, j, ".", 
                                                 COLOURS['ground'], 
                                                 COLOURS['bg'])

    # Draw entities
    for lst in map_objects:
        draw_obj(map_objects[lst])

    # Draw GUI
    borders()
    stat_bars()
    msg_box()
    libt.console_print_ex(gui, config.GUI_WIDTH / 2, 1,
                          libt.BKGND_NONE, libt.CENTER, objects_under_mouse())

    # Blit the consoles
    libt.console_blit(game_map, 0, 0, 
                      config.MAP_WIDTH, config.MAP_HEIGHT, 0, 
                      0, 0)
    libt.console_blit(gui, 0, 0,
                      config.GUI_WIDTH, config.GUI_HEIGHT, 0, 
                      0, config.MAP_HEIGHT)


def keybinds():
    """Handles keyboard input from the user."""
    global fov_refresh

    if key.vk == libt.KEY_ENTER and key.lalt:
        libt.console_set_fullscreen(not libt.console_is_fullscreen())
    elif key.vk == libt.KEY_ESCAPE:
        return "exit"

    if game_state == "play":
        if key.vk == libt.KEY_UP:
            player.move_or_attack(0, -1)
        elif key.vk == libt.KEY_DOWN:
            player.move_or_attack(0, 1)
        elif key.vk == libt.KEY_LEFT:
            player.move_or_attack(-1, 0)
        elif key.vk == libt.KEY_RIGHT:
            player.move_or_attack(1, 0)
        else:
            return "no_move"


def setup():
    """Sets up the initial game state."""
    global player, game_msgs, mouse, key

    player = Player(0, 0, "Player")
    game_msgs = []
    key = libt.Key()
    mouse = libt.Mouse()
    libt.sys_set_fps(60)


def initialize():
    """Initializes game state for each new map."""
    global map_objects
    global fov_refresh, fov_map
    global game_state, player_action, game_msgs
    

    # Map objects
    map_objects = {
        'mobs': [],
        'characters': [player]
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

######################################

# Main loop

######################################
setup()
initialize()

while not libt.console_is_window_closed():
    libt.sys_check_for_event(libt.EVENT_KEY_PRESS | libt.EVENT_MOUSE, key, mouse)
    render_all()
    libt.console_flush()

    for lst in map_objects:
        clear_obj(map_objects[lst])

    player_action = keybinds()
    if player_action == "exit":
        break
    elif game_state == "play" and player_action != "no_move":
        for mob in map_objects['mobs']:
            mob.action_handler()
