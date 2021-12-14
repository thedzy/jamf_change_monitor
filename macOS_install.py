#!/usr/bin/env python3

"""
Script:	macOS_install.py
Date:	2021-12-11	

Platform: macOS/Windows/Linux

Description:

"""
__author__ = 'thedzy'
__copyright__ = 'Copyright 2021, thedzy'
__license__ = 'GPL'
__version__ = '1.0'
__maintainer__ = 'thedzy'
__email__ = 'thedzy@hotmail.com'
__status__ = 'Development'

__description__ = """
    install and setup daemon on macos
"""

import argparse
import logging
import os
import plistlib
import subprocess
import venv
from pathlib import Path
import shutil
from multiprocessing import Process
import pwd


def main():
    # Initialise a log for the email
    logging.basicConfig(filename=None, format='{asctime} [{levelname:7}] {message}', level=options.debug, style='{')
    logging.info('Start')
    logging.debug('Debug ON')

    # Make sure its run as sudo
    if os.getuid() != 0:
        logging.error('Run as sudo')
        exit()

    # Check that a frequency is chosen
    if not any([options.hourly, options.daily, options.weekly, options.continuous, options.cron]):
        logging.error('Must choose a frequency')
        exit()

    # Check config
    if not Path(options.config_file):
        logging.error(f'No configuration found at {options.config_file}')
        exit()

    # Source and destinations of the files
    source = Path(__file__).parent
    destination = Path(options.location)

    logging.debug(f'{source} -> {destination}')

    # Setup venv in owner of install location
    thread = Process(target=install_venv, args=[source, destination, options.debug])
    thread.start()
    thread.join()
    thread.close()

    # Determine the python to use
    context = destination.joinpath('venv')
    python = context.joinpath('bin', 'python3')

    # Create plist of dict keys
    plist_dict = {
        'Label': 'jamf_change_monitor',
        'LowPriorityIO': True,
        'ProgramArguments':
            [
                python.as_posix(),
                '/usr/local/jamf_change_monitor/jamf_change_monitor.py',
                '--config',
                options.config_file
            ],
        'RunAtLoad': True,
        'StandardErrorPath': destination.joinpath('jamf_change_monitor_err.log').as_posix(),
        'StandardOutPath': destination.joinpath('jamf_change_monitor_out.log').as_posix(),
    }
    logging.debug(' '.join(plist_dict['ProgramArguments']))

    # Append with dict with options
    if options.force:
        plist_dict['ProgramArguments'].append('--force')

    if options.hourly or options.daily:
        options.cron = '0 0 * * *'

    if options.daily:
        options.cron = '0 * * * *'

    if options.weekly:
        options.cron = '0 0 * * 0'

    if options.cron:
        cron = options.cron.split()
        if len(cron) != 5:
            logging.error(f'Invalid cron {cron}')
            exit()

        minutes = split(*cron[0].split(','), max_value=59)
        hours = split(*cron[1].split(','), max_value=23)
        days = split(*cron[2].split(','), max_value=31)
        months = split(*cron[3].split(','), max_value=12)
        weekdays = split(*cron[4].split(','), max_value=6)

        logging.debug(f'Minutes: {minutes}')
        logging.debug(f'Hours: {hours}')
        logging.debug(f'Days: {days}')
        logging.debug(f'Months: {months}')
        logging.debug(f'Weekdays: {weekdays}')

        cron_sets = (
            [[minute, hour, day, month, weekday] for minute in minutes
             for hour in hours
             for day in days
             for month in months
             for weekday in weekdays])

        cron_dicts = []

        logging.debug('Cron sets')
        for cron_set in cron_sets:
            logging.debug(cron_gen(*cron_set))
            cron_dicts.append(cron_gen(*cron_set))

        plist_dict['StartCalendarInterval'] = cron_dicts

    if options.continuous:
        plist_dict['KeepAlive'] = {'SuccessfulExit': True}

    # Create a plist
    logging.info('Installing daemon at /Library/LaunchDaemons/com.thedzy.jamf_change_monitor.plist')
    with open('/Library/LaunchDaemons/com.thedzy.jamf_change_monitor.plist', 'wb') as outfile:
        logging.debug(plistlib.dumps(plist_dict, fmt=plistlib.FMT_XML, sort_keys=True).decode())
        plistlib.dump(plist_dict, outfile, fmt=plistlib.FMT_XML, sort_keys=True)

    # Launch the Daemon
    logging.info('Starting daemon')
    commands = ['/bin/launchctl unload /Library/LaunchDaemons/com.thedzy.jamf_change_monitor.plist',
                '/bin/launchctl load /Library/LaunchDaemons/com.thedzy.jamf_change_monitor.plist', ]

    for command in commands:
        process = subprocess.run(command, shell=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 universal_newlines=True)
        if process.returncode != 0:
            logging.error(process.stderr)


