# Jamf Change Monitor
**__jamf_change_monitor.py__**

## Be notified of changes when they happen and be able to revert
1. Be notified of changes before it's too late
2. Be able to revert changes buy re-uploading old configurations
3. Be able to easily go through change history
4. Be able to search through Jamf content in more detail including history

# How it works:
1. Each module in the modules folder is run simultaneously
2. Each module downloads data from the API into a git repository
3. Each file is committed and or removed
4. A log of diif changes are emailed





## Modules
A module is responsible for acquiring the data from the API and determining if any items have been removed.  The files can be saved in anyway as long as the results returned can distinguish removed content and pulled content.

A module only needs to be placed in the modules folder to be activated and run.

### Requirements:
#### def get(api_classic=None, api_universal=None):
This is the default function of the module and what will be called when it is run. \
It recieves two classes. One for the classic API and one for the universal API 
The module must return an array/list of tupples. Each tupple defines the file that was added change or deleted \
The tupple contains:
1. File name of the file: 
2. The user friendly name of the module
3. The user friendly name of the item
4. Integer for what has done with the file.
    1. 0: File was added
    2. 1: File was deleted
    3. 2: Parent directory/folder was created
    
  Example list:
  ```
  [
   (ldapservers, LDAP Sservers, init, 0,),
   (ldapservers/1.json, LDAP Sservers, tor.example.com, 0,),
   (ldapservers/2.json, LDAP Sservers, tor.example.com, 0,),
   (ldapservers/3.json, LDAP Sservers, win.example.com, 1,)
  ]
```
The git commit function will add directory and remove deleted contents.  Data that was pulled will be checked against the untracked file and changes.
In this, ldapservers folder will be added and it's contents \

In this example: \
1. 1.json will be added and the report will show 'Created: LDAP Sservers: tor.example.com' as the file is  showing Untracked\
2. 2.json will be added and the report will show 'Changed: LDAP Sservers: tor.example.com' as the file is unstaged \
3. 3.json will be removed and the report will show 'Removed: LDAP Sservers: win.example.com' as the file is marked as deleted

## Modules Disbaled
### Move modules here that you wish to disable, or keep from running


## Files
### config.ini
Contains the configuration for the accessing the Jamf API, email, etc

All keys:
```
[jamf]
    url (required)
    user (required)
    pass (required)

[email]
    url (required)
    port (optional)
    user (optional)
    pass (optional)

[message]
    name (required)
    email (required)
    subject (optional)

[git]
    name (optional)
    email (optional)
    repo (optional)


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
Script to run the python script in a continuous loop

### jamf.py
Jamf classes to access the api

### modules_common.py
Functions that the will be common across all modules.

### repo_repair.py
Will remove the git history and restart the repo with only the current data

### jamf_change_monitor.py
The main program
```
Usage: jamf_change_monitor.py [options]
 jamf_change_monitor.py pulls from the jamf api and commit the files into git.  You can be alerted on the changes, see changes over time and use the data to revert changes made.

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -m MODULE_NAME, --module=MODULE_NAME
                        Test/run only a specific module
  -c CONFIG_FILE, --config=CONFIG_FILE
                        Specify an an alternate file for the configuration
```

### simple_multitasking.py
Class to handle the multitasking of the modules
