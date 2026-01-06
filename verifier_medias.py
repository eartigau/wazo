#!/usr/bin/env python3
"""
Vérificateur de médias eBird / Macaulay Library
Vérifie si les fichiers sont des images (existent en 480) ou des sons
Maintient un cache CSV avec possibilité d'exclusions manuelles
"""

import csv
import os
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError


# ============================================================================
# CONFIGURATION
# ============================================================================

CACHE_FILE = "media_cache.csv"
REQUEST_TIMEOUT = 10  # secondes
DELAY_BETWEEN_REQUESTS = 0.2  # secondes (pour ne pas surcharger le serveur)


# ============================================================================
# FONCTIONS DE VÉRIFICATION HTTP
# ============================================================================

def verifier_image_existe(ml_catalog_number: str) -> bool:
    """
    Vérifie si une image existe en taille 480 sur Macaulay Library
    Retourne True si c'est une image, False si c'est un son ou n'existe pas
    """
    url = f"https://cdn.download.ams.birds.cornell.edu/api/v2/asset/{ml_catalog_number}/480"
    
    try:
        # Utiliser HEAD pour ne pas télécharger le contenu
        request = Request(url, method='HEAD')
        request.add_header('User-Agent', 'Mozilla/5.0 (compatible; eBird Gallery)')
        
        with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            # Vérifier le Content-Type
            content_type = response.headers.get('Content-Type', '')
            if 'image' in content_type.lower():
                return True
            # Même si pas explicitement image, si status 200, c'est probablement OK
            return response.status == 200
            
    except HTTPError as e:
        # 404 = fichier n'existe pas (probablement un son)
        if e.code == 404:
            return False
        # Autres erreurs HTTP
        print(f"  ⚠ Erreur HTTP {e.code} pour {ml_catalog_number}")
        return False
        
    except URLError as e:
        print(f"  ⚠ Erreur réseau pour {ml_catalog_number}: {e.reason}")
        return False
        
    except Exception as e:
        print(f"  ⚠ Erreur inattendue pour {ml_catalog_number}: {e}")
        return False


# ============================================================================
# GESTION DU CACHE CSV
# ============================================================================

