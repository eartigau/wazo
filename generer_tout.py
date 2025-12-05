#!/usr/bin/env python3
"""
Script principal pour générer toutes les galeries eBird v2.0
Bilingue français/anglais avec support taxonomie
"""

import sys
import re
from pathlib import Path
from datetime import datetime, timedelta

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    print("❌ Jinja2 non installé. Exécutez: pip install jinja2")
    sys.exit(1)

from generate_gallery import EBirdGalleryGenerator, verifier_tous_les_medias, generer_description_groupe_fr, mettre_au_pluriel
from config_galeries import VOYAGES, GALERIES_GENERALES


# ============================================================================
# CONFIGURATION
# ============================================================================

CSV_FILE = "MyEBirdData.csv"
TAXONOMY_FILE = "eBird_taxonomy_v2025.csv"
MEDIA_CACHE = "media_cache.csv"
TRADUCTIONS_FILE = "traductions_lieux.csv"

# Templates
GALLERY_TEMPLATE = "gallery_template.html"
SPECIES_LIST_TEMPLATE = "species_list_template.html"

# Vérifier les médias en ligne (True = plus lent mais plus précis)
VERIFIER_MEDIAS_EN_LIGNE = False  # Mettre True pour la première exécution


# ============================================================================
# CONSTRUCTION DU MENU
# ============================================================================

def construire_menu(generator):
    """Construit la structure du menu bilingue"""
    
    # Récupérer les familles qui ont des photos
    familles_avec_photos = generator.get_families_with_photos()
    
    menu = [
        {
            'name_fr': 'Accueil',
            'name_en': 'Home',
            'file_fr': 'index.html',
            'file_en': 'index_en.html'
        },
        {
            'name_fr': 'Espèces',
            'name_en': 'Species',
            'file_fr': 'species_list_fr.html',
            'file_en': 'species_list_en.html'
        },
        {
            'name_fr': 'Ajouts récents',
            'name_en': 'Recent Updates',
            'file_fr': 'gallery_recent_fr.html',
            'file_en': 'gallery_recent_en.html'
        }
    ]
    
    # Dropdown Voyages
    voyages_dropdown = []
    for v in VOYAGES:
        voyages_dropdown.append({
            'name_fr': v['nom_fr'],
            'name_en': v['nom_en'],
            'file_fr': f"{v['id']}_fr.html",
            'file_en': f"{v['id']}_en.html"
        })
    
    if voyages_dropdown:
        menu.append({
            'name_fr': 'Voyages',
            'name_en': 'Trips',
            'dropdown': voyages_dropdown
        })
    
    # Dropdown Familles - TOUTES les familles avec photos
    # Générer les descriptions pour chaque famille
    species_list = generator.get_species_list()
    
    # Grouper les espèces par famille pour générer les descriptions
    familles_especes = {}
    for sp in species_list:
        fam = sp['family'] or 'Unknown'
        if fam not in familles_especes:
            familles_especes[fam] = []
        familles_especes[fam].append(sp['common_name_fr'])
    
    familles_dropdown = []
    for fam_info in familles_avec_photos:
        fam_code = fam_info['code']
        
        # Ignorer Unknown pour le menu
        if fam_code == 'Unknown':
            continue
        
        # Générer description française
        noms_fr = familles_especes.get(fam_code, [])
        desc_fr = generer_description_groupe_fr(noms_fr)
        
        # Extraire description anglaise du family_full
        name_en_match = re.search(r'\(([^)]+)\)', fam_info['name'])
        desc_en = name_en_match.group(1) if name_en_match else ''
        
        # Format: "Anatidae (Canards, Oies, etc.)"
        name_fr = f"{fam_code} ({desc_fr})" if desc_fr else fam_code
        name_en = f"{fam_code} ({desc_en})" if desc_en else fam_code
        
        # ID de fichier basé sur le code famille (en minuscules, sans caractères spéciaux)
        file_id = f"gallery_{fam_code.lower()}"
        
        familles_dropdown.append({
            'name_fr': name_fr,
            'name_en': name_en,
            'desc_fr': desc_fr,  # Description seule pour sous-titre
            'desc_en': desc_en,  # Description seule pour sous-titre
            'file_fr': f"{file_id}_fr.html",
            'file_en': f"{file_id}_en.html",
            'family_code': fam_code  # Pour la génération
        })
    
    if familles_dropdown:
        # Calculer le nombre de colonnes (max 20 familles par colonne)
        num_familles = len(familles_dropdown)
        import math
        num_columns = math.ceil(num_familles / 20)
        num_columns = max(2, min(6, num_columns))  # Entre 2 et 6 colonnes
        
        column_class = {
            2: 'two_columns',
            3: 'three_columns', 
            4: 'four_columns',
            5: 'five_columns',
            6: 'six_columns'
        }
        
        menu.append({
            'name_fr': 'Familles',
            'name_en': 'Families',
            'dropdown': familles_dropdown,
            column_class[num_columns]: True
        })
    
    return menu, familles_dropdown


