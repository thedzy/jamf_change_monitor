#!/usr/bin/env python3

"""
Script:	repo_repair.py
Date:	2020-01-10
Platform: macOS/Linux
Description:
Restart the repo.  This is intended for local repos.  If using a remote repo, pull the repo again.
"""
__author__ = 'thedzy'
__copyright__ = 'Copyright 2020, thedzy'
__license__ = 'GPL'
__version__ = '1.0'
__maintainer__ = 'thedzy'
__email__ = 'thedzy@hotmail.com'
__status__ = 'Development'

import logging
import optparse
import os

from git import Repo, InvalidGitRepositoryError


def main(config_file, repo_path):
    logging.basicConfig(format='[%(asctime)s] [%(levelname)-7s] %(message)s', level=logging.INFO)
    logging.info('Starting')

    base_path = os.path.dirname(os.path.abspath(__file__))

    if config_file is None:
        config = load_config(os.path.join(base_path, 'config.ini'))
    else:
        config = load_config(config_file)

    # Set and/or create the git repo
    if repo_path is None and config['git']['repo']:
        repo_path = os.path.join(base_path, 'data')
    else:
        if repo_path is None:
            repo_path = config['git']['repo']

    os.chdir(repo_path)

    if os.path.exists(repo_path):
        while True:
            answer = input('Do you wish to remove all git history and restart the repo?\n'
                           'This will keep all existing files and start a new commit history.\n'
                           'This is NOT recommended for remote repos and is intended to simply repairing a local repo.\nContinue (y/n)? ')
            if answer.lower() == 'y':
                accept = True
                break
            elif answer.lower() == 'n':
                accept = False
                break

        if answer == 'y':
            os.chdir(repo_path)

            git_folder = os.path.join(repo_path, '.git')
            print('Removing all git files')
            if os.path.exists(git_folder):
                for root, dirs, files in os.walk(git_folder, topdown=False):
                    for file in files:
                        os.remove(os.path.join(root, file))
                    os.rmdir(root)

            print('Initialising the repo')
            try:
                repo = Repo(repo_path)
            except InvalidGitRepositoryError:
                repo = Repo.init(repo_path)
            assert not repo.bare

            print('Committing all top level files and directories')
            for item in os.listdir(repo_path):
                if not item.startswith('.'):
                    repo.index.add([item])
                    repo.index.commit('Initializing: {}'.format(item))

            if repo.is_dirty():
                print('Something went wrong')
            else:
                print('Repo is clean')
        else:
            print('Exiting')
    else:
        print('Repo does not exist')


def load_config(config_file):
    """
    Load the configuration file into memory and fill in defaults
    :param config_file: (str) path to configuration file
    :return: (dict) settings
    """

    base_path = os.path.dirname(os.path.abspath(__file__))

    config = ConfigParser(allow_no_value=True)
    if config_file is None:
        config_file = os.path.join(base_path, 'config.ini')
    if os.path.isfile(config_file):
        defaults = {'git': {
            'repo': None
        }}
        config.read_dict(defaults)
        config.read(config_file)
    else:
        print('Please run config.py to create {}'.format(config_file))
        exit()

    # Replace blank records with None
    config = {section: dict(config.items(section)) for section in config.sections()}
    for key in config:
        for sub_key in config[key]:
            if len(config[key][sub_key].strip(' ')) == 0:
                config[key][sub_key] = None
    return config


if __name__ == '__main__':
    parser = optparse.OptionParser('%prog [options]\n %prog Removed the git information in a directory, recreates it as a git repo and commits the files in it.',
                                   version='%prog 1.0')

    # Specify the location of the configuration file
    parser.add_option('-c', '--config',
                      action='store', dest='config_file', default=None,
                      help='Specify an an alternate file for the configuration')
    # Specify a repo
    parser.add_option('-r', '--repo',
                      action='store', dest='repo_path', default=None,
                      help='Specify an existing repo or alternate location')

    options, args = parser.parse_args()
    main(options.config_file, options.repo_path)

