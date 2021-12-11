#!/usr/bin/env python3

"""
Script:	config.py
Date:	2020-01-10
Platform: macOS/Linux
Description:
Create a configuration file for jamf_change_monitor
"""
__author__ = 'thedzy'
__copyright__ = 'Copyright 2020, thedzy'
__license__ = 'GPL'
__version__ = '1.0'
__maintainer__ = 'thedzy'
__email__ = 'thedzy@hotmail.com'
__status__ = 'Development'

__description__ = """
create a configurtation file for jamf_change_monitor
"""

import argparse
from configparser import ConfigParser
from pathlib import Path


def main():
    file_path = Path(__file__)
    base_path = file_path.parent

    # Create configuration
    config = ConfigParser()
    config_file = options.config_file if options.config_file else base_path.joinpath('config.ini')

    if Path(config_file).exists():
        config.read(config_file)
    else:
        # Set defaults
        config['jamf'] = {
            'url': 'http://www.example.com',
            'user': 'api_username',
            'pass': 'api_password'
        }
        config['email'] = {
            'url': 'mail.example.com',
            'port': 25,
            'user': 'email_username',
            'pass': 'email_password'
        }
        config['message'] = {
            'name': 'User friendly from name',
            'email': 'jamf@example.com',
            'subject': 'Jamf Changes'
        }
        config['git'] = {
            'name': 'Author B. Public',
            'email': 'author@example.com',
            'path': '',
        }

    # Section, key, Prompt, Optional
    prompts = [
        ('jamf', 'url', 'URL to Jamf API', False,),
        ('jamf', 'user', 'Username to the Jamf API', False,),
        ('jamf', 'pass', 'Password to the Jamf API', False,),

        ('email', 'url', 'URL to the SMTP server', False,),
        ('email', 'port', 'Port for SMTP server', True,),
        ('email', 'user', 'Username to the SMTP server', True,),
        ('email', 'pass', 'Password to the SMTP server', True,),

        ('message', 'name', 'User friendly from name', False,),
        ('message', 'email', 'Email to address', False,),
        ('message', 'subject', 'Email subject line', True,),

        ('git', 'name', 'Git author name', True,),
        ('git', 'email', 'Git author email address', True),
        ('git', 'path', 'Git repo path', True),
    ]

    while True:
        greeting = 'Please answer the following questions to create your configuration'
        print('=' * len(greeting))
        print(greeting)
        print('=' * len(greeting))

        for prompt in prompts:
            return_value = get_option(prompt[0], prompt[1], prompt[2], config, prompt[3])
            if return_value is not None:
                config[prompt[0]][prompt[1]] = return_value

        if verify_answers(config):
            break

    with open(config_file, 'w') as loaded_file:
        config.write(loaded_file)


def get_option(section, key, prompt, config, optional=False):
    """
    Get the value for the value for the key
    :param section: (str) Config section
    :param key: (str) Section key
    :param prompt: (str) Prompt/Question
    :param config: (ConfigParser) Configuration
    :param optional: (Bool) Optional?
    :return: (String/None) Value
    """
    if optional:
        print('Optional:')
    try:
        current_value = config[section][key]
        answer = input('{0} ({1})? '.format(prompt, current_value))
    except KeyError:
        current_value = ''
        answer = input('{0}? '.format(prompt))

    if len(answer) == 0 and not optional:
        return current_value
    elif len(answer) == 0 and optional:
        config.remove_option(section, key)
        if len(current_value) == 0:
            return None
        else:
            if input('\tRemove? (y)? ').lower() == 'y':
                return None
            else:
                return current_value

    return answer


def verify_answers(config):
    """
    Prompt user to verify the options selected
    :param config: (ConfigParser) Configuration
    :return: (Bool) Accepted
    """
    greeting = 'Proposed Configuration'
    print('=' * len(greeting))
    print(greeting)
    print('=' * len(greeting))

    for section in config.sections():
        print('[{}]'.format(section))
        for key in config[section]:
            print('\t{0} = {1}'.format(key, config[section][key]))

    while True:
        answer = input('Continue with these settings (y/n/exit)? ')
        if answer.lower() == 'y':
            accept = True
            break
        elif answer.lower() == 'n':
            accept = False
            break
        elif answer.lower() == 'exit' or answer.lower() == 'e':
            exit()

    return accept


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__description__)

    # Specify the location of the configuration file
    parser.add_argument('-c', '--config', default=None,
                        action='store', dest='config_file',
                        help='Specify an an alternate file for the configuration')

    options = parser.parse_args()
    main()