def charger_cache(fichier_cache: str = CACHE_FILE) -> dict:
    """
    Charge le cache depuis le fichier CSV
    Format: ml_number,status,raison
    status: 'image', 'son', 'exclu_manuel'
    """
    cache = {}
    
    if not os.path.exists(fichier_cache):
        return cache
    
    try:
        with open(fichier_cache, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ml_number = row.get('ml_number', '').strip()
                if ml_number:
                    cache[ml_number] = {
                        'status': row.get('status', 'inconnu'),
                        'raison': row.get('raison', ''),
                        'date_verification': row.get('date_verification', '')
                    }
    except Exception as e:
        print(f"⚠ Erreur lecture cache: {e}")
    
    return cache


def sauvegarder_cache(cache: dict, fichier_cache: str = CACHE_FILE):
    """
    Sauvegarde le cache dans le fichier CSV
    """
    try:
        with open(fichier_cache, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['ml_number', 'status', 'raison', 'date_verification']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for ml_number, data in sorted(cache.items()):
                writer.writerow({
                    'ml_number': ml_number,
                    'status': data.get('status', ''),
                    'raison': data.get('raison', ''),
                    'date_verification': data.get('date_verification', '')
                })
        
        print(f"✓ Cache sauvegardé: {fichier_cache}")
        
    except Exception as e:
        print(f"⚠ Erreur sauvegarde cache: {e}")


def ajouter_exclusion_manuelle(ml_numbers: list, raison: str = "photo mauvaise",
                               fichier_cache: str = CACHE_FILE):
    """
    Ajoute des exclusions manuelles au cache
    Utilisation: pour exclure des photos de mauvaise qualité
    """
    from datetime import datetime
    
    cache = charger_cache(fichier_cache)
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    for ml_number in ml_numbers:
        ml_number = str(ml_number).strip()
        cache[ml_number] = {
            'status': 'exclu_manuel',
            'raison': raison,
            'date_verification': date_now
        }
        print(f"  ✗ Exclu manuellement: {ml_number} ({raison})")
    
    sauvegarder_cache(cache, fichier_cache)
    print(f"\n✓ {len(ml_numbers)} exclusion(s) ajoutée(s)")


def retirer_exclusion(ml_numbers: list, fichier_cache: str = CACHE_FILE):
    """
    Retire des exclusions du cache (force re-vérification)
    """
    cache = charger_cache(fichier_cache)
    
    for ml_number in ml_numbers:
        ml_number = str(ml_number).strip()
        if ml_number in cache:
            del cache[ml_number]
            print(f"  ✓ Retiré du cache: {ml_number}")
    
    sauvegarder_cache(cache, fichier_cache)


# ============================================================================
# VÉRIFICATION PRINCIPALE
# ============================================================================

def verifier_medias(ml_numbers: list, fichier_cache: str = CACHE_FILE,
                   forcer_verification: bool = False) -> dict:
    """
    Vérifie une liste de numéros ML et retourne leur statut
    Utilise le cache pour éviter les requêtes répétées
    
    Retourne: dict avec 'images' (liste) et 'exclus' (liste)
    """
    from datetime import datetime
    
    cache = charger_cache(fichier_cache)
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    images = []
    exclus = []
    a_verifier = []
    
    # Séparer ce qui est en cache vs à vérifier
    for ml_number in ml_numbers:
        ml_number = str(ml_number).strip()
        if not ml_number:
            continue
            
        if ml_number in cache and not forcer_verification:
            status = cache[ml_number]['status']
            if status == 'image':
                images.append(ml_number)
            else:
                exclus.append(ml_number)
        else:
            a_verifier.append(ml_number)
    
    # Vérifier les nouveaux
    if a_verifier:
        print(f"\n🔍 Vérification de {len(a_verifier)} médias...")
        
        for i, ml_number in enumerate(a_verifier, 1):
            if i % 50 == 0:
                print(f"  ... {i}/{len(a_verifier)}")
            
            est_image = verifier_image_existe(ml_number)
            
            if est_image:
                cache[ml_number] = {
                    'status': 'image',
                    'raison': 'vérifié automatiquement',
                    'date_verification': date_now
                }
                images.append(ml_number)
            else:
                cache[ml_number] = {
                    'status': 'son',
                    'raison': 'pas d\'image 480 disponible',
                    'date_verification': date_now
                }
                exclus.append(ml_number)
            
            # Délai entre requêtes
            time.sleep(DELAY_BETWEEN_REQUESTS)
        
        # Sauvegarder le cache mis à jour
        sauvegarder_cache(cache, fichier_cache)
    
    print(f"\n📊 Résultats:")
    print(f"   ✓ Images valides: {len(images)}")
    print(f"   ✗ Exclus (sons/manuels): {len(exclus)}")
    
    return {
        'images': images,
        'exclus': exclus,
        'cache': cache
    }


def est_image_valide(ml_number: str, fichier_cache: str = CACHE_FILE) -> bool:
    """
    Vérifie rapidement si un numéro ML est une image valide
    Utilise le cache, vérifie en ligne si pas en cache
    """
    cache = charger_cache(fichier_cache)
    ml_number = str(ml_number).strip()
    
    if ml_number in cache:
        return cache[ml_number]['status'] == 'image'
    
    # Pas en cache, vérifier en ligne
    est_image = verifier_image_existe(ml_number)
    
    # Mettre en cache
    from datetime import datetime
    cache[ml_number] = {
        'status': 'image' if est_image else 'son',
        'raison': 'vérifié automatiquement',
        'date_verification': datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    sauvegarder_cache(cache, fichier_cache)
    
    return est_image


def afficher_statistiques_cache(fichier_cache: str = CACHE_FILE):
    """
    Affiche les statistiques du cache
    """
    cache = charger_cache(fichier_cache)
    
    if not cache:
        print("Cache vide")
        return
    
    images = sum(1 for v in cache.values() if v['status'] == 'image')
    sons = sum(1 for v in cache.values() if v['status'] == 'son')
    manuels = sum(1 for v in cache.values() if v['status'] == 'exclu_manuel')
    
    print(f"\n📊 Statistiques du cache ({fichier_cache}):")
    print(f"   Total entrées: {len(cache)}")
    print(f"   ✓ Images: {images}")
    print(f"   ♪ Sons: {sons}")
    print(f"   ✗ Exclusions manuelles: {manuels}")


# ============================================================================
# INTERFACE LIGNE DE COMMANDE
# ============================================================================

if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("🔍 VÉRIFICATEUR DE MÉDIAS eBird")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("""
Usage:
    python verifier_medias.py stats
        → Afficher les statistiques du cache
    
    python verifier_medias.py exclure ML123456 ML789012 "raison"
        → Ajouter des exclusions manuelles
    
    python verifier_medias.py retirer ML123456
        → Retirer une exclusion
    
    python verifier_medias.py verifier ML123456 ML789012
        → Vérifier des numéros ML spécifiques
""")
        afficher_statistiques_cache()
        sys.exit(0)
    
    commande = sys.argv[1].lower()
    
    if commande == "stats":
        afficher_statistiques_cache()
    
    elif commande == "exclure":
        if len(sys.argv) < 3:
            print("Erreur: spécifiez au moins un numéro ML")
            sys.exit(1)
        
        # Chercher la raison (dernier argument si c'est du texte)
        args = sys.argv[2:]
        raison = "photo mauvaise"
        ml_numbers = []
        
        for arg in args:
            if arg.isdigit() or arg.startswith('ML'):
                ml_numbers.append(arg.replace('ML', ''))
            else:
                raison = arg
        
        if ml_numbers:
            ajouter_exclusion_manuelle(ml_numbers, raison)
    
    elif commande == "retirer":
        if len(sys.argv) < 3:
            print("Erreur: spécifiez au moins un numéro ML")
            sys.exit(1)
        
        ml_numbers = [arg.replace('ML', '') for arg in sys.argv[2:]]
        retirer_exclusion(ml_numbers)
    
    elif commande == "verifier":
        if len(sys.argv) < 3:
            print("Erreur: spécifiez au moins un numéro ML")
            sys.exit(1)
        
        ml_numbers = [arg.replace('ML', '') for arg in sys.argv[2:]]
        resultats = verifier_medias(ml_numbers)
        
        print("\nImages valides:")
        for ml in resultats['images']:
            print(f"  ✓ ML{ml}")
        
        print("\nExclus:")
        for ml in resultats['exclus']:
            print(f"  ✗ ML{ml}")
    
    else:
        print(f"Commande inconnue: {commande}")
        sys.exit(1)
