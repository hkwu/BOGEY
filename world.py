#
# world.py
# Classes for constructing the game map
#

import random
import config
import entities


class Tile(object):
    """A single coordinate on the map."""
    def __init__(self, passable, fog=False, seen=False):
        self.passable = passable

        if not fog:
            fog = not passable

        self.fog = fog
        self.seen = seen


class Room(object):
    """A block of passable area in the map."""
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


class Map(object):
    """Class that stores the game's map information."""
    def __init__(self):
        self.map = []
        self.rooms = []

    def make_h_tunnel(self, x1, x2, y):
        """Creates passable tiles between x1 and x2 on the y coordinate."""
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.map[x][y].passable = True
            self.map[x][y].fog = False

    def make_v_tunnel(self, y1, y2, x):
        """Creates passable tiles between y1 and y2 on the x coordinate."""
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.map[x][y].passable = True
            self.map[x][y].fog = False

    def connect_rooms(self, room1, room2):
        """Takes two rooms and connects them with tunnels."""
        (r1_x, r1_y) = room1.centre()
        (r2_x, r2_y) = room2.centre()

        # Determine which direction to begin the connection
        # 0 is vertical, 1 is horizontal
        direction = random.randrange(2)

        if direction:
            self.make_h_tunnel(r1_x, r2_x, r1_y)
            self.make_v_tunnel(r1_y, r2_y, r2_x)
        else:
            self.make_v_tunnel(r1_y, r2_y, r1_x)
            self.make_h_tunnel(r1_x, r2_x, r2_y)

    def make_room(self, room):
        """Takes an instance of a Room and creates it on the game world."""
        for i in range(room.x1 + 1, room.x2):
            for j in range(room.y1 + 1, room.y2):
                self.map[i][j].passable = True
                self.map[i][j].fog = False

    def is_solid(self, x, y):
        """Determines if tile/entity at (x, y) is solid."""
        if not self.map[x][y].passable:
            return True
        
        for lst in self.handler.map_objects:
            for obj in self.handler.map_objects[lst]:
                if obj.solid and obj.x == x and obj.y == y:
                    return True

        return False

    def add_entities(self, room):
        """Adds random entities to a room."""
        count = config.MAX_MOBS

        while count > 0:
            entity_x = random.randrange(room.x1 + 1, room.x2)
            entity_y = random.randrange(room.y1 + 1, room.y2)
            mob = random.randrange(10)

            if not self.is_solid(entity_x, entity_y):
                if mob == 0:
                    self.handler.map_objects['mobs'].append(entities.Spider(entity_x, entity_y))
                elif mob == 1:
                    self.handler.map_objects['mobs'].append(entities.Skeleton(entity_x, entity_y))

            count -= 1

    def add_items(self, room):
        """Adds random items to a room."""
        count = config.MAX_ITEMS

        while count > 0:
            item_x = random.randrange(room.x1 + 1, room.x2)
            item_y = random.randrange(room.y1 + 1, room.y2)
            item = random.randrange(5)

            if not self.is_solid(item_x, item_y):
                if item == 0:
                    self.handler.map_objects['items'].append(entities.WoodenSword(item_x, item_y))
                elif item == 1:
                    self.handler.map_objects['items'].append(entities.StoneSword(item_x, item_y))

            count -= 1

    def add_item_tile(self, x, y, item):
        """
        Adds item to the tile at (x, y). 
        Requires that the tile is passable and that the item is 
        an instance of an entity.
        """
        assert hasattr(item, "name")

        for entity in self.handler.map_objects['mobs'] + self.handler.map_objects['characters']:
            if entity.x == x and entity.y == y:
                break
        else:
            if self.is_solid(x, y):
                return

        item.x = x
        item.y = y
        self.handler.map_objects['items'].append(item)

    def make_map(self):
        """Initializes the game world."""
        # Initialize the multi-dimensional array with unpassable tiles
        for i in range(config.MAP_WIDTH):
            self.map.append([])
            for j in range(config.MAP_HEIGHT):
                self.map[i].append(Tile(False))

        self.rooms = []
        num_rooms = 0

        # Fill array with passable tiles that represent up to MAX_ROOMS
        # number of rooms
        for num in range(config.MAX_ROOMS):
            w = random.randrange(config.ROOM_MIN_SIZE, config.ROOM_MAX_SIZE)
            h = random.randrange(config.ROOM_MIN_SIZE, config.ROOM_MAX_SIZE)
            x = random.randrange(config.MAP_WIDTH - w - 1)
            y = random.randrange(config.MAP_HEIGHT - h - 1)

            new = Room(x, y, w, h)
            intersected = False

            # Check for overlaps, stop if room overlaps old ones
            for room in self.rooms:
                if new.intersect(room):
                    intersected = True
                    break

            # Create new rooms if no intersections with previous rooms exist
            # Otherwise link rooms to each other
            if not intersected and num_rooms == 0:
                (player_x, player_y) = new.centre()
                self.handler.player.x = player_x
                self.handler.player.y = player_y
                num_rooms += 1

                self.rooms.append(new)
                self.make_room(new)
                self.add_entities(new)
                self.add_items(new)
            elif not intersected:
                num_rooms += 1
                self.rooms.append(new)
                self.make_room(new)
                self.add_entities(new)
                self.add_items(new)
                self.connect_rooms(self.rooms[num_rooms - 2], 
                                   self.rooms[num_rooms - 1])
