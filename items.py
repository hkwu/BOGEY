import libtcodpy as libt
from main import Entity


class Inventory(object):
    """
    Inventory class.

    inv: the inventory
    max_weight: the maximum weight that inventory supports
    """
    def __init__(self, inv=[], max_weight):
        self.inv = inv
        self.max_weight = max_weight

    def add_item(self, item):
        inv.append(item)

    def remove_item(self, item):
        inv.remove(item)


class Item(Entity):
    """
    Base item class.

    weight: the amount of weight the item gets in the inventory
    value: how much the item can be sold to NPCs
    """
    def __init__(self, x, y, name, char, colour, weight, value):
        Entity.__init__(self, x, y, name, char, colour)
        self.weight = weight
        self.value = value
        self.game_map = None
        self.colour_map = None


class Weapon(Item):
    """
    Weapon class.

    damage: amount of damage weapon deals
    """
    def __init__(self, x, y, name, weight, value, damage):
        Item.__init__(self, x, y, name, "+", self.colour_map['weapons'], weight, value)
        self.damage = damage


class Sword(Weapon):
    """All the different types of swords."""
    def __init__(self, x, y, name, weight, value, damage):
        Weapon.__init__(self, x, y, name, weight, value)


class WoodenSword(Sword):
    def __init__(self, x, y):
        Sword.__init__(self, x, y, "Wooden Sword", 10, 50, 35)
