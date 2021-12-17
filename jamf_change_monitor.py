#!/usr/bin/env python3

"""
Script:	jamf_change_monitor.py
Date:	2021-01-08
Platform: macOS/Linux
Description:
Call modules to get data to maintain a repo and report on changes
"""
__author__ = 'thedzy'
__copyright__ = 'Copyright 2020, thedzy'
__license__ = 'GPL'
__version__ = '2.0'
__maintainer__ = 'thedzy'
__email__ = 'thedzy@hotmail.com'
__status__ = 'Development'

__description__ = """
pulls from the Jamf api and commit the files into git.  
You can be alerted on the changes, see changes over time and use the data to revert changes made.',
"""

import argparse
import importlib
import logging
import pprint
import smtplib
import subprocess
import re
from configparser import ConfigParser
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import jamf
from simple_multitasking import *


class Repo:
    def __init__(self, repo_path, __binary='/usr/bin/git'):
        """
        Initialise
        :param repo_path: (str) Path to repo
        :param bin: (str) Path to binary
        """
        self.__binary = __binary
        self.__repo_path = Path(repo_path)

        if not self.__repo_path.is_dir():
            self.__repo_path.mkdir()

        if not self.__repo_path.joinpath('.git').is_dir():
            self.init()

    def __del__(self):
        pass

    def init(self):
        """
        Initialise the repo
        :return: (bool) Success
        """
        command = f'{self.__binary} init {self.__repo_path}'
        process = self.__process(command)

        return True if process.returncode == 0 else False

    def config(self, **kwargs):
        """
        Configure git
        :param kwargs: (dict) Keywords for argument and value
        :return: (bool) Success
        """
        return_values = []
        for kwarg in kwargs:
            command = f'{self.__binary} config --local {kwarg.replace("_", ".")} {kwargs[kwarg]}'
            process = self.__process(command)
            return_values.append((process.stdout, process.stderr))

        return return_values

    def add(self, *args):
        """
        Add files to git
        :param args: (str) File paths
        :return: (bool) Success
        """
        command = f'{self.__binary} add {" ".join(args)}'
        process = self.__process(command)

        return True if process.returncode == 0 else False

    def remove(self, *args):
        """
        Remove files from git
        :param args: (str) File paths
        :return: (bool) Success
        """
        command = f'{self.__binary} rm {" ".join(args)}'
        process = self.__process(command)

        return True if process.returncode == 0 else False

    def commit(self, message):
        """
        Commit changes
        :param message: (str) Commit message
        """
        command = f'{self.__binary} commit -m "{message}"'
        process = self.__process(command)

        return True if process.returncode == 0 else False

    def push(self, force=False):
        """
        Push commits
        :param force: (bool) Force
        """
        command = f'{self.__binary} push {"--force" if force else ""}'
        process = self.__process(command)

        return True if process.returncode == 0 else False

    def log(self, *args):
        """
        Return a log
        :param args: (str) Arguments
        :return: (str) Log
        """
        command = f'{self.__binary} log {" ".join(args)}'
        process = self.__process(command)

        return process.stdout

    def __process(self, command):
        """
        Process a command
        :param command: (str) Command and parameters
        :return: (CompletedProcess) Process
        """
        logging.debug(f'Git command: {command}')
        process = subprocess.run(command,
                                 cwd=self.__repo_path.as_posix(),
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 shell=True, universal_newlines=True)

        logging.debug(f'stdout {process.stdout}')
        logging.debug(f'stderr {process.stderr}')

        return process


