#!/usr/bin/env python3

"""
Script:	modules_common.py
Date:	2020-01-10
Platform: macOS/Linux
Description:
Common functions for modules
"""
__author__ = 'thedzy'
__copyright__ = 'Copyright 2020, thedzy'
__license__ = 'GPL'
__version__ = '1.0'
__maintainer__ = 'thedzy'
__email__ = 'thedzy@hotmail.com'
__status__ = 'Development'

import time


def runtime_message(start_time, path):
    """
    Display total run time message
    :param start_time: (int) Epoch startime
    :param path: (str) module name
    :return: (str) message
    """
    minutes, seconds = divmod(time.time() - start_time, 60)
    hours, minutes = divmod(minutes, 60)

    return 'Total runtime for {3}: {0:.0f}:{1:.0f}:{2:.3f}'.format(hours, minutes, seconds, path)


print('Not intendedt o run on independantly')

