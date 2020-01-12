#!/usr/bin/env python3

"""
Script:	jamf_change_monitor.py
Date:	2020-01-10
Platform: macOS/Linux
Description:
Call modules to get data to maintain a repo and report on changes
"""
__author__ = 'thedzy'
__copyright__ = 'Copyright 2020, thedzy'
__license__ = 'GPL'
__version__ = '1.0'
__maintainer__ = 'thedzy'
__email__ = 'thedzy@hotmail.com'
__status__ = 'Development'

import importlib
import logging
import optparse
import os
import smtplib
from configparser import ConfigParser
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from git import Repo, InvalidGitRepositoryError

import jamf
from simple_multitasking import *


def main(test_module, config_file):
    start_time = time.time()

    logs = []

    # Paths
    base_path = os.path.dirname(os.path.abspath(__file__))
    modules_path = os.path.join(base_path, 'modules')

    # Initalise a log for the email
    log_ext = 'txt'  # Use txt to view directly in your email client (if supported), use log to be read by a traditional log viewer
    log_file = os.path.join(base_path, '{}.{}'.format(os.path.basename(__file__).split('.')[0], log_ext))
    logging.basicConfig(filename=log_file, format='[%(asctime)s] [%(levelname)-7s] %(message)s', level=logging.INFO)
    logging.info('Starting')

    # Load configuration
    config = load_config(config_file)

    # Set and/or create the git repo
    if config['git']['repo'] is None:
        config['git']['repo'] = os.path.join(base_path, 'data')
        os.makedirs(config['git']['repo'], exist_ok=True)
    else:
        if not os.path.exists(config['git']['repo']):
            if os.makedirs(config['git']['repo'], exist_ok=True):
                logging.error('Repo {} does not exist and cannot be created'.format(config['git']['repo']))
                exit()
        else:
            logging.warning('Specified repo contains files') if os.listdir(config['git']['repo']) else None
    os.chdir(config['git']['repo'])

    try:
        repo = Repo(config['git']['repo'])
    except InvalidGitRepositoryError:
        repo = Repo.init(config['git']['repo'])
    assert not repo.bare
    # Set author and committer
    with repo.config_writer() as repo_config:
        repo_config.set_value('user', 'name', config['git']['name'])
        repo_config.set_value('user', 'email', config['git']['email'])
        repo_config.release()

    # Although this is intended to run on Linux, we will clean any ds_stores to prevent errors on macos
    for root, dirs, files in os.walk(config['git']['repo']):
        for file in files:
            if file.lower() == '.ds_store':
                os.remove(os.path.join(root, file))

    # Initialise a jamf universal api class instance
    api_universal = jamf.JamfUAPI(config['jamf']['url'], config['jamf']['user'], config['jamf']['pass'])
    api_classic = jamf.JamfClassic(config['jamf']['url'], config['jamf']['user'], config['jamf']['pass'])

    # Load all modules into memory
    data_functions = []
    for module in os.listdir(modules_path):
        module_name = os.path.splitext(module)[0]
        if '_' not in module_name:
            data_functions.append(importlib.import_module('modules.{}'.format(module_name)))

    # If we are testing one module
    if test_module is not None:
        logging.debug('Running with only module: {}'.format(test_module))
        if os.path.exists(os.path.join(base_path, 'modules', test_module + '.py')):
            data_functions = [importlib.import_module('modules.{}'.format(test_module))]
        else:
            logging.error('Module {} does not exist'.format(test_module))
            print('Module {} does not exist'.format(test_module))
            exit()

    # Start threads
    threads = []
    for data_function in data_functions:
        threads.append(ThreadFunction(data_function.get, api_classic, api_universal))
        threads[len(threads) - 1].start()

    # Loop through the completed threads
    unhandled_threads = [t for t in threads if not t.is_handled()]
    while len(unhandled_threads) != 0:
        # Loop through processed threads
        for inactive_thread in [a for a in unhandled_threads if not a.isAlive()]:
            # Collect log files
            return_log = inactive_thread.get_value()
            logs.extend(return_log)
        unhandled_threads = [t for t in threads if not t.is_handled()]

    # print end/total time
    runtime = (time.time() - start_time)
    minutes, seconds = divmod(runtime, 60)
    hours, minutes = divmod(minutes, 60)
    logging.info('Total runtime: {0:.0f}:{1:.0f}:{2:.3f}'.format(hours, minutes, seconds))

    exit()
    if repo.is_dirty():
        # Make all git commits
        git_commit(logs, repo)

        # Get git log from start of run
        git_status = repo.git().log('--since={0}'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() - runtime))), '--numstat', '--patch', '--date=local').encode('utf-16', 'replace').decode('utf-16')
        # Do some garbage collection
        git_status += '\n\n-------------------------\nGarbage collection:\n'
        git_status += repo.git.gc('--auto')

        # Send email
        logging.info('Logging into email')
        smtpconn, success = login_email(config['email']['url'], config['email']['port'], config['email']['user'], config['email']['pass'])
        if not success:
            logging.error('Could not initialize a smtp connection')
            logging.error(smtpconn)
        else:
            logging.info('Sending email')
            send_result = send_email(smtpconn, config['message']['name'], config['message']['email'], '{} @ {}'.format(config['message']['subject'], time.ctime()), git_status, log_file)
            if len(send_result) == 0:
                os.remove(log_file)
            else:
                logging.error('Failed to send email to {0}'.format(config['message']['email']))
                logging.info(send_result)
                logging.info('Completed')
                logging.info('-' * 80)
    else:
        logging.info('Repo is clean, no email sent')
        logging.info('-' * 80)


