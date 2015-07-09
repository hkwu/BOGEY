#
# state.py
# Handles interactions between game modules
#

import collections
import libtcodpy as libt
import config
import data
import entities
import gui
import world

import random

class StateHandler(object):
    """
    Class that takes care of interactions between entity, 
    gui and world modules. It also stores important data
    about the state of the game.
    """
    def __init__(self):
        # Screen consoles
        self.game_map = libt.console_new(config.MAP_WIDTH, config.MAP_HEIGHT)
        self.gui = libt.console_new(config.GUI_WIDTH, config.GUI_HEIGHT)

        # Set up input
        self.key = libt.Key()
        self.mouse = libt.Mouse()

        # FOV
        self.fov_refresh = True
        self.fov_map = libt.map_new(config.MAP_WIDTH, config.MAP_HEIGHT)

        # Set this class as owner for Entity, Map and GUIElement classes
        entities.Entity.handler = self
        world.Map.handler = self
        gui.GUIElement.handler = self

        # Instantiate
        self.player = entities.Player(0, 0, "Player")
        self.world = world.Map()

        self.border = gui.Border()
        self.health_bar = gui.HealthBar()
        self.message_box = gui.MessageBox()

        # Map objects, OrderedDict ensures proper draw order
        self.map_objects = collections.OrderedDict([('items', []), 
                                                    ('mobs', []), 
                                                    ('characters', [self.player])])
        
        self.world.make_map()

        # DEBUG for inventory
        # for i in range(20):
        #     if random.randrange(2):
        #         self.player.inv.append(entities.WoodenSword(self.player.x, self.player.y))
        #     else:
        #         self.player.inv.append(entities.StoneSword(self.player.x, self.player.y))

        # Keep track of game state and player action
        self.game_state = data.PLAY
        self.player_action = None

        # Set FOV properties for all tiles
        for i in range(config.MAP_WIDTH):
            for j in range(config.MAP_HEIGHT):
                libt.map_set_properties(self.fov_map, i, j, 
                                        not self.world.map[i][j].fog, 
                                        self.world.map[i][j].passable)

    def keybinds(self):
        """Handles keyboard input from the user."""
        if self.key.vk == libt.KEY_ENTER and self.key.lalt:
            libt.console_set_fullscreen(not libt.console_is_fullscreen())
        elif self.key.vk == libt.KEY_ESCAPE:
            return data.EXIT

        if self.game_state == data.PLAY:
            if self.key.vk == libt.KEY_UP:
                self.player.move_or_attack(0, -1)
            elif self.key.vk == libt.KEY_DOWN:
                self.player.move_or_attack(0, 1)
            elif self.key.vk == libt.KEY_LEFT:
                self.player.move_or_attack(-1, 0)
            elif self.key.vk == libt.KEY_RIGHT:
                self.player.move_or_attack(1, 0)
            else:
                char = chr(self.key.c)

                if char == "g":
                    self.player.player_take()
                elif char == "i":
                    menu = gui.InventoryMenu()
                    menu.draw()
                    menu.select()

                return data.NO_MOVE

    def draw_obj(self, lst):
        """Takes a list of objects and draws them on the map."""
        for obj in lst:
            obj.draw()

    def clear_obj(self, lst):
        """Takes a list of objects and clears them from the map."""
        for obj in lst:
            obj.clear()

    def render_all(self):
        """Places objects and tiles on the console display."""
        if self.fov_refresh:
            self.fov_refresh = False
            libt.map_compute_fov(self.fov_map, self.player.x, self.player.y, 
                                 config.LIGHT_RANGE, config.FOV_LIT_WALLS, 
                                 config.FOV)

            for i in range(config.MAP_WIDTH):
                for j in range(config.MAP_HEIGHT):
                    fog = self.world.map[i][j].fog
                    visible = libt.map_is_in_fov(self.fov_map, i, j)

                    if visible:
                        self.world.map[i][j].seen = True

                        if fog:
                            libt.console_put_char_ex(self.game_map, i, j, "#",
                                                     data.COLOURS['lit_wall'], 
                                                     data.COLOURS['bg'])
                        else:
                            libt.console_put_char_ex(self.game_map, i, j, ".",
                                                     data.COLOURS['lit_ground'], 
                                                     data.COLOURS['bg'])
                    elif self.world.map[i][j].seen:
                        if fog:
                            libt.console_put_char_ex(self.game_map, i, j, "#", 
                                                     data.COLOURS['wall'], 
                                                     data.COLOURS['bg'])
                        else:
                            libt.console_put_char_ex(self.game_map, i, j, ".", 
                                                     data.COLOURS['ground'], 
                                                     data.COLOURS['bg'])

        # Draw entities
        for lst in self.map_objects:
            self.draw_obj(self.map_objects[lst])

        # Refresh the status bars
        self.health_bar = gui.HealthBar()

        # Draw GUI
        self.border.draw()
        self.health_bar.draw()
        self.message_box.draw()

        # Blit the consoles
        libt.console_blit(self.game_map, 0, 0, 
                          config.MAP_WIDTH, config.MAP_HEIGHT, 0, 
                          0, 0)
        libt.console_blit(self.gui, 0, 0,
                          config.GUI_WIDTH, config.GUI_HEIGHT, 0, 
                          0, config.MAP_HEIGHT)
