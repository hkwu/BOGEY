#
# gui.py
# Classes for each element of the GUI
#

import textwrap

import libtcodpy as libt

import config
import data


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
                    names.append("%s" % entity.name)
                else:
                    names.append("%s [%d/%d]" % (entity.name, entity.hp, entity.max_hp))

        # Names of items
        for item in self.handler.map_objects['items']:
            if (item.x == x and item.y == y and
                libt.map_is_in_fov(self.handler.fov_map, item.x, item.y)):
                names.append("%s" % item.name)

        names = ", ".join(names)
        return names.capitalize()

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
        libt.console_rect(self.handler.gui, config.GUI_WIDTH/2 - config.BORDER_WIDTH/2, upper_height, 
                          config.BORDER_WIDTH, left_height, False, libt.BKGND_SCREEN)

        # Hover details
        libt.console_set_default_foreground(self.handler.gui, data.COLOURS['text'])
        libt.console_print_ex(self.handler.gui, config.GUI_WIDTH / 2, 0,
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
                              "%s: %d/%d" % (self.name, self.val, self.max_val))

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
            libt.console_print_ex(self.handler.gui, config.MSG_WIDTH + config.BORDER_WIDTH, y, 
                                  libt.BKGND_NONE, libt.LEFT, msg)
            y += 1


class Overlay(GUIElement):
    """
    Base class for anything that pops up over the game screen.

    header: title of the overlay
    width: width of the overlay
    height: height of the overlay
    """
    def __init__(self, header, width, height):
        GUIElement.__init__(self)
        self.header = header
        self.width = width
        self.height = height
        self.overlay = libt.console_new(self.width, self.height)
        self.x = config.SCREEN_WIDTH/2 - self.width/2
        self.y = config.SCREEN_HEIGHT/2 - self.height/2
        self.header_height = libt.console_get_height_rect(self.overlay, 0, 0, 
                                                          self.width, self.height, 
                                                          self.header)

    def draw(self):
        libt.console_set_default_foreground(self.overlay, data.COLOURS['text'])
        libt.console_print_rect_ex(self.overlay, 0, 0, self.width, self.height, 
                                   libt.BKGND_NONE, libt.LEFT, self.header)
        libt.console_blit(self.overlay, 0, 0, self.width, self.height, 
                          0, self.x, self.y, 1.0, 0.7)


class SelectMenu(Overlay):
    """
    Class for menu that allows selection of options.

    options: the selections that can be made in the menu
    empty_options: string that is displayed when no options exist
    selection_index: zero-based index that player's selection is on
    max_selection: maximum index for selections
    """
    def __init__(self, header, width, height, options, empty_options):
        Overlay.__init__(self, header, width, height)
        self.options = options
        self.empty_options = empty_options
        self.selection_index = 0
        self.max_selection = len(options) - 1

    def draw(self):
        Overlay.draw(self)

        if self.options:
            y = self.header_height
            for option in self.options:
                text = "%s" % (option)

                if y - self.header_height == self.selection_index:
                    libt.console_set_default_foreground(self.overlay, 
                                                        data.COLOURS['selection_text'])
                    libt.console_print_ex(self.overlay, 0, y,
                                          libt.BKGND_NONE, libt.LEFT, text)
                else:
                    libt.console_set_default_foreground(self.overlay, 
                                                        data.COLOURS['text'])
                    libt.console_print_ex(self.overlay, 0, y, 
                                          libt.BKGND_NONE, libt.LEFT, text)

                y += 1
        else:
            libt.console_print_ex(self.overlay, 0, self.header_height, libt.BKGND_NONE, 
                                  libt.LEFT, self.empty_options)

        libt.console_blit(self.overlay, 0, 0, self.width, self.height, 
                          0, self.x, self.y, 1.0, 0.7)
        libt.console_flush()

    def select(self):
        """Handles selection of options in the menu."""
        choice = libt.console_check_for_keypress(True)

        while choice.vk != libt.KEY_ESCAPE and chr(choice.c) != "i":
            libt.console_wait_for_keypress(True)
            choice = libt.console_wait_for_keypress(True)

            self.handler.render_all()
            libt.console_flush()

            if choice.vk == libt.KEY_UP and self.selection_index > 0:
                self.selection_index -= 1
                self.draw()
            elif choice.vk == libt.KEY_DOWN and self.selection_index < self.max_selection:
                self.selection_index += 1
                self.draw()
            else:
                self.draw()


class InventoryMenu(SelectMenu):
    """Popup that appears when entering inventory view."""
    def __init__(self):
        self.item_names = []
        for item in self.handler.player.inv:
            self.item_names.append(item.name)

        SelectMenu.__init__(self, "Inventory", 50, 50, self.item_names,
                            "Your inventory is empty.")
