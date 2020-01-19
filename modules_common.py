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

import logging
import os
import time


def timer(script_file=None):
    def timer_wrapper(func):
        def timer_func(*args, **kwargs):
            # Get the start time
            start_time = time.time()

            if script_file is None:
                module = 'undefined'
            else:
                module = os.path.basename(script_file).split('.')[0]

            logging.info('Starting {}'.format(module))

            # Run function
            result = func(*args, **kwargs)

            # Print timeer
            minutes, seconds = divmod(time.time() - start_time, 60)
            hours, minutes = divmod(minutes, 60)
            logging.info('Total runtime for {3}: {0:.0f}:{1:.0f}:{2:.3f}'.format(hours, minutes, seconds, module))

            return result

        return timer_func

    return timer_wrapper