# ============================================================================
# GÉNÉRATION
# ============================================================================

def generer_toutes_galeries():
    """Génère toutes les galeries configurées"""
    
    print("=" * 60)
    print("🐦 GÉNÉRATION DES GALERIES eBird v2.0")
    print("=" * 60)
    
    # Vérifier les fichiers
    if not Path(CSV_FILE).exists():
        print(f"\n❌ Fichier non trouvé: {CSV_FILE}")
        print("   Téléchargez depuis: https://ebird.org/downloadMyData")
        sys.exit(1)
    
    if not Path(TAXONOMY_FILE).exists():
        print(f"\n❌ Fichier taxonomie non trouvé: {TAXONOMY_FILE}")
        print("   Téléchargez depuis: https://ebird.org/science/use-ebird-data/the-ebird-taxonomy")
        sys.exit(1)
    
    # Initialiser le générateur
    print(f"\n📂 Chargement des données...")
    generator = EBirdGalleryGenerator(
        csv_file=CSV_FILE,
        taxonomy_file=TAXONOMY_FILE,
        media_cache_file=MEDIA_CACHE,
        traductions_file=TRADUCTIONS_FILE
    )
    
    # Construire le menu (retourne aussi la liste des familles)
    menu, familles_dropdown = construire_menu(generator)
    
    # Compteurs
    total_galeries = 0
    
    # ========================================
    # LISTE DES ESPÈCES
    # ========================================
    print(f"\n📋 Liste des espèces...")
    generator.generate_species_list(
        output_base='species_list',
        template_file=SPECIES_LIST_TEMPLATE,
        menu=menu
    )
    
    # ========================================
    # AJOUTS RÉCENTS
    # ========================================
    print(f"\n🆕 Galerie ajouts récents...")
    
    # Calculer la date d'il y a 3 mois
    trois_mois = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    
    # D'abord, obtenir les photos des 3 derniers mois (sans limite)
    photos_3_mois = generator.filter_observations(
        limit=9999,  # Pas de limite réelle
        date_start=trois_mois,
        verifier_medias_en_ligne=VERIFIER_MEDIAS_EN_LIGNE,
        sort_by='date'  # Tri chronologique inverse (plus récent d'abord)
    )
    
    # Si moins de 50 photos dans les 3 derniers mois, prendre les 50 dernières
    if len(photos_3_mois) < 50:
        photos_recent = generator.filter_observations(
            limit=50,
            verifier_medias_en_ligne=VERIFIER_MEDIAS_EN_LIGNE,
            sort_by='date'
        )
        print(f"   (moins de 50 photos en 3 mois, affichage des 50 dernières)")
    else:
        photos_recent = photos_3_mois
        print(f"   ({len(photos_recent)} photos des 3 derniers mois)")
    
    if photos_recent:
        # Compter les espèces
        species_set = set(p.get('scientific_name', '') for p in photos_recent)
        species_count = len(species_set)
        
        generator.generate_gallery(
            output_base='gallery_recent',
            title_fr='Ajouts récents',
            title_en='Recent Updates',
            photos=photos_recent,
            template_file=GALLERY_TEMPLATE,
            menu=menu,
            gallery_id='gallery_recent',
            species_count=species_count,
            show_date_in_overlay=True  # Afficher la date au survol
        )
        total_galeries += 1
    
    # ========================================
    # GALERIES GÉNÉRALES
    # ========================================
    print(f"\n📸 Galeries générales...")
    
    for config in GALERIES_GENERALES:
        photos = generator.filter_observations(
            limit=config.get('limite', 300),
            countries=config.get('pays'),
            date_start=config.get('date_debut'),
            date_end=config.get('date_fin'),
            verifier_medias_en_ligne=VERIFIER_MEDIAS_EN_LIGNE
        )
        
        if photos:
            generator.generate_gallery(
                output_base=config['id'],
                title_fr=config['nom_fr'],
                title_en=config['nom_en'],
                photos=photos,
                template_file=GALLERY_TEMPLATE,
                menu=menu,
                gallery_id=config['id']
            )
            total_galeries += 1
    
    # ========================================
    # VOYAGES
    # ========================================
    if VOYAGES:
        print(f"\n✈️ Galeries voyages...")
        
        for voyage in VOYAGES:
            photos = generator.filter_observations(
                limit=voyage.get('limite', 300),
                countries=voyage.get('pays'),
                regions=voyage.get('regions'),
                date_start=voyage.get('date_debut'),
                date_end=voyage.get('date_fin'),
                verifier_medias_en_ligne=VERIFIER_MEDIAS_EN_LIGNE
            )
            
            if photos:
                generator.generate_gallery(
                    output_base=voyage['id'],
                    title_fr=voyage['nom_fr'],
                    title_en=voyage['nom_en'],
                    photos=photos,
                    template_file=GALLERY_TEMPLATE,
                    menu=menu,
                    gallery_id=voyage['id']
                )
                total_galeries += 1
    
    # ========================================
    # FAMILLES (TOUTES LES FAMILLES OBSERVÉES)
    # ========================================
    if familles_dropdown:
        print(f"\n🦅 Galeries par famille ({len(familles_dropdown)} familles)...")
        
        for famille in familles_dropdown:
            fam_code = famille['family_code']
            file_id = f"gallery_{fam_code.lower()}"
            
            photos = generator.filter_observations(
                limit=500,  # Limite généreuse pour les familles
                families_list=[fam_code],
                verifier_medias_en_ligne=VERIFIER_MEDIAS_EN_LIGNE,
                sort_by='taxonomy'  # Tri taxonomique pour les familles
            )
            
            if photos:
                # Compter les espèces uniques
                species_set = set(p.get('scientific_name', '') for p in photos)
                species_count = len(species_set)
                
                # Titre: "Famille des Anatidaes" (avec 's')
                title_fr = f"Famille des {fam_code}s"
                title_en = f"{fam_code} Family"
                
                # Sous-titre: description (Canards, Oies, etc.)
                subtitle_fr = famille.get('desc_fr', '')
                subtitle_en = famille.get('desc_en', '')
                
                generator.generate_gallery(
                    output_base=file_id,
                    title_fr=title_fr,
                    title_en=title_en,
                    photos=photos,
                    template_file=GALLERY_TEMPLATE,
                    menu=menu,
                    gallery_id=file_id,
                    subtitle_fr=subtitle_fr,
                    subtitle_en=subtitle_en,
                    species_count=species_count
                )
                total_galeries += 1
    
    # ========================================
    # RÉSUMÉ
    # ========================================
    print("\n" + "=" * 60)
    print("✅ GÉNÉRATION TERMINÉE")
    print("=" * 60)
    
    species_list = generator.get_species_list()
    
    print(f"\n   📊 {total_galeries * 2} fichiers HTML générés ({total_galeries} galeries × 2 langues)")
    print(f"   🐦 {len(species_list)} espèces photographiées")
    print(f"   🦅 {len(familles_dropdown)} familles")
    print(f"   📁 Cache médias: {MEDIA_CACHE}")
    print(f"\n   → Ouvrez species_list_fr.html ou index.html")


# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        
        if cmd == "verifier":
            verifier_tous_les_medias(CSV_FILE, MEDIA_CACHE)
        
        elif cmd == "help":
            print("""
Usage:
    python generer_tout.py           → Génère toutes les galeries
    python generer_tout.py verifier  → Vérifie les médias (images vs sons)
    python generer_tout.py help      → Cette aide

Configuration:
    1. Placez MyEBirdData.csv et eBird_taxonomy_v2025.csv dans le dossier
    2. Modifiez config_galeries.py pour vos voyages
    3. Complétez traductions_lieux.csv avec vos régions
    4. Lancez: python generer_tout.py verifier (première fois)
    5. Lancez: python generer_tout.py

Note: Les galeries par famille sont générées automatiquement
      pour toutes les familles observées.
""")
        else:
            print(f"Commande inconnue: {cmd}")
            print("Utilisez 'python generer_tout.py help' pour l'aide")
    else:
        generer_toutes_galeries()
