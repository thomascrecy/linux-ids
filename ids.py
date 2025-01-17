import os
import json
import argparse
import logging
import hashlib
import pwd
import grp
import time

CONFIG_PATH = "/etc/ids/config.json"
DB_PATH = "/var/ids/db.json"
LOG_PATH = "/var/log/ids/ids.log"

def setup_logging():
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z"
    )
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console.setFormatter(formatter)
    logging.getLogger().addHandler(console)

def load_config(path):
    try:
        with open(path, "r") as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        logging.error(f"Fichier de configuration non trouvé : {path}")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Erreur de lecture du fichier de configuration : {e}")
        return {}

def compute_hashes(file_path):
    hashes = {"MD5": None, "SHA256": None, "SHA512": None}
    try:
        with open(file_path, "rb") as f:
            data = f.read()
            hashes["MD5"] = hashlib.md5(data).hexdigest()
            hashes["SHA256"] = hashlib.sha256(data).hexdigest()
            hashes["SHA512"] = hashlib.sha512(data).hexdigest()
    except Exception as e:
        logging.error(f"Erreur de calcul des hachages pour {file_path}: {e}")
    return hashes

def get_file_properties(file_path):
    try:
        stats = os.stat(file_path)
        return {
            "path": file_path,
            "size": stats.st_size,
            "last_modified": time.ctime(stats.st_mtime),
            "created": time.ctime(stats.st_ctime),
            "owner": pwd.getpwuid(stats.st_uid).pw_name,
            "group": grp.getgrgid(stats.st_gid).gr_name,
            **compute_hashes(file_path)
        }
    except Exception as e:
        logging.error(f"Erreur de récupération des propriétés pour {file_path}: {e}")
        return {}

def scan_files_and_dirs(files, dirs):
    results = []
    for file_path in files:
        results.append(get_file_properties(file_path))
    for dir_path in dirs:
        for root, _, files in os.walk(dir_path):
            for file in files:
                full_path = os.path.join(root, file)
                results.append(get_file_properties(full_path))
    return results

def get_open_ports():
    try:
        result = subprocess.check_output(["ss", "-tuln"], text=True)
        logging.info("Open ports retrieved successfully")
        return result.strip().split("\n")
    except Exception as e:
        logging.error(f"Erreur de récupération des ports ouverts : {e}")
        return []

def build_report(config):
    report = {
        "build_time": time.ctime(),
        "files": scan_files_and_dirs(config.get("files", []), config.get("dirs", [])),
    }
    if config.get("monitor_ports", False):
        report["open_ports"] = get_open_ports()
    return report

def save_report(report, path):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as json_file:
            json.dump(report, json_file, indent=4)
        logging.info(f"Rapport sauvegardé dans {path}")
    except Exception as e:
        logging.error(f"Erreur de sauvegarde du rapport : {e}")

def check_report(config):
    current_report = build_report(config)
    try:
        with open(DB_PATH, "r") as db_file:
            saved_report = json.load(db_file)
        if current_report == saved_report:
            print(json.dumps({"state": "ok"}))
        else:
            print(json.dumps({"state": "divergent", "changes": current_report}))
    except FileNotFoundError:
        logging.error(f"Fichier de base de données non trouvé : {DB_PATH}")
        print(json.dumps({"state": "error", "message": "Base de données introuvable"}))

def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Outil de surveillance des fichiers.")
    subparsers = parser.add_subparsers(dest="command")

    build_parser = subparsers.add_parser("build", help="Construire le fichier JSON de base.")
    build_parser.add_argument("--config", help="Chemin vers le fichier de configuration", default=CONFIG_PATH)

    check_parser = subparsers.add_parser("check", help="Vérifier l'état actuel par rapport au fichier JSON de base.")
    check_parser.add_argument("--config", help="Chemin vers le fichier de configuration", default=CONFIG_PATH)

    args = parser.parse_args()
    config = load_config(args.config)

    if args.command == "build":
        report = build_report(config)
        save_report(report, DB_PATH)
    elif args.command == "check":
        check_report(config)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
