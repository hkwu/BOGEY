#
# gui.py
# Classes for each element of the GUI
#

import textwrap
import libtcodpy as libt
import config
import data
import save


class GUIElement(object):
    """Base class for GUI elements."""
    def __init__(self):
        pass

    def draw(self):
        pass


class Border(GUIElement):
    """Border that surrounds the GUI."""
    def __init__(self):
        GUIElement.__init__(self)

    def objects_under_mouse(self):
        """Returns list of entities that mouse is hovering over."""
        x = self.handler.mouse.cx
        y = self.handler.mouse.cy
        names = []

        # Names of mobs
        for entity in self.handler.map_objects['mobs']:
            if (entity.x == x and entity.y == y and 
                libt.map_is_in_fov(self.handler.fov_map, entity.x, entity.y)):
                if entity.state == data.DEAD:
                    names.append(entity.name)
                else:
                    names.append("{} [{}/{}]".format(entity.name, entity.hp, entity.max_hp))

        # Names of items
        for item in self.handler.map_objects['items']:
            if (item.x == x and item.y == y and
                libt.map_is_in_fov(self.handler.fov_map, item.x, item.y)):
                names.append(item.name)

        names = ", ".join(names)
        return names

    def draw(self):
        """Draws borders around the info panel."""
        libt.console_set_default_background(self.handler.gui, data.COLOURS['gui_bg'])
        libt.console_clear(self.handler.gui)

        upper_height = config.BORDER_WIDTH / 2
        left_height = config.GUI_HEIGHT - upper_height*2

        libt.console_set_default_background(self.handler.gui, data.COLOURS['gui_border'])
        # Upper border
        libt.console_rect(self.handler.gui, 0, 0, config.GUI_WIDTH, upper_height, 
                          False, libt.BKGND_SCREEN)
        # Lower border
        libt.console_rect(self.handler.gui, 0, config.GUI_HEIGHT - config.BORDER_WIDTH/2,  
                          config.GUI_WIDTH, upper_height, False, libt.BKGND_SCREEN)
        # Left border
        libt.console_rect(self.handler.gui, 0, upper_height, config.BORDER_WIDTH / 2, 
                          left_height, False, libt.BKGND_SCREEN)
        # Right border
        libt.console_rect(self.handler.gui, config.GUI_WIDTH - config.BORDER_WIDTH/2, upper_height, 
                          config.BORDER_WIDTH / 2, left_height, False, libt.BKGND_SCREEN)
        # Middle border
        libt.console_rect(self.handler.gui, (config.GUI_WIDTH - 1)/2 - config.BORDER_WIDTH/2, upper_height, 
                          config.BORDER_WIDTH, left_height, False, libt.BKGND_SCREEN)

        # Hover details
        libt.console_set_default_foreground(self.handler.gui, data.COLOURS['text'])
        libt.console_print_ex(self.handler.gui, (config.GUI_WIDTH - 1)/2, 0,
                              libt.BKGND_NONE, libt.CENTER, self.objects_under_mouse())


class StatusBar(GUIElement):
    """
    Class for status bars.

    x: x-coordinate of the bar
    y: y-coordinate of the bar
    name: name displayed for the bar
    val: current value out of the maximum
    max_val: the largest value the bar can contain
    bar_colour: colour of the bar portion that is filled
    back_colour: colour of the bar portion that is unfilled
    """
    def __init__(self, x, y, name, val, max_val, bar_colour, back_colour):
        GUIElement.__init__(self)
        self.x = x
        self.y = y
        self.name = name
        self.val = val
        self.max_val = max_val
        self.bar_colour = bar_colour
        self.back_colour = back_colour

    def draw(self):
        """
        Creates a bar that shows the current value 
        out of the given maximum.
        """
        filled_width = int(float(self.val) / self.max_val * config.BAR_WIDTH)

        libt.console_set_default_background(self.handler.gui, self.back_colour)
        libt.console_rect(self.handler.gui, self.x, self.y, config.BAR_WIDTH, config.BAR_HEIGHT, 
                          False, libt.BKGND_SCREEN)

        libt.console_set_default_background(self.handler.gui, self.bar_colour)
        if filled_width > 0:
            libt.console_rect(self.handler.gui, self.x, self.y, filled_width, config.BAR_HEIGHT, 
                              False, libt.BKGND_SCREEN)

        bar_midpoint = (int(config.BAR_WIDTH/2 + self.x), int(config.BAR_HEIGHT/2 + self.y))

        libt.console_set_default_foreground(self.handler.gui, data.COLOURS['text'])
        libt.console_print_ex(self.handler.gui, bar_midpoint[0], bar_midpoint[1], 
                              libt.BKGND_NONE, libt.CENTER,
                              "{}: {}/{}".format(self.name, self.val, self.max_val))

        libt.console_set_default_foreground(self.handler.gui, data.COLOURS['text'])


