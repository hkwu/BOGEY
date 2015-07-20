#
# save.py
# Manages saving and loading
#

import os
import shelve
import config


class SaveHandler(object):
    def __init__(self):
        pass

    def is_save(self, index):
        """Returns true if a save file exists in given index."""
        return os.path.isfile(config.SAVE_DIR + "save_" + str(index))

    def save_status(self):
        """
        Returns list of booleans representing whether 
        or not each save index is filled.
        """
        lst = []

        for i in range(config.MAX_SAVES):
            if self.is_save(i):
                lst.append(True)
            else:
                lst.append(False)

        return lst

    def add_data(self, key, val, index):
        """
        Adds a key/value pair to the save file at index.
        Creates the file if it does not exist.
        """
        if not os.path.exists(config.SAVE_DIR):
            os.makedirs(config.SAVE_DIR)

        savefile = shelve.open(config.SAVE_DIR + "save_" + str(index))
        savefile[key] = val
        savefile.close()

    def get_data(self, key, index):
        """
        Returns the value of the given key in the save file at index.
        Requires that the file and key exists.
        """
        assert self.is_save(index)

        savefile = shelve.open(config.SAVE_DIR + "save_" + str(index), "r")
        assert key in savefile

        value = savefile[key]
        savefile.close()

        return value
