#!/usr/bin/env python3

"""
Script:	macOS_install.py
Date:	2021-12-11	

Platform: Linux

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
    install and setup daemon on linux
"""

import argparse
import logging
import os
import subprocess
import venv
from pathlib import Path
import shutil
from multiprocessing import Process
import pwd
from configparser import RawConfigParser


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
    if not any([options.hourly, options.daily, options.weekly, options.continuous, options.oncalendar]):
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

    # Append with dict with options
    force = ' --force' if options.force else ''

    # Create configuration
    config = RawConfigParser()
    config.optionxform = lambda option: option
    # Create plist of dict keys
    config.read_dict({
        'Unit': {
            'Description': 'Jamf Change Monitor',
            'After': 'network.target',
            'Wants': 'network-online.target'
        },
        'Service': {
            'Type': 'onshot',
            'User': 'root',
            'ExecStart': f'{python} {destination} --config {options.config_file} {force}',
        },
        'Install': {

        }
    })
    logging.debug(' '.join(config['Service']['ExecStart']))

    if options.continuous:
        config['Service']['Type'] = 'simple'
        config['Service']['Restart'] = 'always'

    with open('/etc/systemd/system/jamf_change_monitor.service', 'w+') as service_file:
        config.write(service_file)

    # Create timer
    timer = RawConfigParser()
    timer.optionxform = lambda option: option
    if options.hourly:
        oncalendar = 'weekly'

    if options.daily:
        oncalendar = 'daily'

    if options.weekly:
        oncalendar = 'weekly'

    if options.oncalendar:
        oncalendar = options.oncalendar

    if not options.continuous:
        timer.read_dict({
            'Unit': {
                'Description': 'Jamf Change Monitor Timer',
            },
            'Service': {
                'OnCalendar': oncalendar,
                'Persistent': True
            },
            'Install': {
                'WantedBy': 'jamf_change_monitor.service'
            }
        })
        with open('/etc/systemd/system/jamf_change_monitor.timer', 'w+') as timer_file:
            timer.write(timer_file)

        logging.info('Installing Timer at /etc/systemd/system/jamf_change_monitor.timer')
    logging.info('Installing Service at /etc/systemd/system/jamf_change_monitor.service')

    # Launch the Service
    logging.info('Starting daemon')
    commands = ['/bin/systemctl daemon-reload',
                '/bin/systemctl restart jamf_change_monitor', ]

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


if __name__ == '__main__':
    def parser_formatter(format_class, **kwargs):
        """
        Use a raw parser to use line breaks, etc
        :param format_class: (class) formatting class
        :param kwargs: (dict) kwargs for class
        :return: (class) formatting class
        """
        try:
            return lambda prog: format_class(prog, **kwargs)
        except TypeError:
            return format_class


    parser = argparse.ArgumentParser(__description__,
                                     formatter_class=parser_formatter(
                                         argparse.RawTextHelpFormatter,
                                         indent_increment=4, max_help_position=12, width=160))

    # debug a module
    parser.add_argument('-l', '--location', default='/usr/local/jamf_change_monitor',
                        action='store', dest='location',
                        help='install location\n'
                             'default: %(default)s')

    parser.add_argument('-f', '--force',
                        action='store_true', dest='force',
                        help='force commits before each run')

    interval = parser.add_mutually_exclusive_group()
    interval.add_argument('--hourly',
                          action='store_true', dest='hourly',
                          help='run monitor once each hour')
    interval.add_argument('--daily',
                          action='store_true', dest='daily',
                          help='run monitor once each day')
    interval.add_argument('--weekly',
                          action='store_true', dest='weekly',
                          help='run monitor once each week')
    interval.add_argument('--oncalendar', default=None,
                          action='store', dest='oncalendar',
                          help='use on calendar format (no sytax checking)')
    interval.add_argument('--continuous', default=None,
                          action='store_true', dest='continuous',
                          help='runs monitor immediately after completing')

    # Specify the location of the configuration file
    parser.add_argument('-c', '--config', default=Path(Path(__file__).parent).joinpath('config.ini'),
                        action='store', dest='config_file',
                        required=True,
                        help='specify the permanent file location for the configuration\n'
                             'the file will not be moved')

    parser.add_argument('--debug', const=10, default=20,
                        action='store_const', dest='debug',
                        help=argparse.SUPPRESS)

    options = parser.parse_args()
    main()
