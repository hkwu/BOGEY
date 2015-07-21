#
# config.py
# Game settings
#

import os

# File paths
IMG_DIR = "img"
IMG_FILES = {
    'title': "title.png",
    'char_sheet': "dejavu10x10_gs_tc.png"
}
SAVE_DIR = "saves"


def get_img_path(key):
    """Returns the path of the image with given key."""
    return os.path.join(IMG_DIR, IMG_FILES[key])


def get_save_path(index):
    """
    Returns the path of the save with given index 
    (which may or may not exist).
    """
    return os.path.join(SAVE_DIR, "save_" + str(index))

# Save data
MAX_SAVES = 5

# Console dimensions
SCREEN_WIDTH = 150
SCREEN_HEIGHT = 80
MAP_WIDTH = SCREEN_WIDTH
MAP_HEIGHT = int(0.7 * SCREEN_HEIGHT)
GUI_WIDTH = SCREEN_WIDTH
GUI_HEIGHT = SCREEN_HEIGHT - MAP_HEIGHT

# GUI dimensions
BORDER_WIDTH = 2
BAR_WIDTH = (GUI_WIDTH - 1)/2 - 2*BORDER_WIDTH
BAR_UNADJUSTED = int(0.1 * GUI_HEIGHT)
BAR_HEIGHT = BAR_UNADJUSTED if BAR_UNADJUSTED % 2 == 1 else BAR_UNADJUSTED + 1
MSG_WIDTH = GUI_WIDTH / 2
MSG_HEIGHT = GUI_HEIGHT - BORDER_WIDTH
ITEMS_PER_PAGE = 15

# Room data
ROOM_MAX_SIZE = 25
ROOM_MIN_SIZE = 5
MAX_ROOMS = 50
MAX_MOBS = 3
MAX_ITEMS = 3

# FOV
FOV = 0
FOV_LIT_WALLS = True
LIGHT_RANGE = 10
