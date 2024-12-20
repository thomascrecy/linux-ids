import os
import stat
import time
import json

file_path = 'etc/shadow'
LOG_FILE = 'logs.json'

# Get file status
file_status = os.stat(file_path)

# File properties
file_properties = {
    "file_size": file_status.st_size,
    "last_modified": time.ctime(file_status.st_mtime),
    "permissions": oct(file_status.st_mode)[-3:]
}

# Write the properties to the JSON file
with open(LOG_FILE, 'w') as json_file:
    json.dump(file_properties, json_file, indent=4)

print(f"File properties have been logged to {LOG_FILE}")