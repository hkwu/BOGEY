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
    'player_die_text': libt.white,
    'weapons': libt.copper
}

# Game states
EXIT = "exit"
PLAY = "play"
NO_MOVE = "no_move"

# Entity states
HOLD = 0
CHASE = 1
RUN = 2
DEAD = "dead"