def git_commit(logs, repo):
    """
    Use logs from data pulls to make git add, removes, ans commits
    :param logs: (List)(Tupples) Data pull details
    :param repo: (Repo) Repo
    :return: (Void)
    """
    for log in logs:
        if log[3] == 0:
            if log[0] in repo.untracked_files:
                repo.index.add([log[0]])
                repo.index.commit('Add {}:{}'.format(log[1], log[2]))
                logging.info('Add {}'.format(log[0]))
            elif log[0] in repo.git.diff(None, name_only=True).splitlines():
                repo.index.add([log[0]])
                repo.index.commit('Changed {}:{}'.format(log[1], log[2]))
                logging.info('Changed {}'.format(log[0]))
            continue

        if log[3] == 1:
            repo.index.remove([log[0]])
            repo.index.commit('Removed {}:{}'.format(log[1], log[2]))
            logging.info('Removed {}'.format(log[0]))
            continue

        if log[3] == 3:
            repo.index.add([log[0]])
            repo.index.commit('Init {}:{}'.format(log[1], log[2]))
            logging.info('Init {}'.format(log[0]))
            continue


def login_email(host, port, username=None, userpass=None):
    """
    Establish a SMTP conneciton
    :param host: (str) Hostname
    :param port:  (int) Port number
    :param username: (str) Username
    :param userpass: (str) Password
    :return: Connection or error description
        (bool) If successful
    """
    try:
        smtpconn = smtplib.SMTP(host=host, port=port)
        smtpconn.connect(host, port)
        smtpconn.ehlo()
        smtpconn.starttls()
        if username is None or userpass is None:
            logging.warning('Skipping login to email')
        else:
            smtpconn.login(username, userpass)
    except smtplib.SMTPException as err:
        return err, False

    return smtpconn, True


def send_email(smtpconn, from_name, to_email, subject, message, attachment):
    """
    Send a prepared message with an established SMTP connection
    :param smtpconn: STMP Connection Object
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
        attached_file.add_header('content-disposition', 'attachment', filename=os.path.basename(attachment))
    msg.attach(attached_file)

    # Send
    result = smtpconn.send_message(msg)

    # Destroy message
    del msg

    return result


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
        defaults = {'email': {
            'port': 25,
            'user': None,
            'pass': None
        }, 'message': {
            'subject': 'Jamf_git log'
        }, 'git': {
            'name': __file__,
            'email': 'annoymous',
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
    parser = optparse.OptionParser('%prog [options]\n %prog pulls from the jamf api and commit the files into git.  You can be alerted on the changes, see changes over time and use the data to revert changes made.',
                                   version='%prog 1.0')
    # debug a module
    parser.add_option('-m', '--module',
                      action='store', dest='module_name', default=None,
                      help='Test/run only a specific module')

    # Specify the location of the configuration file
    parser.add_option('-c', '--config',
                      action='store', dest='config_file', default=None,
                      help='Specify an an alternate file for the configuration')

    options, args = parser.parse_args()
    main(options.module_name, options.config_file)
