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
import time
from pathlib import Path


def timer(module_file=None):
    def timer_wrapper(func):
        def timer_func(*args, **kwargs):
            # Get the start time
            start_time = time.time()

            if module_file is None:
                module = 'undefined'
            else:
                module = Path(module_file).stem

            logging.info(f'Starting {module}')

            # Run function
            result = func(*args, **kwargs)

            # Print timer
            minutes, seconds = divmod(time.time() - start_time, 60)
            hours, minutes = divmod(minutes, 60)
            logging.info(f'Total runtime for {module}: {hours:.0f}:{minutes:.0f}:{seconds:.3f}')

            return result

        return timer_func

    return timer_wrapper
