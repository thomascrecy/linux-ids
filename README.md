# IDS - Outil de Surveillance des Fichiers et Ports

Ce script python est un outil de surveillance pour suivre l'état des fichiers, des dossiers et des ports TCP/UDP sur une machine Linux. Il permet de détecter les changements dans le système et de générer des rapports détaillés.

## Installation

### Pré-requis

- Python 3
- Accès administrateur pour écrire dans `/etc/` et `/var/`

### Étapes d'installation

1. Clonez ce dépôt :
   ```bash
   git clone https://github.com/thomascrecy/linux-ids
   cd linux-ids

2. Lancer le programme :
    ```bash
    python ids.py build

3. Vérifier si les fichiers ont changés :
    ```bash
    python ids.py check