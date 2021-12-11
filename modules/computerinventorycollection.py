#!/usr/bin/env python3

"""
Script:	computerinventorycollection.py
Date:	2020-01-10
Platform: macOS/Linux
Description:
Retrieves and processes /JSSResource/computerinventorycollection
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
from pathlib import Path

import modules_common


@modules_common.timer(__file__)
def get(api_classic=None, api_universal=None, repo_path=None):
    """
    Get data from the API
    :param api_classic: (JamfClassic)
    :param api_universal: (JamfUAPI)
    :param repo_path: (Path) Repo path
    :return: (list)(tuples)
    """
    module = Path(__file__).stem
    log = {
        module: {
            'diff': [],
            'add': [],
            'remove': []
        }
    }
    module_path = repo_path.joinpath(module)

    # Sort keys?
    sort_keys = True

    # Create folders if it does not exist
    if not module_path.exists():
        module_path.mkdir(exist_ok=True)

    # Query api
    api_query = api_classic.get_data('computerinventorycollection')
    logging.debug(f'Query: {api_query.data}')

    if api_query.success:
        # Single file
        file_path = module_path.joinpath('data')

        # Save new/changed data
        if file_path.exists():
            with open(file_path, 'r+') as file:
                old_data = file.read()
                new_data = json.dumps(clean_data(api_query.data), indent=4, sort_keys=sort_keys)
                if old_data != new_data:
                    file.seek(0)
                    file.truncate()
                    file.write(new_data)
                    log[module]['diff'].append({
                        'name': module,
                        'id': 0,
                        'file': file_path.as_posix()
                    })

            logging.info(f'Completed {module}')
        else:
            with open(file_path, 'w') as file:
                file.write(json.dumps(clean_data(api_query.data), indent=4, sort_keys=sort_keys))
                log[module]['add'].append({
                    'name': module,
                    'id': 0,
                    'file': file_path.as_posix()
                })
    else:
        logging.error('Failed to retrieve: {}'.format(module))

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

    name = None

    return name
