#!/usr/bin/env python3

"""
Script:	directorybindings.py
Date:	2020-01-10
Platform: macOS/Linux
Description:
Retrieves and processes /JSSResource/directorybindings
"""
__author__ = 'thedzy'
__copyright__ = 'Copyright 2020, thedzy'
__license__ = 'GPL'
__version__ = '1.0'
__maintainer__ = 'thedzy'
__email__ = 'thedzy@hotmail.com'
__status__ = 'Development'

import json
import logging
import os
import time

import modules_common


def get(api_classic=None, api_universal=None):
    """
    Get data from the API
    :param api_classic: (JamfClassic)
    :param api_universal: (JamfUAPI)
    :return: (list)(tuples)
    """
    start_time = time.time()

    log = []

    # Sort keys?
    sort_keys = True

    # Create folders if it does not exist
    path = 'directorybindings'
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        log.append((path, path, 'init', 3,))

    api_query = api_classic.get_data('directorybindings')

    if api_query.success:
        logging.info('Starting {}'.format(path))

        for file in os.listdir(path):
            if not any(data_object['id'] == int(os.path.splitext(file)[0]) for data_object in api_query.data['directory_bindings']):
                saved_file_path = '{0}/{1}'.format(path, file)
                with open(saved_file_path, 'r') as saved_file:
                    name = get_name(json.load(saved_file))
                log.append((saved_file_path, path, name, 1,))

                if not os.remove(saved_file_path):
                    logging.info('{0}: {1} File failed to be removed'.format(path, file))

        for data_object in api_query.data['directory_bindings']:
            object_query = api_classic.get_data('directorybindings', 'id', data_object['id'])
            if object_query.success:
                name = get_name(object_query.data)
                json_file_path = '{0}/{1}.json'.format(path, data_object['id'])

                with open(json_file_path, 'w') as file:
                    file.write(json.dumps(clean_data(object_query.data), indent=4, sort_keys=sort_keys))
                log.append((json_file_path, path, name, 0,))

        logging.info('Completed {}'.format(path))
    else:
        logging.info('Failed to retrieve: {}'.format(path))

    # Display run time
    logging.info(modules_common.runtime_message(start_time, path))

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

    name = json_data['directory_binding']['name']

    return name
