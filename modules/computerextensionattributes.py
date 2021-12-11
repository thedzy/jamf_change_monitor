#!/usr/bin/env python3

"""
Script:	computerextensionattributes.py
Date:	2020-01-10
Platform: macOS/Linux
Description:
Retrieves and processes /JSSResource/computerextensionattributes
"""
__author__ = 'thedzy'
__copyright__ = 'Copyright 2020, thedzy'
__license__ = 'GPL'
__version__ = '1.0'
__maintainer__ = 'thedzy'
__email__ = 'thedzy@hotmail.com'
__status__ = 'Development'

import difflib
import json
import logging
import re
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
    sort_keys = False

    # Create folders if it does not exist
    if not module_path.exists():
        module_path.mkdir(exist_ok=True)

    # Query api
    api_query = api_classic.get_data('computerextensionattributes')
    logging.debug(f'Query {api_query.data}')

    if api_query.success:
        data_objects = api_query.data['computer_extension_attributes']

        # Remove files
        for file in module_path.iterdir():
            if re.match(r'^\d+', file.name):
                if all(False for data_object in data_objects if int(data_object['id']) == int(file.stem)):
                    with open(file, 'r') as saved_file:
                        name = get_name(json.load(saved_file))
                    log[module]['remove'].append({
                        'name': name,
                        'id': file.stem,
                        'file': file.as_posix()
                    })

        # Save new/changed data
        for data_object in data_objects:
            object_query = api_classic.get_data('computerextensionattributes', 'id', data_object['id'])
            if object_query.success:
                name = get_name(object_query.data)
                file_path = module_path.joinpath(str(data_object['id']))

                new_script = {} if object_query.data['computer_extension_attribute']['input_type'][
                                       'type'] != 'script' else \
                    object_query.data['computer_extension_attribute']['input_type']['script']
                if object_query.data['computer_extension_attribute']['input_type']['type'] == 'script':
                    del object_query.data['computer_extension_attribute']['input_type']['script']
                new_data = json.dumps(clean_data(object_query.data), indent=4, sort_keys=sort_keys)

                # Data
                if Path(file_path).with_suffix('.data').exists():
                    with open(file_path.with_suffix('.data'), 'r+') as file:
                        old_data = file.read()
                        if old_data != new_data:
                            file.seek(0)
                            file.truncate()
                            file.write(new_data)
                            log[module]['diff'].append({
                                'name': name,
                                'id': data_object['id'],
                                'file': file_path.with_suffix('.data').as_posix()
                            })
                else:
                    with open(file_path.with_suffix('.data'), 'w') as file:
                        file.write(json.dumps(clean_data(object_query.data), indent=4, sort_keys=sort_keys))
                        log[module]['add'].append({
                            'name': name,
                            'id': data_object["id"],
                            'file': file_path.with_suffix('.data').as_posix()
                        })

                # Script
                if Path(file_path).with_suffix('.script').exists():
                    with open(file_path.with_suffix('.script'), 'r+') as file:
                        old_script = file.read()
                        diff = list(difflib.context_diff(old_script.splitlines(), new_script.splitlines()))
                        if len(diff) > 0:
                            file.seek(0)
                            file.truncate()
                            file.write(new_script)
                            log[module]['diff'].append({
                                'name': name,
                                'id': data_object['id'],
                                'file': file_path.with_suffix('.script').as_posix()
                            })
                else:
                    with open(file_path.with_suffix('.script'), 'w') as file:
                        file.write(new_script)
                        log[module]['add'].append({
                            'name': name,
                            'id': data_object["id"],
                            'file': file_path.with_suffix('.script').as_posix()
                        })

        logging.info('Completed {}'.format(module))
    else:
        logging.info('Failed to retrieve: {}'.format(module))

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

    name = json_data['computer_extension_attribute']['name']

    return name
