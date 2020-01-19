#!/usr/bin/env python3

"""
Script:	blank-sh.py
Date:	2020-01-10
Platform: macOS/Linux
Description:
Retrieves and processes ...
"""
__author__ = 'thedzy'
__copyright__ = 'Copyright 2020, thedzy'
__license__ = 'GPL'
__version__ = '1.0'
__maintainer__ = 'thedzy'
__email__ = 'thedzy@hotmail.com'
__status__ = 'Development'

import logging
import subprocess
import time

from modules_common import timer


@timer(__file__)
def get(api_classic=None, api_universal=None):
    log = []

    # Here is an example of using shell code to get the data
    # Below is how data can be processed in shell and returned to python
    shell_processing = """
    # TODO: Shell code to process API and output 
    # TODO: verify and parse all data to ensure error freee  
    echo "path/to/file, modulename, objectname, 0"
    echo "path/to/file, modulename, objectname, 1"
    """

    processinfo = subprocess.run(shell_processing,
                                 shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

    if processinfo.returncode == 0:
        # TODO: Process string stdout into list of tuples
        print(processinfo.stdout)
        lines = processinfo.stdout.split('\n')
        for line in lines:
            item = tuple(line.split(','))
            if len(item) == 4:
                log.append(item)

    return log

