#
# state.py
# Handles interactions between game modules
#

import collections
import os
import random
import libtcodpy as libt
import config
import data
import entities
import gui
import world


class StateHandler(object):
    """
    Class that takes care of interactions between entities, 
    gui and world modules. It also stores important data
    about the state of the game.
    """
    def __init__(self):
        # Set this class as owner for Entity, Map and GUIElement classes
        entities.Entity.handler = self
        world.Map.handler = self
        gui.GUIElement.handler = self

    def keybinds(self):
        """Handles keyboard input from the user."""
        if self.key.vk == libt.KEY_ENTER and self.key.lalt:
            libt.console_set_fullscreen(not libt.console_is_fullscreen())
        elif self.key.vk == libt.KEY_ESCAPE:
            menu = gui.InGameMenu()
            menu.draw()
            status = menu.select()

            if status == data.EXIT:
                return status
            else:
                return data.NO_MOVE
        elif self.game_state == data.PLAY:
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

    def init_program(self):
        """Setup method that is run when program starts."""
        libt.console_set_custom_font(config.get_img_path('char_sheet'), 
                                     libt.FONT_TYPE_GREYSCALE 
                                     | libt.FONT_LAYOUT_TCOD)
        libt.console_init_root(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, 
                               "BOGEY", False)
        libt.console_credits()
        libt.console_set_keyboard_repeat(50, 100)
        libt.sys_set_fps(60)

        # Screen consoles
        self.game_map = libt.console_new(config.MAP_WIDTH, config.MAP_HEIGHT)
        self.gui = libt.console_new(config.GUI_WIDTH, config.GUI_HEIGHT)

        # Set up input
        self.key = libt.Key()
        self.mouse = libt.Mouse()

        # Create main menu
        self.main_menu = gui.MainMenu()
        self.main_menu.draw()
        self.main_menu.select()

    def new_game(self):
        """Generates a new game."""
        self.game_state = data.PLAY
        self.player_action = None
        self.init_game_objects()
        self.world.make_map()
        self.init_fov()
        self.init_gui()

    def init_game_objects(self):
        """Creates the object instances."""
        self.player = entities.Player(0, 0, "Player")
        self.world = world.Map()

        # Map objects, OrderedDict ensures proper draw order
        self.map_objects = collections.OrderedDict([('items', []), 
                                                    ('mobs', []), 
                                                    ('characters', [self.player])])

    def init_fov(self):
        """Initializes the FOV map."""
        self.fov_refresh = True
        self.fov_map = libt.map_new(config.MAP_WIDTH, config.MAP_HEIGHT)
        libt.console_clear(self.game_map)

        for i in range(config.MAP_WIDTH):
            for j in range(config.MAP_HEIGHT):
                libt.map_set_properties(self.fov_map, i, j, 
                                        not self.world.map[i][j].fog, 
                                        self.world.map[i][j].passable)

    def init_gui(self):
        """Instantiates the GUI elements."""
        self.border = gui.Border()
        self.health_bar = gui.HealthBar()
        self.message_box = gui.MessageBox()

    def play(self):
        """Runs the game loop after game data has been set."""
        while not libt.console_is_window_closed():
            libt.sys_check_for_event(libt.EVENT_KEY_PRESS | libt.EVENT_MOUSE, 
                                     self.key, self.mouse)
            self.render_all()
            libt.console_flush()

            for lst in self.map_objects:
                self.clear_obj(self.map_objects[lst])

            player_action = self.keybinds()
            if player_action == data.EXIT:
                break
            elif self.game_state == data.PLAY and player_action != data.NO_MOVE:
                for mob in self.map_objects['mobs']:
                    mob.action_handler()

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
