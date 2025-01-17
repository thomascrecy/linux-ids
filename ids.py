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
OUTPUT_FILE = "/var/ids/db.json"
LOG_FILE = "/var/log/ids/ids.log"

# Liste pour stocker les propriétés des fichiers
file_properties_list = []

# Parseur d'arguments en ligne de commande
parser = argparse.ArgumentParser(
    description='Document d\'aide',
    epilog="Fin de l'aide"
)
parser.add_argument('-v', '--version', action='version',
                    version='%(prog)s 1.0')
parser.add_argument('command', choices=['build', 'check'], help="Commande à exécuter", nargs='?')
args = parser.parse_args()

# Configuration des logs
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

# Fonction pour calculer les hachages des fichiers
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
        logging.error(f"Erreur lors du calcul des hachages pour {file_path}: {e}")
        return {"error": str(e)}

# Fonction pour obtenir les propriétés d'un fichier
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
        logging.info(f"Propriétés récupérées pour {file_path}")
        return properties
    except (FileNotFoundError, PermissionError) as e:
        logging.error(f"Erreur lors de la récupération des propriétés pour {file_path}: {e}")
        return {"error": str(e)}

# Fonction pour obtenir le propriétaire du fichier
def get_owner(file_path):
    import pwd
    return pwd.getpwuid(os.stat(file_path).st_uid).pw_name

# Fonction pour obtenir le groupe du fichier
def get_group(file_path):
    import grp
    return grp.getgrgid(os.stat(file_path).st_gid).gr_name

# Fonction pour obtenir les ports TCP/UDP ouverts
def get_open_ports():
    try:
        result = subprocess.check_output(["ss", "-tuln"], text=True)
        logging.info("Ports ouverts récupérés avec succès")
        return result.strip().split("\n")
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des ports ouverts: {e}")
        return {"error": str(e)}

# Fonction pour générer et sauvegarder l'état actuel (commande build)
def generate_report():
    logging.info("Démarrage de la génération du rapport")
    report = {
        "build_time": time.ctime(),
        "files": [],
        "open_ports": get_open_ports(),
    }

    for file_path in file_paths:
        report["files"].append(get_file_properties(file_path))

    # Sauvegarder le rapport dans un fichier JSON
    try:
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, "w") as json_file:
            json.dump(report, json_file, indent=4)
        logging.info(f"Rapport sauvegardé dans {OUTPUT_FILE}")
    except Exception as e:
        logging.error(f"Erreur lors de la sauvegarde du rapport: {e}")

# Fonction pour vérifier si l'état a changé (commande check)
def check_state():
    try:
        with open(OUTPUT_FILE, "r") as json_file:
            stored_state = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Erreur lors du chargement de l'état sauvegardé: {e}")
        return {"state": "divergent", "error": str(e)}

    # Génération de l'état actuel
    current_report = {
        "build_time": time.ctime(),
        "files": [],
        "open_ports": get_open_ports(),
    }

    for file_path in file_paths:
        current_report["files"].append(get_file_properties(file_path))

    # Comparaison des états
    if current_report == stored_state:
        return {"state": "ok"}
    else:
        return {"state": "divergent", "changes": current_report}

# Exécution du script
if __name__ == "__main__":
    if args.command == 'build':
        generate_report()
    elif args.command == 'check':
        result = check_state()
        print(json.dumps(result, indent=4, ensure_ascii=False))
    else:
        print("Usage: python ids.py [build|check]")
        print("Veuillez spécifier une commande valide.")