def main():
    start_time = time.time()

    # Paths
    file_path = Path(__file__)
    base_path = file_path.parent
    modules_path = base_path.joinpath(base_path, 'modules')

    # Initialise a log for the email
    log_ext = '.txt'
    log_file = Path(base_path).joinpath(file_path.stem).with_suffix(log_ext) if options.debug > 10 else None
    logging.basicConfig(filename=log_file, format='{asctime} [{levelname:7}] {message}', level=options.debug, style='{')

    # Ensure a log file exists even if blank for the attachment
    if log_file is None:
        log_file = Path('/tmp/no_log_file.txt')
        log_file.write_text('In debug mode')

    logging.info('Starting')
    logging.debug('Debug Started')

    # Track changed made by the modules
    logs = {}

    # Load configuration
    config = load_config(Path(options.config_file))
    logging.debug(f'Loaded config\n{config}')

    # Set and/or create the git repo
    repo_path = Path(base_path).joinpath('data') if config['git']['repo'] is None else Path(config['git']['repo'])

    # Ensure repo exists
    if not repo_path.exists():
        first_run = True
        logging.info(f'Creating repo at {repo_path}')
        if repo_path.mkdir(exist_ok=True):
            logging.error(f'Repo {repo_path.as_posix()} does not exist and cannot be created')
            exit()
    else:
        first_run = False
        logging.warning('Specified repo contains files') if repo_path.match('*') else None

    # Make/Set dir as repo
    repo = Repo(repo_path)

    # Set repo configuration
    repo.config(user_email=config['git']['email'], user_name=config['git']['name'])

    # Untracked problem files
    untracked_files = ['**/.DS_store\n', 'config.ini\n']
    if repo_path.joinpath('.gitignore').is_file():
        with open(repo_path.joinpath('.gitignore'), 'r') as gitignore:
            current_ignore = gitignore.readlines()
            logging.debug(f'Starting gitignore {current_ignore}')
    else:
        current_ignore = []

    with open(repo_path.joinpath('.gitignore'), 'w+') as gitignore:
        new_gitignore = [value for value in untracked_files if value not in current_ignore] + current_ignore
        gitignore.writelines(new_gitignore)

    if len(current_ignore) != len(new_gitignore):
        logging.debug(f'Final gitignore {new_gitignore}')
        logging.info('Updating .gitignore')
        repo.add(repo_path.joinpath('.gitignore').as_posix())
        repo.commit('Updated gitignore')

    # Clean up untracked files and commit all uncommitted changes
    if options.force:
        logging.info('Forcing cleanup')
        repo.add('.')
        repo.commit('Forced cleanup')

    # Initialise a Jamf universal api class instance
    api_universal = jamf.JamfUAPI(config['jamf']['url'], config['jamf']['user'], config['jamf']['pass'])
    api_classic = jamf.JamfClassic(config['jamf']['url'], config['jamf']['user'], config['jamf']['pass'])

    # Load all modules into memory
    data_functions = []
    for module in modules_path.glob('*.py'):
        if re.match(r'^[^._]+', module.stem):
            data_functions.append(importlib.import_module(f'modules.{module.stem}'))

    # If we are testing one module
    if options.test_module is not None:
        test_module = Path(options.test_module)
        logging.debug(f'Running with only module: {test_module}')
        if Path(base_path).joinpath(f'modules', f'{test_module}.py').exists():
            data_functions = [importlib.import_module(f'modules.{test_module}')]
        else:
            logging.error(f'Module {test_module} does not exist')
            print(f'Module {test_module} does not exist')
            exit()

    # Start threads
    threads = []
    for data_function in data_functions:
        threads.append(ThreadFunction(data_function.get, api_classic, api_universal, repo_path))
        threads[len(threads) - 1].start()

    # Loop through the completed threads
    unhandled_threads = [t for t in threads if not t.is_handled()]
    while len(unhandled_threads) != 0:
        # Loop through processed threads
        for inactive_thread in [a for a in unhandled_threads if not a.is_alive()]:
            # Collect log files
            return_log = inactive_thread.get_value()
            logs.update(return_log)
        unhandled_threads = [t for t in threads if not t.is_handled()]

    # If we are testing one display the output for verification
    if options.test_module:
        logging.info(f'Module log for testing {test_module}:')
        logging.info(pprint.pformat(logs))

    # Print end/total time
    runtime = (time.time() - start_time)
    minutes, seconds = divmod(runtime, 60)
    hours, minutes = divmod(minutes, 60)
    logging.info(f'Total runtime for all modules: {hours:.0f}:{minutes:.0f}:{seconds:.3f}')

    # Commit the changes
    logging.info('Starting git commits')

    # Make all git commits
    for module in logs:
        logging.info(f'Processing new files in {module}')
        for add in logs[module]['add']:
            logging.info(f'\tAdding "{add["name"]}": {add["file"]}')
            repo.add(add['file'])
            repo.commit(f'Created {add["id"]}:{add["name"]}')

    for module in logs:
        logging.info(f'Processing changes in {module}')
        for diff in logs[module]['diff']:
            logging.info(f'\tChanging "{diff["name"]}": {diff["file"]}')
            repo.add(diff['file'])
            repo.commit(f'Changed {diff["id"]}:{diff["name"]}')

    for module in logs:
        logging.info(f'Processing removals {module}')
        for remove in logs[module]['remove']:
            logging.info(f'\tRemoving "{remove["name"]}": {remove["file"]}')
            if repo.remove(remove['file']):
                repo.commit(f'Removed {remove["id"]}:{remove["name"]}')
            else:
                Path(remove['file']).unlink()

    # Push commits
    if repo.push():
        logging.info('Pushed')
    else:
        logging.warning('Push Failed')

    logging.info('Completed git commits')

    # Get git log from start of run
    if first_run:
        git_status = f'First run\n'
        for module in logs:
            git_status += f'Processed {module}\n'
    else:
        git_status = repo.log(f'--since="{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time))}"',
                              '--numstat',
                              '--patch',
                              '--date=local')

    # If there is a change send it
    if len(git_status) > 0:
        try:
            # Send email
            logging.info('Logging into email')
            logging.debug(f'Server: {config["email"]["url"]}')
            logging.debug(f'Port  : {config["email"]["port"]}')
            logging.debug(f'User  : {config["email"]["user"]}')
            smtp_conn, success = login_email(config['email']['url'],
                                             config['email']['port'],
                                             config['email']['user'],
                                             config['email']['pass'])
            if not success:
                logging.error('Could not initialize a smtp connection')
                logging.error(smtp_conn)
            else:
                logging.info('Sending email')
                send_result = send_email(smtp_conn,
                                         config['message']['name'],
                                         config['message']['email'],
                                         f'{config["message"]["subject"]} @ {time.ctime()}',
                                         git_status,
                                         log_file.as_posix())

                if len(send_result) == 0:
                    logging.debug(f'Cleaning up file {log_file}')
                    log_file.unlink()
                else:
                    logging.error(f'Failed to send email to {config["message"]["email"]}')
                    logging.info(send_result)
                    logging.info('Completed')
                    logging.info('-' * 80)

                logging.info('-' * 80)
        except Exception as err:
            # If all fails, print results to the screen
            logging.debug(f'Failed to send, reason: {err}')
            print(git_status)
    else:
        print(git_status)


