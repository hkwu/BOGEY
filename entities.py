#
# entities.py
# Classes for entities such as mobs and items
#

import copy
import math
import random
import libtcodpy as libt
import data


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
        if not self.handler.world.is_solid(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy

    def draw(self):
        """Draws entity on console."""
        if libt.map_is_in_fov(self.handler.fov_map, self.x, self.y):
            libt.console_set_default_foreground(self.handler.game_map, self.colour)
            libt.console_put_char(self.handler.game_map, self.x, self.y, 
                                  self.char, libt.BKGND_NONE)

    def clear(self):
        """Clears entity from console."""
        if libt.map_is_in_fov(self.handler.fov_map, self.x, self.y):
            libt.console_put_char(self.handler.game_map, self.x, self.y, 
                                  " ", libt.BKGND_NONE)

    def send_to_back(self, lst_of_entities):
        """Moves entity to first index in respective list."""
        self.handler.map_objects[lst_of_entities].remove(self)
        self.handler.map_objects[lst_of_entities].insert(0, self)


class LivingEntity(Entity):
    """Class for entities that are alive."""
    def __init__(self, x, y, name, char, colour):
        Entity.__init__(self, x, y, name, char, colour, True)
        self.inv = {}

    def add_to_inv(self, item):
        """Adds the item to entity's inventory."""
        for obj in self.inv:
            if obj.name == item.name:
                self.inv[obj] += 1
                break
        else:
            self.inv[item] = 1

    def remove_from_inv(self, item):
        """
        Removes instance of item from inventory.
        Requires that the item exists in entity's inventory.
        """
        if self.inv[item] > 1:
            self.inv[item] -= 1
        else:
            return self.inv.pop(item)

    def take(self):
        """
        Places the first item on the ground below the entity
        into entity's inventory.
        """
        for item in self.handler.map_objects['items']:
            if item.x == self.x and item.y == self.y:
                self.handler.map_objects['items'].remove(item)
                self.add_to_inv(item)
                return item.name

        return False

    def drop(self, item):
        """
        Removes item from entity's inventory and places it
        on the ground below.
        """
        for obj in self.handler.player.inv:
            if obj.name == item.name:
                dropped = self.remove_from_inv(obj)

                # If we popped the item from player's inventory, we 
                # can drop it directly. Else we need to copy it and
                # drop it
                if dropped:
                    self.handler.world.add_item_tile(self.x, self.y, obj)
                else:
                    self.handler.world.add_item_tile(self.x, self.y, copy.copy(obj))
                
                return obj.name

        return False


class CombatEntity(LivingEntity):
    """
    Class for entities that engage in combat.

    hp: hitpoints for entity
    atk: attack strength of entity
    """
    def __init__(self, x, y, name, char, colour, hp, atk):
        LivingEntity.__init__(self, x, y, name, char, colour)
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
        pass


class Player(CombatEntity):
    """Player class."""
    def __init__(self, x, y, name):
        CombatEntity.__init__(self, x, y, name, "@", 
                              data.COLOURS['player'], 300, 30)

    def move_or_attack(self, dx, dy):
        """Makes a move or attack, depending on surroundings."""
        for mob in self.handler.map_objects['mobs']:
            if (mob.x == self.x + dx and 
                mob.y == self.y + dy and mob.solid):
                dmg = self.deal_damage(mob)

                if dmg:
                    self.handler.message_box.add_msg("You attack {} for {} damage!".format(mob.name, dmg), 
                                                     data.COLOURS['player_atk_text'])
                else:
                    self.handler.message_box.add_msg("You missed!", data.COLOURS['player_atk_text'])

                if mob.state == data.DEAD:
                    self.handler.message_box.add_msg("You killed {}!".format(mob.name), 
                                                     data.COLOURS['player_kill_text'])
                    mob.name += "'s remains"
        else:
            self.handler.fov_refresh = True
            self.move(dx, dy)

    def die(self):
        if self.handler.game_state != data.DEAD:
            self.handler.game_state = data.DEAD
            self.char = "%"

    def player_take(self):
        """
        Player-specific method for taking items. Will 
        generate a message on successful take.
        """
        taken = self.take()
        if taken:
            self.handler.message_box.add_msg("You take the {}!".format(taken),
                                             data.COLOURS['player_item_text'])

    def player_drop(self, item):
        """
        Player-specific method for dropping items. Will
        generate a message on successful drop.
        """
        dropped = self.drop(item)
        if dropped:
            self.handler.message_box.add_msg("You drop the {}!".format(dropped),
                                             data.COLOURS['player_item_text'])


class Mob(CombatEntity):
    """
    Hostile mob class.

    morale: probability for entity to stand its ground in combat
    state: defines AI behaviour of entity
    """
    def __init__(self, x, y, name, char, hp, atk, morale, state=data.HOLD):
        CombatEntity.__init__(self, x, y, name, char, 
                              data.COLOURS['mob'], hp, atk)
        self.morale = morale
        self.state = state
        self.state_chart = [[None, self.in_sight_and_healthy, self.in_sight_and_not_healthy],
                            [self.not_in_sight, None, self.in_sight_and_not_healthy],
                            [self.not_in_sight, self.in_sight_and_healthy, None]]

    def die(self):
        self.char = "X"
        self.solid = False
        self.state = data.DEAD
        self.send_to_back('mobs')

    # Behavioural checks to switch between states
    def in_sight(self):
        return libt.map_is_in_fov(self.handler.fov_map, self.x, self.y)

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
            if (self.x + posn[0] == self.handler.player.x and 
                self.y + posn[1] == self.handler.player.y and 
                self.handler.game_state != data.DEAD):
                dmg = self.deal_damage(self.handler.player)

                if dmg:
                    self.handler.message_box.add_msg("{} attacks you for {} damage!".format(self.name, dmg), 
                                                     data.COLOURS['mob_atk_text'])
                else:
                    self.handler.message_box.add_msg("{} missed!".format(self.name), 
                                                     data.COLOURS['mob_atk_text'])

                if self.handler.game_state == data.DEAD:
                    self.handler.message_box.add_msg("{} killed you!".format(self.name),
                                                     data.COLOURS['player_die_text'])
            elif not self.handler.world.is_solid(self.x + posn[0], self.y + posn[1]):
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
            if not self.handler.world.is_solid(self.x + posn[0], self.y + posn[1]):
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
        if self.state == data.DEAD:
            return

        x = 0
        for check in self.state_chart[self.state]:
            if not check:
                x += 1
                continue
            elif check():
                self.state = x

                # Some messages when state changes
                if self.state == data.CHASE:
                    self.handler.message_box.add_msg("{} sees you!".format(self.name), 
                                                     data.COLOURS['mob_behaviour_text'])
                elif self.state == data.RUN:
                    self.handler.message_box.add_msg("{} runs away!".format(self.name), 
                                                     data.COLOURS['mob_behaviour_text'])

            x += 1

        if self.state == data.HOLD:
            return
        elif self.state == data.CHASE:
            self.chase(self.handler.player)
        elif self.state == data.RUN:
            self.run(self.handler.player)


class Spider(Mob):
    def __init__(self, x, y):
        Mob.__init__(self, x, y, "Spider", "s", 200, 15, 50)


class Skeleton(Mob):
    def __init__(self, x, y):
        Mob.__init__(self, x, y, "Skeleton", "S", 235, 20, 100)


class Item(Entity):
    """
    Base item class.

    weight: the amount of weight the item gets in the inventory
    value: how much the item can be sold to NPCs
    usable: whether or not the item has effects that can be triggered
    stackable: if true, the item will be grouped with other items
    that are the same in player's inventory
    """
    def __init__(self, x, y, name, char, colour, weight, value, 
                 usable=False, stackable=True):
        Entity.__init__(self, x, y, name, char, colour)
        self.weight = weight
        self.value = value
        self.usable = usable
        self.stackable = stackable

    def use(self):
        """Uses the item."""
        # DEBUG
        print("You use the {}!".format(self.name))


class Weapon(Item):
    """
    Weapon class.

    damage: amount of damage weapon deals
    """
    def __init__(self, x, y, name, weight, value, damage):
        Item.__init__(self, x, y, name, "|", 
                      data.COLOURS['weapons'], weight, value, True, False)
        self.damage = damage


class Sword(Weapon):
    """All the different types of swords."""
    def __init__(self, x, y, name, weight, value, damage):
        Weapon.__init__(self, x, y, name, weight, value, damage)


class WoodenSword(Sword):
    def __init__(self, x, y):
        Sword.__init__(self, x, y, "Wooden Sword", 10, 50, 35)


class StoneSword(Sword):
    def __init__(self, x, y):
        Sword.__init__(self, x, y, "Stone Sword", 15, 75, 37)