class HealthBar(StatusBar):
    """The health bar."""
    def __init__(self):
        StatusBar.__init__(self, config.BORDER_WIDTH, config.BORDER_WIDTH, "HP", 
                           self.handler.player.hp, self.handler.player.max_hp, 
                           data.COLOURS['bar_hp'], data.COLOURS['bar_hp_unfilled'])


class MessageBox(GUIElement):
    """Messages are displayed here."""
    def __init__(self):
        GUIElement.__init__(self)
        self.messages = []
        self.max_messages = config.MSG_HEIGHT - config.BORDER_WIDTH

    def add_msg(self, msg, colour=data.COLOURS['text']):
        """Adds a message to the message box."""
        wrapped = textwrap.wrap(msg, config.MSG_WIDTH - config.BORDER_WIDTH*2)

        for line in wrapped:
            if len(self.messages) == self.max_messages:
                del self.messages[0]
            self.messages.append((line, colour))

    def draw(self):
        """Draws messages in the message box."""
        y = config.BORDER_WIDTH
        for (msg, colour) in self.messages:
            libt.console_set_default_foreground(self.handler.gui, colour)
            libt.console_print_ex(self.handler.gui, config.MSG_WIDTH - 1 + config.BORDER_WIDTH, y, 
                                  libt.BKGND_NONE, libt.LEFT, msg)
            y += 1


class Overlay(GUIElement):
    """
    Base class for anything that pops up over the game screen.
    Requires that the given header is exactly one line high.

    x: top-left x-coordinate to blit the overlay
    y: top-left y-coordinate to blit the overlay
    header: title of the overlay
    header_align: alignment of the header; left, centre or right
    width: width of the overlay
    height: height of the overlay
    ingame: true if overlay is being called while game is in progress
    pad: minimum amount of space on all sides between text and border
    """
    def __init__(self, x, y, header, header_align, width, height, ingame, pad):
        GUIElement.__init__(self)
        self.x = x
        self.y = y
        self.header = header
        self.header_align = header_align
        self.width = width
        self.height = height
        self.ingame = ingame
        self.pad = pad

        self.header_height = libt.console_get_height_rect(self.handler.game_map, 0, 0, 
                                                          config.SCREEN_WIDTH, 
                                                          config.SCREEN_HEIGHT, 
                                                          self.header)
        assert self.header_height == 1

        # Initialize overlay and define some parameters
        self.overlay = libt.console_new(self.width, self.height)
        self.header_pad = 1

    def background(self):
        """Draws the contents behind the overlay."""
        pass
    
    def draw(self):
        """
        Adds the header to the overlay and blits its contents
        to the root console.
        """
        if self.header_align == data.LEFT:
            self.header_x = self.pad
            self.libt_align = libt.LEFT
        elif self.header_align == data.CENTER:
            self.header_x = (self.width - 1)/2
            self.libt_align = libt.CENTER
        else:
            self.header_x = self.width - 1 - self.pad
            self.libt_align = libt.RIGHT

        libt.console_set_default_foreground(self.overlay, data.COLOURS['text'])
        libt.console_print_ex(self.overlay, self.header_x, self.header_pad, 
                              libt.BKGND_NONE, self.libt_align, self.header)
        libt.console_blit(self.overlay, 0, 0, self.width, self.height, 
                          0, self.x, self.y, 1.0, 0.7)


