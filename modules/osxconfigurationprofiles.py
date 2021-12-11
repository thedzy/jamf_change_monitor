#!/usr/bin/env python3

"""
Script:	osxconfigurationprofiles.py
Date:	2020-01-10
Platform: macOS/Linux
Description:
Retrieves and processes /JSSResource/osxconfigurationprofiles
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
import plistlib
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
    api_query = api_classic.get_data('osxconfigurationprofiles')
    logging.debug(f'Query {api_query.data}')

    if api_query.success:
        data_objects = api_query.data['os_x_configuration_profiles']

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
            object_query = api_classic.get_data('osxconfigurationprofiles', 'id', data_object['id'])
            if object_query.success:
                name = get_name(object_query.data)
                file_path = module_path.joinpath(str(data_object['id']))

                raw_xml = plistlib.loads(
                    object_query.data['os_x_configuration_profile']['general']['payloads'].encode('utf-8'),
                    fmt=plistlib.FMT_XML)
                del object_query.data['os_x_configuration_profile']['general']['payloads']
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

                # XML
                if Path(file_path).with_suffix('.xml').exists():
                    with open(file_path.with_suffix('.xml'), 'r+') as file:
                        old_xml = file.read()
                        new_xml = clean_xml(raw_xml)
                        if old_xml != new_xml:
                            file.seek(0)
                            file.truncate()
                            file.write(new_xml)
                            log[module]['diff'].append({
                                'name': name,
                                'id': data_object['id'],
                                'file': file_path.with_suffix('.xml').as_posix()
                            })
                else:
                    with open(file_path.with_suffix('.xml'), 'w') as file:
                        new_xml = clean_xml(raw_xml)
                        file.write(new_xml)
                        log[module]['add'].append({
                            'name': name,
                            'id': data_object["id"],
                            'file': file_path.with_suffix('.xml').as_posix()
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


def clean_xml(xml_data):
    """
    Function to clean any data that you do not wish to store or changes on a regular basis
    :param xml_data: (plist) xml to be parsed
    :return: (str) Cleansed xml
    """

    def clean(data, keys):
        """
        Recursively remove values
        :param data: (dict/list) Data to parse
        :param keys: (list)((str) Keys to filter
        :return:
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    clean(value, keys)
                elif isinstance(value, list):
                    clean(value, keys)
                else:
                    if key.lower() in [key.lower() for key in keys]:
                        if isinstance(data[key], str):
                            data[key] = re.sub(r'\w', 'x', data[key], flags=re.IGNORECASE)
        elif isinstance(data, list):
            for value in data:
                clean(value, keys)

    # Clean keys
    # PayloadIdentifier and PayloadUUID as they will be different everytime
    # Password in attempt to clean passwords
    clean(xml_data, ['PayloadIdentifier', 'PayloadUUID', 'Password'])
    xml_data = plistlib.dumps(xml_data).decode()

    return xml_data


def get_name(json_data):
    """
    Rules to get the name of the object
    :param (dict) json_data:
    :return: (str) User friendly name
    """

    name = json_data['os_x_configuration_profile']['general']['name']

    return name