def login_email(host, port, username=None, password=None):
    """
    Establish a SMTP connection
    :param host: (str) Hostname
    :param port:  (int) Port number
    :param username: (str) Username
    :param password: (str) Password
    :return: (bool) True if successful
    """
    try:
        smtp_conn = smtplib.SMTP(host=host, port=port)
        smtp_conn.connect(host, port)
        smtp_conn.ehlo()
        smtp_conn.starttls()
        if username is None or password is None:
            logging.warning('Skipping login to email')
        else:
            smtp_conn.login(username, password)
    except smtplib.SMTPException as err:
        return err, False

    return smtp_conn, True


def send_email(smtp_conn, from_name, to_email, subject, message, attachment):
    """
    Send a prepared message with an established SMTP connection
    :param smtp_conn: STMP Connection Object
    :param from_name: (Sting) Name
    :param to_email: (str) Email
    :param subject: (str) Subject
    :param message: (str) Message
    :param attachment: (str) filepath
    :return: Results of the message send
    """

    # Initialise the message
    msg = MIMEMultipart()

    # Setup the parameters of the message
    msg['From'] = from_name
    msg['To'] = to_email
    msg['Subject'] = subject

    # Add in the message body
    msg.attach(MIMEText(message, 'plain'))

    # Attach file
    with open(attachment, 'rb') as file:
        ext = attachment.split('.')[-1:]
        attached_file = MIMEApplication(file.read(), _subtype=ext)
        attached_file.add_header('content-disposition', 'attachment', filename=Path(attachment).name)
    msg.attach(attached_file)

    # Send
    result = smtp_conn.send_message(msg)

    # Destroy message
    del msg

    return result


def load_config(config_file):
    """
    Load the configuration file into memory and fill in defaults
    :param config_file: (str) path to configuration file
    :return: (dict) settings
    """

    config = ConfigParser(allow_no_value=True)

    try:
        if config_file.is_file():
            defaults = {
                'email': {
                    'port': 25,
                    'user': None,
                    'pass': None
                }, 'message': {
                    'subject': 'Jamf_git log'
                }, 'git': {
                    'name': __file__,
                    'email': 'anonymous',
                    'repo': None
                }
            }
            config.read_dict(defaults)
            config.read(config_file.as_posix())
        else:
            print(f'Please run config.py to create {config_file}')
            exit()
    except Exception as err:
        logging.error(err)

    # Replace blank records with None
    config = {section: dict(config.items(section)) for section in config.sections()}
    for key in config:
        for sub_key in config[key]:
            if len(config[key][sub_key].strip()) == 0:
                config[key][sub_key] = None
    return config


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__description__)
    # debug a module
    parser.add_argument('-m', '--module', default=None,
                        action='store', dest='test_module',
                        help='Test/run only a specific module')

    # Force git cleanup
    parser.add_argument('--force',
                        action='store_true', dest='force',
                        help='Before starting add and commit everything into a clean repo\n'
                             'Useful for testing a module')

    # Specify the location of the configuration file
    parser.add_argument('-c', '--config', default=Path(Path(__file__).parent).joinpath('config.ini'),
                        action='store', dest='config_file',
                        help='Specify an an alternate file for the configuration')

    parser.add_argument('--debug', const=10, default=20,
                        action='store_const', dest='debug',
                        help=argparse.SUPPRESS)

    options = parser.parse_args()
    main()