class SelectMenu(Overlay):
    """
    Class for menu that allows selection of options.

    align: alignment of the options; anything other than left align
    requires that tail_txt is empty
    options: the selections that can be made in the menu
    empty_options: string that is displayed when no options exist
    tail_txt: additional text that is aligned right of each option,
    must be same length as options
    max_options: number of options to show at once
    bindings: additional keys that enable additional interactivity
    within the menu
    escape: list of keys that dismiss the menu
    """
    def __init__(self, x, y, align, header, header_align, width, height, ingame,
                 options, empty_options, tail_txt, max_options, bindings,
                 escape, pad):
        Overlay.__init__(self, x, y, header, header_align, width, height, ingame, pad)
        self.align = align
        self.options = options
        self.empty_options = empty_options
        self.tail_txt = tail_txt
        self.max_options = max_options
        self.max_selection = len(self.options) - 1
        self.slice_head = 0
        self.slice_tail = min(self.max_options, self.max_selection + 1)
        self.selection_index = 0
        self.bindings = bindings
        self.escape = escape
        self.active = True
        self.status = None

        if self.align != data.LEFT:
            assert not tail_txt

    def draw(self):
        """
        Prints all the given options up to the specified max_options,
        then draws the background and header.
        """
        self.background()
        libt.console_clear(self.overlay)

        if self.options:
            def print_options():
                """Prints each option out in a column."""
                if self.align == data.LEFT:
                    self.option_x = self.pad
                    self.libt_align = libt.LEFT
                elif self.align == data.CENTER:
                    self.option_x = (self.width - 1)/2
                    self.libt_align = libt.CENTER
                else:
                    self.option_x = self.width - 1 - self.pad
                    self.libt_align = libt.RIGHT

                if y - self.header_height - self.header_pad == self.selection_index - self.slice_head:
                    libt.console_set_default_foreground(self.overlay, 
                                                        data.COLOURS['selection_text'])
                    libt.console_print_ex(self.overlay, self.option_x, y + self.pad,
                                          libt.BKGND_NONE, self.libt_align, text)
                else:
                    libt.console_set_default_foreground(self.overlay, 
                                                        data.COLOURS['text'])
                    libt.console_print_ex(self.overlay, self.option_x, y + self.pad, 
                                          libt.BKGND_NONE, self.libt_align, text)

            y = self.header_height + self.header_pad

            if self.tail_txt:
                for option, tail in zip(self.options[self.slice_head:self.slice_tail], 
                                        self.tail_txt[self.slice_head:self.slice_tail]):
                    padding = " " * (self.width - len(option) - len(tail) - 2*self.pad)
                    text = option + padding + tail
                    print_options()
                    y += 1
            else:
                for option in self.options[self.slice_head:self.slice_tail]:
                    text = option
                    print_options()
                    y += 1
        else:
            libt.console_set_default_foreground(self.overlay, data.COLOURS['text'])
            libt.console_print_ex(self.overlay, self.pad, self.header_height + self.header_pad + self.pad, 
                                  libt.BKGND_NONE, libt.LEFT, self.empty_options)

        Overlay.draw(self)
        libt.console_flush()

    def select(self):
        """Handles selection of options in the menu."""
        while self.active:
            choice = libt.console_check_for_keypress(True)

            if self.escape:
                for key in self.escape:
                    if choice.vk == key or chr(choice.c) == key:
                        return
            
            if choice.vk == libt.KEY_UP:
                if self.selection_index > self.slice_head:
                    self.selection_index -= 1
                elif self.slice_head > 0:
                    self.selection_index -= 1
                    self.slice_head -= 1
                    self.slice_tail -= 1
            elif choice.vk == libt.KEY_DOWN:
                if self.selection_index < self.slice_tail - 1:
                    self.selection_index += 1
                elif self.slice_tail < self.max_selection + 1:
                    self.selection_index += 1
                    self.slice_head += 1
                    self.slice_tail += 1
            elif choice.vk == libt.KEY_ENTER and choice.lalt:
                libt.console_set_fullscreen(not libt.console_is_fullscreen())
            elif choice.vk == libt.KEY_ENTER and self.options:
                if self.selection_index in self.bindings:
                    status = self.bindings[self.selection_index]()

                    if (status == data.REBUILD and 
                        self.header != self.handler.main_menu.header):
                        return data.REBUILD
                    elif status == data.REBUILD:
                        self.selection_index = 0
                        self.handler.play()
            else:
                for key in self.bindings:
                    if chr(choice.c) == key:
                        self.bindings[key]()
                        break

            self.draw()

        return self.status


