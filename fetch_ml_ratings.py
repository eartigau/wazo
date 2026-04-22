#!/usr/bin/env python3
"""
Récupère les ratings (qualité ML) des photos eBird via l'API Macaulay Library.

Usage:
    python fetch_ml_ratings.py --cookie "VOTRE_COOKIE" [--limit 100]

Comment obtenir le cookie :
    1. Connectez-vous sur https://media.ebird.org
    2. Ouvrez les DevTools (F12) → onglet Network
    3. Rechargez la page
    4. Cliquez sur n'importe quelle requête vers media.ebird.org
    5. Dans les Request Headers, copiez la valeur complète de "Cookie"
    6. Passez-la avec --cookie "..."

Le script lit les ML catalog numbers depuis MyEBirdData.csv et
enregistre les ratings dans ml_ratings.csv
"""

import csv
import json
import time
import argparse
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

# ============================================================================
# CONFIG
# ============================================================================

EBIRD_CSV = "MyEBirdData.csv"
OUTPUT_FILE = "ml_ratings.csv"
API_URL = "https://media.ebird.org/api/v2/asset/{ml_id}"
REQUEST_TIMEOUT = 10
DELAY = 0.3  # secondes entre requêtes


# ============================================================================
# FONCTIONS
# ============================================================================

def charger_ml_ids(csv_file: str) -> list[str]:
    """Lit tous les ML catalog numbers depuis MyEBirdData.csv"""
    ml_ids = []
    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ml = row.get('ML Catalog Numbers', '').strip()
            if ml and not ml.startswith('--'):
                # Peut contenir plusieurs IDs séparés par des espaces
                for m in ml.split():
                    m = m.strip().rstrip(',')
                    if m.isdigit():
                        ml_ids.append(m)
    return list(dict.fromkeys(ml_ids))  # dédoublonner en gardant l'ordre


def charger_ratings_existants(output_file: str) -> dict:
    """Charge les ratings déjà récupérés pour ne pas re-fetcher"""
    ratings = {}
    if not Path(output_file).exists():
        return ratings
    with open(output_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ratings[row['ml_id']] = row
    return ratings


def fetch_rating(ml_id: str, cookie: str) -> dict | None:
    """
    Appelle l'API Macaulay Library et retourne les métadonnées.
    Retourne None en cas d'erreur.
    """
    url = API_URL.format(ml_id=ml_id)
    req = Request(url)
    req.add_header('Cookie', cookie)
    req.add_header('Accept', 'application/json')
    req.add_header('User-Agent', 'Mozilla/5.0 (compatible; eBird Gallery)')

    try:
        with urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            # Extraire les champs utiles
            return {
                'ml_id': ml_id,
                'rating': data.get('rating', ''),
                'rating_count': data.get('ratingCount', ''),
                'common_name': data.get('commonName', ''),
                'scientific_name': data.get('sciName', ''),
                'date': data.get('obsDtDisplay', ''),
                'location': data.get('locationLine1', ''),
                'media_type': data.get('mediaType', ''),
            }
    except HTTPError as e:
        if e.code == 401:
            print(f"  ⚠ Cookie invalide ou expiré (401)")
            return None
        elif e.code == 404:
            return {'ml_id': ml_id, 'rating': '', 'rating_count': '',
                    'common_name': '', 'scientific_name': '', 'date': '',
                    'location': '', 'media_type': 'not_found'}
        else:
            print(f"  ✗ HTTP {e.code} pour {ml_id}")
            return None
    except (URLError, Exception) as e:
        print(f"  ✗ Erreur pour {ml_id}: {e}")
        return None


def sauvegarder(output_file: str, ratings: dict):
    """Sauvegarde tous les ratings dans le CSV"""
    fields = ['ml_id', 'rating', 'rating_count', 'common_name',
              'scientific_name', 'date', 'location', 'media_type']
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in ratings.values():
            writer.writerow({k: row.get(k, '') for k in fields})


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Récupère les ratings ML des photos eBird')
    parser.add_argument('--cookie', required=True,
                        help='Valeur complète du header Cookie depuis media.ebird.org')
    parser.add_argument('--limit', type=int, default=0,
                        help='Limiter au N premiers IDs (0 = tous)')
    parser.add_argument('--ebird-csv', default=EBIRD_CSV,
                        help=f'Fichier eBird CSV (défaut: {EBIRD_CSV})')
    parser.add_argument('--output', default=OUTPUT_FILE,
                        help=f'Fichier de sortie (défaut: {OUTPUT_FILE})')
    args = parser.parse_args()

    print(f"\n📂 Lecture des ML IDs depuis {args.ebird_csv}...")
    ml_ids = charger_ml_ids(args.ebird_csv)
    print(f"   {len(ml_ids)} IDs trouvés")

    # Exclure ceux déjà récupérés
    ratings = charger_ratings_existants(args.output)
    a_fetcher = [m for m in ml_ids if m not in ratings]
    print(f"   {len(ratings)} déjà en cache, {len(a_fetcher)} à fetcher")

    if args.limit > 0:
        a_fetcher = a_fetcher[:args.limit]
        print(f"   → Limité à {args.limit}")

    if not a_fetcher:
        print("\n✅ Tout est déjà en cache.")
        return

    print(f"\n🌐 Récupération des ratings...")
    erreurs_consecutives = 0

    for i, ml_id in enumerate(a_fetcher, 1):
        print(f"  [{i}/{len(a_fetcher)}] {ml_id}...", end=' ', flush=True)
        result = fetch_rating(ml_id, args.cookie)

        if result is None:
            erreurs_consecutives += 1
            print("✗")
            if erreurs_consecutives >= 3:
                print("\n⛔ 3 erreurs consécutives — cookie probablement expiré. Arrêt.")
                break
        else:
            erreurs_consecutives = 0
            rating = result.get('rating', '')
            print(f"{'⭐ ' + str(rating) if rating else '—'}")
            ratings[ml_id] = result

        # Sauvegarder toutes les 50 requêtes
        if i % 50 == 0:
            sauvegarder(args.output, ratings)
            print(f"   💾 Sauvegarde intermédiaire ({len(ratings)} entrées)")

        time.sleep(DELAY)

    sauvegarder(args.output, ratings)
    print(f"\n✅ Terminé — {len(ratings)} ratings dans {args.output}")

    # Résumé des ratings
    rated = [r for r in ratings.values() if r.get('rating')]
    if rated:
        from collections import Counter
        dist = Counter(r['rating'] for r in rated)
        print(f"\n📊 Distribution des ratings:")
        for k in sorted(dist.keys(), reverse=True):
            print(f"   {k}: {dist[k]} photos")


if __name__ == '__main__':
    main()
