import os
import stat
import time
import json
import argparse
import logging
import hashlib
import platform
import subprocess

file_paths = ['/etc/shadow', '/etc/passwd', '/etc/group']
OUTPUT_FILE = "/var/ids/db.json"  # Updated to db.json for storing the state
LOG_FILE = "/var/log/ids/ids.log"

# List to store file properties
file_properties_list = []

# Command-line argument parser
parser = argparse.ArgumentParser(
    description='Help document',
    epilog="End of Help"
)
parser.add_argument('-v', '--version', action='version',
                    version='%(prog)s 1.0')
parser.add_argument('command', choices=['build', 'check'], help="Command to run", nargs='?')
args = parser.parse_args()

# Logging configuration
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console.setFormatter(formatter)
logging.getLogger().addHandler(console)

# Function to compute file hashes
def compute_hashes(file_path):
    try:
        hashes = {"MD5": None, "SHA256": None, "SHA512": None}
        with open(file_path, "rb") as f:
            data = f.read()
            hashes["MD5"] = hashlib.md5(data).hexdigest()
            hashes["SHA256"] = hashlib.sha256(data).hexdigest()
            hashes["SHA512"] = hashlib.sha512(data).hexdigest()
        return hashes
    except (FileNotFoundError, PermissionError) as e:
        logging.error(f"Error computing hashes for {file_path}: {e}")
        return {"error": str(e)}

# Function to get file properties
def get_file_properties(file_path):
    try:
        stats = os.stat(file_path)
        properties = {
            "path": file_path,
            "size": stats.st_size,
            "last_modified": time.ctime(stats.st_mtime),
            "created": time.ctime(stats.st_ctime),
            "owner": get_owner(file_path),
            "group": get_group(file_path),
        }
        properties.update(compute_hashes(file_path))
        logging.info(f"Properties retrieved for {file_path}")
        return properties
    except (FileNotFoundError, PermissionError) as e:
        logging.error(f"Error retrieving properties for {file_path}: {e}")
        return {"error": str(e)}

# Function to get file owner
def get_owner(file_path):
    import pwd
    return pwd.getpwuid(os.stat(file_path).st_uid).pw_name

# Function to get file group
def get_group(file_path):
    import grp
    return grp.getgrgid(os.stat(file_path).st_gid).gr_name

# Function to get open TCP/UDP ports
def get_open_ports():
    try:
        result = subprocess.check_output(["ss", "-tuln"], text=True)
        logging.info("Open ports retrieved successfully")
        return result.strip().split("\n")
    except Exception as e:
        logging.error(f"Error retrieving open ports: {e}")
        return {"error": str(e)}

# Function to generate and save the current state (build command)
def generate_report():
    logging.info("Starting report generation")
    report = {
        "build_time": time.ctime(),
        "files": [],
        "open_ports": get_open_ports(),
    }

    for file_path in file_paths:
        report["files"].append(get_file_properties(file_path))

    # Save report to JSON file
    try:
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, "w") as json_file:
            json.dump(report, json_file, indent=4)
        logging.info(f"Report saved to {OUTPUT_FILE}")
    except Exception as e:
        logging.error(f"Error saving report: {e}")

# Function to check if the state has changed (check command)
def check_state():
    try:
        with open(OUTPUT_FILE, "r") as json_file:
            stored_state = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading stored state: {e}")
        return {"state": "divergent", "error": str(e)}

    # Current state generation
    current_report = {
        "build_time": time.ctime(),
        "files": [],
        "open_ports": get_open_ports(),
    }

    for file_path in file_paths:
        current_report["files"].append(get_file_properties(file_path))

    # Compare states
    if current_report == stored_state:
        return {"state": "ok"}
    else:
        return {"state": "divergent", "changes": current_report}

# Execution
if __name__ == "__main__":
    if args.command == 'build':
        generate_report()
    elif args.command == 'check':
        result = check_state()
        print(json.dumps(result, indent=4))
    else:
        print("Usage: python ids.py [build|check]")
        print("Please specify a valid command.")
