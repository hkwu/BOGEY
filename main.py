##############################################
# BOGEY
# Created by Kelvin Wu
# Initial commit 2015-06-13
# Based on Jotaf's Complete Roguelike Tutorial
##############################################

import libtcodpy as libt
import config
import data
import state

# Set the font, initialize window
libt.console_set_custom_font("dejavu10x10_gs_tc.png", 
                             libt.FONT_TYPE_GREYSCALE 
                             | libt.FONT_LAYOUT_TCOD)
libt.console_init_root(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, 
                       "BOGEY", False)
libt.console_credits()

# Keypress delay
libt.console_set_keyboard_repeat(50, 100)

# Limit FPS
libt.sys_set_fps(60)

# Main loop
game = state.StateHandler()

while not libt.console_is_window_closed():
    libt.sys_check_for_event(libt.EVENT_KEY_PRESS | libt.EVENT_MOUSE, 
                             game.key, game.mouse)
    game.render_all()
    libt.console_flush()

    for lst in game.map_objects:
        game.clear_obj(game.map_objects[lst])

    player_action = game.keybinds()
    if player_action == data.EXIT:
        break
    elif game.game_state == data.PLAY and player_action != data.NO_MOVE:
        for mob in game.map_objects['mobs']:
            mob.action_handler()
