import os
import json
import argparse
import logging
import hashlib
import pwd
import grp
import time

# Configuration par défaut
CONFIG_PATH = "/etc/ids/config.json"
LOG_PATH = "/var/log/ids/ids.log"

# Initialisation du logger
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

# Lecture de la configuration
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

# Calcul des hachages des fichiers
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

# Récupération des propriétés des fichiers
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

# Génération du rapport
def generate_report(config):
    report = {"files": []}
    for file_path in config.get("file_paths", []):
        report["files"].append(get_file_properties(file_path))
    return report

# Écriture du rapport dans un fichier JSON
def save_report(report, output_path):
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as json_file:
            json.dump(report, json_file, indent=4)
        logging.info(f"Rapport sauvegardé dans {output_path}")
    except Exception as e:
        logging.error(f"Erreur de sauvegarde du rapport : {e}")

# Point d'entrée principal
def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Outil de surveillance des fichiers.")
    parser.add_argument("--config", help="Chemin vers le fichier de configuration", default=CONFIG_PATH)
    args = parser.parse_args()

    config = load_config(args.config)
    report = generate_report(config)
    save_report(report, args.output)

if __name__ == "__main__":
    main()