def install_venv(source, destination, debug):
    # Setup logging for new thread
    logging.basicConfig(filename=None, format='{asctime} [{levelname:7}] {message}', level=debug, style='{')

    # Create the install directory if missing
    if not destination.exists():
        destination.mkdir(exist_ok=True, parents=True)
    elif destination.match('*'):
        logging.warning('Destination is not empty')

    logging.debug(f'{source} -> {destination}')

    # Determine the python to use
    context = destination.joinpath('venv')
    python = context.joinpath('bin', 'python3')

    # Get owner uid
    owner = pwd.getpwnam(destination.parent.owner())

    # Change to user permissions to create the venv
    os.setgid(owner.pw_gid)
    os.setuid(owner.pw_uid)

    # Set the home directory
    os.environ['HOME'] = '/var/root'
    logging.debug(f'User: {os.getuid()}')

    # Install a venv
    environment = venv.EnvBuilder(with_pip=True, prompt='jamf_change_monitor')
    environment.create(context)
    environment.post_setup(context)

    # Install requirements
    command = f'{python} -m pip install --upgrade pip'
    process = subprocess.Popen(command, shell=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               universal_newlines=True)

    command = f'{python} -m pip install requests'
    process = subprocess.Popen(command, shell=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               universal_newlines=True)

    if process.returncode != 0:
        logging.warning(process.stdout.read())
        logging.warning(process.stderr.read())

    logging.debug('Using {0}'.format(python))

    # Move the file to its final destination and set the permissions
    logging.info(f'Installing files at {destination}')
    shutil.copytree(source, destination, dirs_exist_ok=True, ignore=shutil.ignore_patterns('*.ini', '*.log', 'data'))
    os.chmod(destination, 0o755)


def split(*args, max_value=100, separator='-', stepper='/'):
    def number(value):
        names = {
            'sunday': 0,
            'monday': 1,
            'tuesday': 2,
            'wednesday': 3,
            'thursday': 4,
            'friday': 5,
            'saturday': 6,

            'january': 1, 'july': 8,
            'february': 2, 'august': 9,
            'march': 3, 'september': 10,
            'april': 4, 'october': 11,
            'may': 5, 'november': 12,
            'june': 6, 'december': 13,

            '*': -1
        }
        try:
            value = int(value) if value.isdigit() else names[value.lower()]
        except KeyError:
            logging.error(f'Invalid name in cron job {arg}')
            exit()

        if value > max_value:
            logging.error(f'Value out of range {value}')
            exit()

        return value

    numbers = []
    for arg in args:
        # If a step is specified
        if stepper in arg:
            indexes = arg.split(stepper)
            arg = indexes[0]
            step = int(indexes[1])
        else:
            step = None

        # If a range separator is found
        if separator in arg:
            indexes = arg.split(separator)
            start = number(indexes[0])
            stop = number(indexes[1])

            step = step if step else 1
            numbers.extend(list(range(start, stop + 1, step)))
        else:
            if step:
                start = number(arg)
                start = 0 if start < 0 else start
                numbers.extend(list(range(start, max_value + 1, step)))
            else:
                numbers.append(number(arg))

    numbers.sort()

    return numbers


def cron_gen(minute, hour, day, month, weekday):
    cron_dict = {}

    try:
        if minute >= 0:
            cron_dict['Minute'] = int(minute)

        if hour >= 0:
            cron_dict['Hour'] = int(hour)

        if day >= 0:
            cron_dict['Day'] = int(day)

        if month >= 0:
            cron_dict['Month'] = int(month)

        if weekday >= 0:
            cron_dict['Weekday'] = int(weekday)

    except ValueError:
        logging.error('Invalid values in cron job')
        exit()

    return cron_dict


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__description__)

    # debug a module
    parser.add_argument('-l', '--location', default='/usr/local/jamf_change_monitor',
                        action='store', dest='location',
                        help='install location\n'
                             'Default: %(default)s')

    parser.add_argument('-f', '--force',
                        action='store_true', dest='force',
                        help='force commits before each run')

    interval = parser.add_mutually_exclusive_group()
    interval.add_argument('--hourly',
                          action='store_true', dest='hourly',
                          help='run monitor each hour')
    interval.add_argument('--daily',
                          action='store_true', dest='daily',
                          help='run monitor each day')
    interval.add_argument('--weekly',
                          action='store_true', dest='weekly',
                          help='run monitor each week')
    interval.add_argument('--cron', default=None,
                          action='store', dest='cron',
                          help='use cron style syntax (no @syntax) '
                               'ex: 0 * * * 1,2,3,4,5,6 = Every hour on weekdays'
                               'ex: 0 7-18 * * monday-friday = Every hour on weekdays during working hours'
                               'ex: */20 * * * * = Every 20 minutes of every days'

                          )
    interval.add_argument('--continuous',
                          action='store_true', dest='continuous',
                          help='run monitor immediately after completing')

    # Specify the location of the configuration file
    parser.add_argument('-c', '--config', default=Path(Path(__file__).parent).joinpath('config.ini'),
                        action='store', dest='config_file',
                        required=True,
                        help='Specify an an alternate file for the configuration')

    parser.add_argument('--debug', const=10, default=20,
                        action='store_const', dest='debug',
                        help=argparse.SUPPRESS)

    options = parser.parse_args()
    main()
