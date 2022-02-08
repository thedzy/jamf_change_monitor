#!/usr/bin/env python3

"""
Script:	computers-inventory.py
Date:	2021-12-07
Platform: macOS/Linux
Description:
Retrieves and processes /v1/computers-inventory
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
import re
from operator import itemgetter
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
    data_objects = []
    remainder, page, size = 1, 0, 200
    while remainder > 0:
        """ Available sections
            Too many sections impacts performance and makes reports noisy as computer details frequently change
            GENERAL,                    CERTIFICATES,
            DISK_ENCRYPTION,            ATTACHMENTS,
            PURCHASING,                 SECURITY,
            CONFIGURATION_PROFILES,     OPERATING_SYSTEM,
            PLUGINS,FONTS,A             LICENSED_SOFTWARE,
            APPLICATIONS,               IBEACONS,
            SERVICES,STORAGE,           SOFTWARE_UPDATES,
            USER_AND_LOCATION,          EXTENSION_ATTRIBUTES,
            PRINTERS,HARDWARE,          CONTENT_CACHING,
            LOCAL_USER_ACCOUNTS,        GROUP_MEMBERSHIPS,
        """
        query_sections = [
            'USER_AND_LOCATION',
            'LOCAL_USER_ACCOUNTS',
            'OPERATING_SYSTEM'
        ]
        api_query = api_universal.get_data('v1', 'computers-inventory', section=query_sections, page=page, size=size,
                                           sort='id:desc')
        logging.debug(f'Query {api_query.data}')
        remainder = (api_query.data['totalCount'] / size) - page
        data_objects.extend(api_query.data['results'])
        page += 1

    if api_query.success:
        # Remove files
        for file in module_path.iterdir():
            if re.match(r'\d+', file.name):
                if all([False for data_object in data_objects if int(data_object['id']) == int(file.stem)]):
                    with open(file, 'r') as saved_file:
                        name = get_name(json.load(saved_file))
                    log[module]['remove'].append({
                        'name': name,
                        'id': file.stem,
                        'file': file.as_posix()
                    })

        # Save new/changed data
        for data_object in data_objects:
            name = get_name(data_object)
            file_path = module_path.joinpath(str(data_object['id']))

            if Path(file_path).exists():
                with open(file_path, 'r+') as file:
                    old_data = file.read()
                    new_data = json.dumps(clean_data(data_object), indent=4, sort_keys=sort_keys)
                    if old_data != new_data:
                        file.seek(0)
                        file.truncate()
                        file.write(new_data)
                        log[module]['diff'].append({
                            'name': name,
                            'id': data_object['id'],
                            'file': file_path.as_posix()
                        })
            else:
                with open(file_path, 'w') as file:
                    file.write(json.dumps(clean_data(data_object), indent=4, sort_keys=sort_keys))
                    log[module]['add'].append({
                        'name': name,
                        'id': data_object["id"],
                        'file': file_path.as_posix()
                    })

        logging.info('Completed {}'.format(module))
    else:
        logging.error('Failed to retrieve: {}'.format(module))

    return log


def clean_data(json_data):
    """
    Function to clean any data that you do not wish to store or changes on a regular basis
    :param json_data: (dict) json/dict to be parsed
    :return: (dict) cleansed json/dict
    """
    # Remove null entries (placeholders)
    keys = list(json_data.keys())
    for key in keys:
        if json_data[key] is None:
            del json_data[key]

    # Remove system users
    if 'localUserAccounts' in json_data:
        index = 0
        while index < len(json_data['localUserAccounts']):
            if int(json_data['localUserAccounts'][index]['uid']) < 500:
                del json_data['localUserAccounts'][index]
            else:
                del json_data['localUserAccounts'][index]['homeDirectorySizeMb']
                index += 1

        # Sort users by uid
        json_data['localUserAccounts'] = sorted(json_data['localUserAccounts'], key=itemgetter('uid'))

    # Remove user extension attributes
    if 'userAndLocation' in json_data:
        del json_data['userAndLocation']['extensionAttributes']

    # Remove OS extension attributes
    if 'operatingSystem' in json_data:
        del json_data['operatingSystem']['extensionAttributes']
        del json_data['operatingSystem']['softwareUpdateDeviceId']

    return json_data


def get_name(json_data):
    """
    Rules to get the name of the object
    :param (dict) json_data:
    :return: (str) User friendly name
    """

    name = json_data['udid']

    return name
