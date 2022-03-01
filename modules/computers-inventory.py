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
import pprint

import modules_common

"""
WARNING:
This module can be very noisy.  Use with caution and configure what data you with track.
Consider limiting sections or applying heavy cleaning to the data

With each Jamf version more (or less) data in the api tends to jitter (flip-flop).  After each upgrade you 
will need to remove the items and reevaluate some times.   Items that flip flop I marked as Jitter

To jamf: If you are reading this, consistency in reporting is appreciated and should be a requirement 
"""


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
    remainder, page, size = True, 0, 100
    while remainder:
        """ Available sections
            Too many sections impacts performance and makes reports noisy
            APPLICATIONS                   LICENSED_SOFTWARE
            ATTACHMENTS                    LOCAL_USER_ACCOUNTS
            CERTIFICATES                   OPERATING_SYSTEM
            CONFIGURATION_PROFILES         PACKAGE_RECEIPTS
            CONTENT_CACHING                PLUGINS
            DISK_ENCRYPTION                PRINTERS
            EXTENSION_ATTRIBUTES           PURCHASING
            FONTS                          SECURITY
            GENERAL                        SERVICES
            GROUP_MEMBERSHIPS              SOFTWARE_UPDATES
            HARDWARE                       STORAGE
            IBEACONS                       USER_AND_LOCATION    
        """
        query_sections = [
            'GENERAL',
            'USER_AND_LOCATION',
            'LOCAL_USER_ACCOUNTS',
            'OPERATING_SYSTEM',
            'DISK_ENCRYPTION',
            'SECURITY',
        ]
        api_query = api_universal.get_data('v1', 'computers-inventory', section=query_sections, page=page, size=size,
                                           sort='id:desc')
        logging.debug(f'Query {api_query.data}')
        remainder = ((page + 1) * size) < api_query.data['totalCount']
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

    # APPLICATIONS
    if 'applications' in json_data:
        for application in json_data['applications']:
            del application['name']
            del application['path']
            del application['macAppStore']
            del application['sizeMegabytes']
            del application['updateAvailable']
            del application['externalVersionId']

    # CERTIFICATES
    if 'certificates' in json_data:
        index = 0
        while index < len(json_data['certificates']):
            del json_data['certificates'][index]['expirationDate']
            index += 1

    # CONFIGURATION_PROFILES
    if 'configurationProfiles' in json_data:
        for configuration_profile in json_data['configurationProfiles']:
            del configuration_profile['id']
            del configuration_profile['username']
            del configuration_profile['lastInstalled']
            del configuration_profile['profileIdentifier']

    # CONTENT_CACHING
    if 'contentCaching' in json_data:
        keeps = ('activated', 'active', 'cacheStatus', 'port', 'publicAddress')
        keys = [item for item in json_data['contentCaching']]
        for key in keys:
            if key not in keeps:
                del json_data['contentCaching'][key]

    # DISK_ENCRYPTION
    if 'diskEncryption' in json_data:
        del json_data['diskEncryption']['bootPartitionEncryptionDetails']['partitionFileVault2Percent']
        del json_data['diskEncryption']['individualRecoveryKeyValidityStatus']  # Jitters

    # GENERAL
    if 'general' in json_data:
        del json_data['general']['lastIpAddress']
        del json_data['general']['lastReportedIp']
        del json_data['general']['jamfBinaryVersion']
        del json_data['general']['reportDate']
        del json_data['general']['lastContactTime']
        del json_data['general']['lastEnrolledDate']
        del json_data['general']['mdmProfileExpiration']
        del json_data['general']['initialEntryDate']
        del json_data['general']['site']
        del json_data['general']['extensionAttributes']
        del json_data['general']['lastCloudBackupDate']

    # HARDWARE
    if 'hardware' in json_data:
        del json_data['hardware']['extensionAttributes']
        del json_data['hardware']['batteryCapacityPercent']
        del json_data['hardware']['smcVersion']
        del json_data['hardware']['bootRom']

    # LOCAL_USER_ACCOUNTS
    if 'localUserAccounts' in json_data:
        index = 0
        # Remove system users
        while index < len(json_data['localUserAccounts']):
            if int(json_data['localUserAccounts'][index]['uid']) < 500:
                del json_data['localUserAccounts'][index]
            else:
                # Remove user directory sizes
                del json_data['localUserAccounts'][index]['homeDirectorySizeMb']
                # Remove user type, Jamf tends to flip flop on these values
                del json_data['localUserAccounts'][index]['userAccountType']  # Jitters
                index += 1

        # Sort users by uid
        json_data['localUserAccounts'] = sorted(json_data['localUserAccounts'], key=itemgetter('uid'))

    # OPERATING_SYSTEM
    if 'operatingSystem' in json_data:
        del json_data['operatingSystem']['extensionAttributes']
        del json_data['operatingSystem']['softwareUpdateDeviceId']
        del json_data['operatingSystem']['fileVault2Status']  # Jitters

        # Use version 1 for Major, 2 for Minor and 3 for all (or uncomment)
        version = json_data['operatingSystem']['version'].split('.')
        json_data['operatingSystem']['version'] = '.'.join(version[:1])
        del json_data['operatingSystem']['build']

    # PURCHASING
    if 'purchasing' in json_data:
        del json_data['purchasing']['extensionAttributes']

    # SECURITY
    if 'security' in json_data:
        del json_data['security']['xprotectVersion']

    # SERVICES
    if 'services' in json_data:
        pass

    # STORAGE
    if 'storage' in json_data:
        del json_data['storage']['bootDriveAvailableSpaceMegabytes']

        index = 0
        while index < len(json_data['storage']['disks']):
            del json_data['storage']['disks'][index]['id']
            del json_data['storage']['disks'][index]['revision']
            del json_data['storage']['disks'][index]['partitions']
            index += 1

    # USER_AND_LOCATION
    if 'userAndLocation' in json_data:
        del json_data['userAndLocation']['extensionAttributes']

    return json_data


def get_name(json_data):
    """
    Rules to get the name of the object
    :param (dict) json_data:
    :return: (str) User friendly name
    """

    try:
        name = json_data['userAndLocation']['email']
    except KeyError:
        name = json_data['udid']

    return name
