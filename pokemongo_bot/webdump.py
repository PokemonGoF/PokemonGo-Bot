# -*- coding: utf-8 -*-
import os


def file_does_exist(location):
    """Will check if file is exist.

    :param location: file location.
    """

    if not os.path.isfile(location):
        return False

    return True