class StandardMenu(SelectMenu):
    """
    Menu with one pixel border around the edges 
    and one character space between the header and body.
    x and y-coordinates default to middle of screen if not provided.
    """
    def __init__(self, align, header, header_align, content_width, ingame, 
                 options, empty_options, tail_txt, max_options, bindings, escape,
                 x=None, y=None):
        width = content_width + 2
        height = max_options + 4

        if not x:
            x = (config.SCREEN_WIDTH - 1)/2 - width/2

        if not y:
            y = (config.SCREEN_HEIGHT - 1)/2 - height/2

        SelectMenu.__init__(self, x, y, align, header, header_align, content_width + 2, 
                            max_options + 4, ingame, options, empty_options, 
                            tail_txt, max_options, bindings, escape, 1)


class InGameMenu(StandardMenu):
    """Options menu when currently within a game."""
    def __init__(self):
        options = ["Resume", "Save Game", "Load Game", "Main Menu"]
        bindings = {
            0: self.bind_resume,
            1: self.bind_save_menu,
            2: self.bind_load_menu,
            3: self.bind_main_menu
        }

        StandardMenu.__init__(self, data.LEFT, "Options", data.CENTER, 
                              longest_str(options), True, options, 
                              "", [], 4, bindings, [libt.KEY_ESCAPE])

    def background(self):
        self.handler.render_all()

    def bind_resume(self):
        """Dismisses menu."""
        self.active = False

    def bind_save_menu(self):
        """Brings up the save menu."""
        save_menu = SaveMenu()
        save_menu.draw()
        save_menu.select()

    def bind_load_menu(self):
        """Brings up the load menu."""
        load_menu = LoadMenu(True)
        load_menu.draw()
        return load_menu.select()

    def bind_main_menu(self):
        """Brings up the main menu."""
        self.active = False
        self.status = data.EXIT


class InventoryMenu(StandardMenu):
    """Popup that appears when entering inventory view."""
    def __init__(self):
        bindings = {
            'd': self.bind_drop,
            'e': self.bind_use_item
        }
        self.item_use_bindings = {}

        item_names = []
        item_qty = []
        index = 0

        for item in self.handler.player.inv:
            if not item.stackable:
                for i in range(self.handler.player.inv[item]):
                    item_names.append(item.name)
                    item_qty.append("")
                    
                    self.item_use_bindings[index] = item.use
                    index += 1
            else:
                item_names.append(item.name)
                item_qty.append("Qty: {}".format(self.handler.player.inv[item]))

                self.item_use_bindings[index] = item.use
                index += 1

        StandardMenu.__init__(self, data.LEFT, "Inventory", data.CENTER, 40,
                              True, item_names, "Your inventory is empty.", 
                              item_qty, config.ITEMS_PER_PAGE, 
                              bindings, [libt.KEY_ESCAPE, "i"])

    def background(self):
        self.handler.render_all()

    def remove_option(self, item):
        """
        Takes an item in player's inventory and decreases its count in
        the list of options, removing it altogether when appropriate.
        Returns current count of the item in player's inventory.
        """
        item_count = self.handler.player.inv[item]

        if item_count == 1 or not item.stackable:
            del self.options[self.selection_index]
            del self.tail_txt[self.selection_index]

            if self.selection_index == self.max_selection and self.slice_head > 0:
                self.slice_head -= 1
                self.slice_tail -= 1
                self.selection_index -= 1
            elif self.selection_index == self.max_selection and self.selection_index > 0:
                self.slice_tail -= 1
                self.selection_index -= 1

            self.max_selection -= 1
        else:
            self.tail_txt[self.selection_index] = "Qty: {}".format(item_count - 1)

        return item_count

    def bind_drop(self):
        """Binding for dropping an item."""
        if self.options:
            for item in self.handler.player.inv:
                if item.name == self.options[self.selection_index]:
                    self.remove_option(item)
                    self.handler.player.player_drop(item)
                    break

    def bind_use_item(self):
        """Wrapper for inventory items' use() method."""
        if self.selection_index in self.item_use_bindings:
            used = self.item_use_bindings[self.selection_index]()

            if used.consumable:
                if self.remove_option(used) == 1:
                    self.item_use_bindings.pop(self.selection_index)

                self.handler.player.remove_from_inv(used)


