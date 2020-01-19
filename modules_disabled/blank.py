#!/usr/bin/env python3

"""
Script:	blank.py
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
import time

from modules_common import timer


@timer(__file__)
def get(api_classic=None, api_universal=None):
    log = []

    # As long as the content is downloaded and the log returned contains the list of tuples of changes, this can be modeled any way

    return log


def clean_data(json_data):
    """
    Function to clean any data that you do not wish to store or changes on a regular basis
    :param json_data: (dict) json/dict to be parsed
    :return: (dict) cleansed json/dict
    """

    return json_data


def get_name(json_data):
    """
    Rules to get the name of the object
    :param (dict) json_data:
    :return: (str) User friendly name
    """

    name = json_data['module']['name']

    return name
