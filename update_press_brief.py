#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de mise à jour automatique des dates dans revue-de-presse.html
Remplace "Date du jour :" et "Date de la nouvelle :" par la date actuelle en français.
"""

import re
from datetime import datetime

# Mois en français (fallback si locale fr_FR.UTF-8 non disponible)
MOIS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre"
]

def obtenir_date_francaise():
    """
    Retourne la date du jour au format français lisible.
    Format : "17 avril 2026"
    """
    aujourd_hui = datetime.now()
    jour = aujourd_hui.day
    mois = MOIS_FR[aujourd_hui.month - 1]
    annee = aujourd_hui.year
    return f"{jour} {mois} {annee}"

def mettre_a_jour_revue():
    """
    Met à jour revue-de-presse.html avec la date actuelle.
    Remplace :
    - La première occurrence de "Date du jour :"
    - Toutes les occurrences de "Date de la nouvelle :"
    """
    chemin_fichier = "revue-de-presse.html"
    date_actuelle = obtenir_date_francaise()
    
    try:
        # Lecture du fichier en UTF-8
        with open(chemin_fichier, 'r', encoding='utf-8') as f:
            contenu = f.read()
    except FileNotFoundError:
        print(f"Erreur : {chemin_fichier} introuvable.")
        exit(1)
    except Exception as e:
        print(f"Erreur lors de la lecture : {e}")
        exit(1)
    
    contenu_original = contenu
    
    # Pattern permissif pour "Date du jour :" (première occurrence)
    # Capture la ligne entière pour la remplacer
    pattern_jour = r'(Date\s+du\s+jour\s*:\s*)([^\n<]+)'
    contenu = re.sub(
        pattern_jour,
        r'\1' + date_actuelle,
        contenu,
        count=1,
        flags=re.IGNORECASE | re.MULTILINE
    )
    
    # Pattern permissif pour "Date de la nouvelle :" (toutes les occurrences)
    pattern_nouvelle = r'(Date\s+de\s+la\s+nouvelle\s*:\s*)([^\n<]+)'
    contenu = re.sub(
        pattern_nouvelle,
        r'\1' + date_actuelle,
        contenu,
        flags=re.IGNORECASE | re.MULTILINE
    )
    
    # Vérifier s'il y a eu des modifications
    if contenu == contenu_original:
        print("Aucune modification nécessaire.")
        exit(0)
    
    # Écrire les modifications en UTF-8
    try:
        with open(chemin_fichier, 'w', encoding='utf-8') as f:
            f.write(contenu)
        print(f"Mise à jour effectuée : {date_actuelle}")
        exit(0)
    except Exception as e:
        print(f"Erreur lors de l'écriture : {e}")
        exit(1)

if __name__ == "__main__":
    mettre_a_jour_revue()