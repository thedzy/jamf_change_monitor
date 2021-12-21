# Jamf Change Monitor

**__jamf_change_monitor.py__**

## Be notified of changes when they happen and be able to revert

1. Be notified of changes before it's too late
2. Be able to revert changes by re-uploading old configurations
3. Be able to easily go through change history

# How it works:

1. Each module in the modules' folder is run simultaneously
2. Each module downloads data from the API into a git repository
3. Each file is committed and or removed
4. A log of diff changes are emailed
5. (Optionally) Push the changes to a remote repository

## Modules

A module is responsible for acquiring the data from the API and determining if any items have been removed. The files
can be saved in any way as long as the results returned can distinguish removed content and pulled content.

A module only needs to be placed in the modules' folder to be activated and run.

_See:_ [modules_disabled/README.md](modules_disabled/README.md) for more information

## Modules Disabled

### Move modules here that you wish to disable, or keep from running

## Files

### config.ini

Contains the configuration for the accessing the Jamf API, email, etc

Optional keys:

```
[email]
    port
    user
    pass

[message]
    subject

[git]
    name
    email
    repo


```

Example config.ini

```
[jamf]
url = https://www.jamfapi.example.com
user = jamfadmin
pass = password

[email]
url = mail.example.com
port = 587
user = email.username@example.com
pass = emailpassword

[message]
name = From name
email = to_email@example.com
subject = Jamf changes

[git]
name = Git author
email = git.user@example.com
repo = /path/to/repo
```

### config.py

Assist with the creation of the configuration

```
Usage: config.py [options]
 config.py create a configurtation file for jamf_change_monitor

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -c CONFIG_FILE, --config=CONFIG_FILE
```

### continuous.sh

**[ Legacy ]** Script to run the python script in a continuous loop

### jamf.py

Jamf classes to access the api

### macOS_install.py

Assist with the installation of the script on macOS. Move the files to their final location and set up a daemon

### linux_install.py

Assist with the installation of the script on Linux. Move the files to their final location and set up a daemon

### modules_common.py

Functions that will be common across all modules.

### jamf_change_monitor.py

The main program

```
usage:
Pulls from the Jamf api and commit the files into git.
You can be alerted on the changes, see changes over time and use the data to revert changes made.',
 [-h] [-m TEST_MODULE] [--force] [-c CONFIG_FILE]

optional arguments:
  -h, --help            show this help message and exit
  -m TEST_MODULE, --module TEST_MODULE
                        run only a specific module
  --force               Before starting add and commit everything into a clean repo useful for testing a module
  -c CONFIG_FILE, --config CONFIG_FILE
                        specify an an alternate file for the configuration
```

### simple_multitasking.py

Class to handle the multitasking of the modules


##Versions
###1
- Pulls and commit changes found in the repo
###2
- Pulls all the content and compares the contents to reduce unnecessary writes
- Commits the changes based on the logs from the modules
- A lot of rewrites, all the modules we re-done
- Storing the files with just the id