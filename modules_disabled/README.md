## Move modules here that you wish to disable, or keep from running

A module is responsible for acquiring the data from the API and determining if any items have been removed. The files
can be saved in any way as long as the results returned are contained in a dictionary.

Requirements:
------

### _def get(api_classic=None, api_universal=None)_:

This is the default function of the module and what will be called when it is run. \
It receives a reference to a class for the classic API and a class for the universal API \ 
The module must return a dictionary. The dictionary contains 1 key which is the name of the module \
and in it 3 keys, add, diff, remove.  Each is a list of dictionaries containing 3 keys: name, id, file.  

| Key | Description |
|-----|-------|
| name | is the human-readable name |
| id | is the identifier of the item |
| file | is the full path to teh file |

Example dictionary:

  ```
    {
        'ebooks': {
            'diff': [
               {
                  'name': 'Book of differences',
                  'id': 3,
                  'file': '/var/jamf_data/ebooks/3'
               }
            ],
            'add': [
               {
                  'name': 'My book',
                  'id': 33,
                  'file': '/var/jamf_data/ebooks/33'
               }
            ],
            'remove': [
               {
                  'name': 'Bad book',
                  'id': 8,
                  'file': '/var/jamf_data/ebooks/08'
               }
            ]
        }
    }
```

The jamf_change_montor will use this to commit the changes, additions and removals

Recommendations:
------

### _clean_data(json_data)_:

This is a function to remove data that will often change or remove data that is unnecessary to track.



### _def get_name(json_data):_
This is a function to extract the name of the object


General Recommendations:
------

1. Avoid saving data that has not changed or not new
2. Avoid (when possible) code that is unique to data so that the code can be easily copied to new modules