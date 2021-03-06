#
# data.py
# Global constants
#

import libtcodpy as libt

# Colours
COLOURS = {
    'bg': libt.white,
    'wall': libt.light_grey,
    'lit_wall': libt.Color(173, 173, 0),
    'ground': libt.light_grey,
    'lit_ground': libt.Color(21, 21, 21),
    'stairs': libt.light_fuchsia,
    'player': libt.black,
    'mob': libt.red,
    'gui_bg': libt.black,
    'gui_border': libt.darkest_grey,
    'bar_hp': libt.dark_red,
    'bar_hp_unfilled': libt.darker_red,
    'text': libt.lightest_grey,
    'selection_text': libt.yellow,
    'mob_behaviour_text': libt.amber,
    'mob_atk_text': libt.flame,
    'player_atk_text': libt.grey,
    'player_kill_text': libt.green,
    'player_die_text': libt.white,
    'player_item_text': libt.azure,
    'player_use_item_text': libt.Color(215, 223, 1),
    'player_gain_hp_text': libt.green,
    'weapons': libt.copper,
    'consumables': libt.Color(191, 0, 255)
}

# Game states
EXIT = "exit"
PLAY = "play"
NO_MOVE = "no_move"
REBUILD = "rebuild"
CONFIRM_YES = "confirm_yes"
CONFIRM_NO = "confirm_no"

# Entity states
HOLD = 0
CHASE = 1
RUN = 2
DEAD = "dead"

# Text alignment for overlays
LEFT = "left"
CENTER = "center"
RIGHT = "right"