class MainMenu(StandardMenu):
    """The main menu."""
    def __init__(self):
        options = ["New Game", "Load Game", "Quit"]
        bindings = {
            0: self.bind_new_game,
            1: self.bind_load_menu,
            2: self.bind_quit
        }

        y = config.SCREEN_HEIGHT/2 + len(options)

        StandardMenu.__init__(self, data.LEFT, "BOGEY", data.CENTER, 
                              longest_str(options), False, options, 
                              "", [], 3, bindings, [], None, y)

    def background(self):
        backdrop = libt.image_load(config.get_img_path('title'))
        libt.image_blit_2x(backdrop, 0, 0, 0)

    def bind_new_game(self):
        """Starts a new game."""
        self.handler.new_game()
        self.handler.play()

    def bind_load_menu(self):
        """Brings up the load game menu."""
        load_menu = LoadMenu(False)
        load_menu.draw()
        return load_menu.select()

    def bind_quit(self):
        """Exits program."""
        self.active = False


class SaveLoadMenu(StandardMenu):
    """Menu that displays saved games and empty save slots."""
    def __init__(self, header, ingame):
        self.save_handler = save.SaveHandler()
        options = []
        occupied = []
        bindings = {
            'd': self.bind_delete_save
        }
        count = 0

        for save_file in self.save_handler.save_status():
            options.append("Slot {}".format(count + 1))

            if save_file:
                occupied.append("FILLED")
            else:
                occupied.append("EMPTY")

            count += 1

        StandardMenu.__init__(self, data.LEFT, header, data.CENTER, 30,
                              ingame, options, "", occupied, 5, bindings, 
                              [libt.KEY_ESCAPE])

    def bind_delete_save(self):
        """Deletes selected save file."""
        if self.tail_txt[self.selection_index] == "FILLED":
            self.tail_txt[self.selection_index] = "EMPTY"
            self.save_handler.delete_save(self.selection_index)


class SaveMenu(SaveLoadMenu):
    """Menu to save games."""
    def __init__(self):
        SaveLoadMenu.__init__(self, "Save Game", True)

        for i in range(config.MAX_SAVES):
            self.bindings[i] = self.bind_save_game

    def background(self):
        self.handler.render_all()

    def bind_save_game(self):
        """Saves game at player's current selection index."""
        if not self.save_handler.is_save(self.selection_index):
            self.tail_txt[self.selection_index] = "FILLED"

        save_data = {
            'world': self.handler.world,
            'map_objects': self.handler.map_objects,
            'player_index': self.handler.map_objects['characters'].index(self.handler.player),
            'messages': self.handler.message_box.messages,
            'game_state': self.handler.game_state,
            'player_action': self.handler.player_action
        }

        self.save_handler.add_data(save_data, self.selection_index)


class LoadMenu(SaveLoadMenu):
    """Menu to load games."""
    def __init__(self, ingame):
        SaveLoadMenu.__init__(self, "Load Game", ingame)
        status = self.save_handler.save_status()

        for i in range(config.MAX_SAVES):
            if status[i]:
                self.bindings[i] = self.bind_load_game

    def background(self):
        if self.ingame:
            self.handler.render_all()
        else:
            backdrop = libt.image_load(config.get_img_path('title'))
            libt.image_blit_2x(backdrop, 0, 0, 0)

    def bind_load_game(self):
        """Loads game at player's current selection index, if possible."""
        if self.save_handler.is_save(self.selection_index):
            if not self.ingame:
                self.handler.new_game()
            else:
                libt.console_clear(self.handler.game_map)

            save_data = self.save_handler.get_data(self.selection_index)

            self.handler.world = save_data['world']
            self.handler.map_objects = save_data['map_objects']
            self.handler.player = self.handler.map_objects['characters'][save_data['player_index']]
            self.handler.game_state = save_data['game_state']
            self.handler.player_action = save_data['player_action']
            self.handler.message_box.messages = save_data['messages']
            self.handler.init_fov()

            return data.REBUILD


# Miscellaneous functions
def longest_str(lst_of_str):
    """Returns the length of the longest string in a list of strings."""
    longest = ""

    for string in lst_of_str:
        if len(string) > len(longest):
            longest = string

    return len(longest)
