## Move modules here that you wish to disable, or keep from running

A module is responsible for acquiring the data from the API and determining if any items have been removed.  The files can be saved in anyway as long as the results returned can distinguish removed content and pulled content.

**Requirements:**
------
### def get(api_classic=None, api_universal=None):
This is the default function of the module and what will be called when it is run. \
It recieves a referesnce to a class for the classic API and a class for the universal API 
The module must return an array/list of tupples. Each tupple defines the file that was added change or deleted \
The tupple contains:
1. File name of the file: 
2. The user friendly name of the module
3. The user friendly name of the item
4. Integer for what has done with the file.
    1. 0: File was added
    2. 1: File was deleted
    3. 2: Parent directory/folder was created
    
  Example array/list:
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
1.json will be added and the report will show 'Created: LDAP Sservers: tor.example.com' as the file is  showing Untracked\
2.json will be added and the report will show 'Changed: LDAP Sservers: tor.example.com' as the file is unstaged \
3.json will be removed and the report will show 'Removed: LDAP Sservers: win.example.com' as the file is marked as deleted
