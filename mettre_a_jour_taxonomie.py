#!/usr/bin/env python3
"""
Télécharge la taxonomie eBird la plus récente (API eBird) et l'écrit au format
du fichier officiel eBird_taxonomy_vXXXX.csv lu par generate_gallery.py.

eBird publie une nouvelle taxonomie chaque automne (splits, changements de genre,
déplacements entre familles). Tant que config.yaml pointe vers l'ancienne, les
espèces renommées dans l'export MyEBirdData.csv ne sont pas reconnues et tombent
dans la famille « Autres ».

Usage:
    python mettre_a_jour_taxonomie.py            # écrit wazo_codes/eBird_taxonomy_v<année>.csv
    python mettre_a_jour_taxonomie.py sortie.csv

Ensuite, mettre à jour `fichiers: taxonomie:` dans config.yaml et relancer
generer_tout.py.
"""

import csv
import io
import json
import sys
from urllib.request import Request, urlopen

URL_TAXONOMIE = "https://api.ebird.org/v2/ref/taxonomy/ebird?fmt=csv"
URL_VERSIONS = "https://api.ebird.org/v2/ref/taxonomy/versions"

# Colonnes du fichier officiel (celles que lit EBirdTaxonomy)
COLONNES = ['TAXON_ORDER', 'CATEGORY', 'SPECIES_CODE', 'TAXON_CONCEPT_ID',
            'PRIMARY_COM_NAME', 'SCI_NAME', 'ORDER', 'FAMILY', 'SPECIES_GROUP',
            'REPORT_AS']


def telecharger(url: str) -> str:
    requete = Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; eBird Gallery)'})
    with urlopen(requete, timeout=60) as reponse:
        return reponse.read().decode('utf-8-sig')


def version_courante() -> str:
    versions = json.loads(telecharger(URL_VERSIONS))
    for v in versions:
        if v.get('latest'):
            return str(int(v['authorityVer']))
    raise RuntimeError("Version courante de la taxonomie introuvable")


def convertir(texte_api: str, sortie: str) -> int:
    """Convertit le CSV de l'API au format eBird_taxonomy_vXXXX.csv."""
    n = 0
    with open(sortie, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=COLONNES)
        writer.writeheader()
        for row in csv.DictReader(io.StringIO(texte_api)):
            fam_sci = row['FAMILY_SCI_NAME'].strip()
            fam_com = row['FAMILY_COM_NAME'].strip()
            ordre = float(row['TAXON_ORDER'])
            writer.writerow({
                'TAXON_ORDER': int(ordre) if ordre == int(ordre) else ordre,
                'CATEGORY': row['CATEGORY'],
                'SPECIES_CODE': row['SPECIES_CODE'],
                'TAXON_CONCEPT_ID': '',  # absent de l'API, non utilisé
                'PRIMARY_COM_NAME': row['COMMON_NAME'],
                'SCI_NAME': row['SCIENTIFIC_NAME'],
                'ORDER': row['ORDER'],
                # Même forme que le fichier officiel : "Anatidae (Ducks, Geese, and Waterfowl)"
                'FAMILY': f"{fam_sci} ({fam_com})" if fam_sci and fam_com else fam_sci,
                'SPECIES_GROUP': fam_com,
                'REPORT_AS': row['REPORT_AS'],
            })
            n += 1
    return n


def main():
    version = version_courante()
    sortie = sys.argv[1] if len(sys.argv) > 1 else f"wazo_codes/eBird_taxonomy_v{version}.csv"
    print(f"📚 Taxonomie eBird v{version} : téléchargement...")
    n = convertir(telecharger(URL_TAXONOMIE), sortie)
    print(f"   ✓ {n} taxons écrits dans {sortie}")
    print(f"   → Mettre à jour config.yaml (fichiers: taxonomie: \"{sortie}\") puis relancer generer_tout.py")


if __name__ == '__main__':
    main()
