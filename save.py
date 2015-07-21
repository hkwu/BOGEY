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
        return os.path.isfile(config.get_save_path(index))

    def save_status(self):
        """
        Returns list of booleans representing whether 
        or not each save index is filled.
        """
        return [self.is_save(i) for i in range(config.MAX_SAVES)]

    def add_data(self, data, index):
        """
        Adds all key/value pairs in data to the save file at index.
        Creates the file if it does not exist.
        """
        if not os.path.exists(config.SAVE_DIR):
            os.makedirs(config.SAVE_DIR)

        savefile = shelve.open(config.get_save_path(index))
        for key, val in data.iteritems():
            savefile[key] = val

        savefile.close()

    def get_data(self, index):
        """
        Returns a dictionary of stored data at save with given index.
        Requires that the file exists.
        """
        assert self.is_save(index)

        savefile = shelve.open(config.get_save_path(index), "r")
        data = {}

        for key, val in savefile.iteritems():
            data[key] = val

        savefile.close()
        return data

    def delete_save(self, index):
        """
        Deletes the save file with given index. 
        Requires that the file exists.
        """
        path = config.get_save_path(index)
        assert os.path.isfile(path)
        os.remove(path)
