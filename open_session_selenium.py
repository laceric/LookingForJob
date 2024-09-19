# Recupere les différents modules
from scraper_offre_utils import *  # Fonctions globales

import time

# Initialisation du navigateur
driver = lancement_session_selenium()

# Demander à l'utilisateur de faire un choix
choix = input("Entrez 'stop'  pour arrêter: ").lower()

# Boucle jusqu'à ce que l'utilisateur entre un choix valide
while choix != 'stop':
    print("Choix invalide.")
    choix = input("Entrez 'stop'  pour arrêter: ").lower()

# Afficher le choix validé
print(f"Vous avez choisi : {choix}")