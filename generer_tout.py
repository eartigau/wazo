#!/usr/bin/env python3
"""
Script principal pour générer toutes les galeries eBird v2.0
Bilingue français/anglais avec support taxonomie

Configuration: config.yaml
"""

import sys
import re
from pathlib import Path
from datetime import datetime, timedelta

try:
    import yaml
except ImportError:
    print("❌ PyYAML non installé. Exécutez: pip install pyyaml")
    sys.exit(1)

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    print("❌ Jinja2 non installé. Exécutez: pip install jinja2")
    sys.exit(1)

from generate_gallery import (
    EBirdGalleryGenerator, 
    verifier_tous_les_medias, 
    generer_description_groupe_fr, 
    mettre_au_pluriel, 
    formater_plage_dates,
    formater_date
)


# ============================================================================
# CHARGEMENT CONFIGURATION
# ============================================================================

CONFIG_FILE = "config.yaml"

def charger_config():
    """Charge la configuration depuis le fichier YAML"""
    if not Path(CONFIG_FILE).exists():
        print(f"❌ Fichier de configuration non trouvé: {CONFIG_FILE}")
        sys.exit(1)
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


# ============================================================================
# CONSTRUCTION DU MENU
# ============================================================================

def construire_menu(config, generator):
    """Construit la structure du menu de navigation"""
    
    # Récupérer les familles avec photos
    familles_avec_photos = generator.get_families_with_photos()
    
    menu = [
        {
            'name_fr': 'Accueil',
            'name_en': 'Home',
            'file_fr': config['site'].get('index', 'index.html'),
            'file_en': config['site'].get('index', 'index.html')
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
    
    # Lien Voyages (si configurés)
    voyages = config.get('voyages', [])
    if voyages:
        menu.append({
            'name_fr': 'Voyages',
            'name_en': 'Trips',
            'file_fr': 'voyages_index_fr.html',
            'file_en': 'voyages_index_en.html'
        })
    
    # Lien Familles (si des familles ont des photos)
    if familles_avec_photos:
        menu.append({
            'name_fr': 'Familles',
            'name_en': 'Families',
            'file_fr': 'familles_index_fr.html',
            'file_en': 'familles_index_en.html'
        })
    
    # Construire les données des familles pour la génération
    species_list = generator.get_species_list()
    
    # Grouper les espèces par famille pour les descriptions
    familles_especes = {}
    for sp in species_list:
        fam = sp['family'] or 'Unknown'
        if fam not in familles_especes:
            familles_especes[fam] = []
        familles_especes[fam].append(sp['common_name_fr'])
    
    familles_data = []
    for fam_info in familles_avec_photos:
        fam_code = fam_info['code']
        
        if fam_code == 'Unknown':
            continue
        
        # Générer description française
        noms_fr = familles_especes.get(fam_code, [])
        desc_fr = generer_description_groupe_fr(noms_fr)
        
        # Extraire description anglaise
        name_en_match = re.search(r'\(([^)]+)\)', fam_info['name'])
        desc_en = name_en_match.group(1) if name_en_match else ''
        
        file_id = f"gallery_{fam_code.lower()}"
        
        familles_data.append({
            'family_code': fam_code,
            'desc_fr': desc_fr,
            'desc_en': desc_en,
            'file_fr': f"{file_id}_fr.html",
            'file_en': f"{file_id}_en.html"
        })
    
    return menu, familles_data


# ============================================================================
# GÉNÉRATION
# ============================================================================

def generer_toutes_galeries():
    """Génère toutes les galeries configurées"""
    
    print("=" * 60)
    print("🐦 GÉNÉRATION DES GALERIES eBird v2.0")
    print("=" * 60)
    
    # Charger la configuration
    config = charger_config()
    
    # Extraire les chemins des fichiers
    fichiers = config.get('fichiers', {})
    CSV_FILE = fichiers.get('donnees_ebird', 'MyEBirdData.csv')
    TAXONOMY_FILE = fichiers.get('taxonomie', 'eBird_taxonomy_v2025.csv')
    MEDIA_CACHE = fichiers.get('cache_medias', 'media_cache.csv')
    TRADUCTIONS_FILE = fichiers.get('traductions_lieux', 'traductions_lieux.csv')
    
    # Options de génération
    generation = config.get('generation', {})
    VERIFIER_MEDIAS = generation.get('verifier_medias_en_ligne', False)
    LIMITE_DEFAUT = generation.get('limite_photos_defaut', 300)
    AJOUTS_RECENTS_MIN = generation.get('ajouts_recents_minimum', 50)
    LIMITE_FAMILLE = generation.get('limite_photos_famille', 500)
    
    # Templates
    GALLERY_TEMPLATE = 'gallery_template.html'
    SPECIES_LIST_TEMPLATE = 'species_list_template.html'
    
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
    
    # Construire le menu
    menu, familles_data = construire_menu(config, generator)
    
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
    
    trois_mois = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    
    photos_3_mois = generator.filter_observations(
        limit=9999,
        date_start=trois_mois,
        verifier_medias_en_ligne=VERIFIER_MEDIAS,
        sort_by='date'
    )
    
    if len(photos_3_mois) < AJOUTS_RECENTS_MIN:
        photos_recent = generator.filter_observations(
            limit=AJOUTS_RECENTS_MIN,
            verifier_medias_en_ligne=VERIFIER_MEDIAS,
            sort_by='date'
        )
        print(f"   (moins de {AJOUTS_RECENTS_MIN} photos en 3 mois, affichage des {AJOUTS_RECENTS_MIN} dernières)")
    else:
        photos_recent = photos_3_mois
        print(f"   ({len(photos_recent)} photos des 3 derniers mois)")
    
    if photos_recent:
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
            show_date_in_overlay=True
        )
        total_galeries += 1
    
    # ========================================
    # GALERIES GÉNÉRALES
    # ========================================
    galeries_generales = config.get('galeries_generales', [])
    if galeries_generales:
        print(f"\n📸 Galeries générales...")
        
        for galerie in galeries_generales:
            photos = generator.filter_observations(
                limit=galerie.get('limite', LIMITE_DEFAUT),
                countries=galerie.get('pays'),
                date_start=galerie.get('date_debut'),
                date_end=galerie.get('date_fin'),
                verifier_medias_en_ligne=VERIFIER_MEDIAS
            )
            
            if photos:
                generator.generate_gallery(
                    output_base=galerie['id'],
                    title_fr=galerie['nom_fr'],
                    title_en=galerie['nom_en'],
                    photos=photos,
                    template_file=GALLERY_TEMPLATE,
                    menu=menu,
                    gallery_id=galerie['id']
                )
                total_galeries += 1
    
    # ========================================
    # VOYAGES
    # ========================================
    voyages = config.get('voyages', [])
    if voyages:
        print(f"\n✈️ Galeries voyages...")
        
        voyages_index_data = []
        
        for voyage in voyages:
            photos = generator.filter_observations(
                limit=voyage.get('limite', LIMITE_DEFAUT),
                countries=voyage.get('pays'),
                regions=voyage.get('regions'),
                date_start=voyage.get('date_debut'),
                date_end=voyage.get('date_fin'),
                verifier_medias_en_ligne=VERIFIER_MEDIAS
            )
            
            if photos:
                # Dates min/max
                dates = [p.get('date_raw', '') for p in photos if p.get('date_raw')]
                if dates:
                    date_min = min(dates)
                    date_max = max(dates)
                    subtitle_fr = formater_plage_dates(date_min, date_max, 'fr')
                    subtitle_en = formater_plage_dates(date_min, date_max, 'en')
                else:
                    date_min = date_max = None
                    subtitle_fr = subtitle_en = None
                
                # Frontispice
                frontispice = voyage.get('frontispice', 'last')
                if frontispice == 'last':
                    frontispice_ml = photos[0]['ml_catalog_number']
                elif frontispice == 'first':
                    frontispice_ml = photos[-1]['ml_catalog_number']
                else:
                    frontispice_ml = frontispice
                
                # Espèces
                species_set = set(p.get('scientific_name', '') for p in photos)
                species_count = len(species_set)
                
                voyages_index_data.append({
                    'nom_fr': voyage['nom_fr'],
                    'nom_en': voyage['nom_en'],
                    'file_fr': f"{voyage['id']}_fr.html",
                    'file_en': f"{voyage['id']}_en.html",
                    'frontispice_ml': frontispice_ml,
                    'dates': True if date_min else False,
                    'dates_fr': subtitle_fr,
                    'dates_en': subtitle_en,
                    'photo_count': len(photos),
                    'species_count': species_count
                })
                
                generator.generate_gallery(
                    output_base=voyage['id'],
                    title_fr=voyage['nom_fr'],
                    title_en=voyage['nom_en'],
                    photos=photos,
                    template_file=GALLERY_TEMPLATE,
                    menu=menu,
                    gallery_id=voyage['id'],
                    subtitle_fr=subtitle_fr,
                    subtitle_en=subtitle_en
                )
                total_galeries += 1
        
        # Page index des voyages
        if voyages_index_data:
            print(f"\n📑 Page index des voyages...")
            today = datetime.now()
            update_date_fr = formater_date(today.strftime('%Y-%m-%d'), 'fr')
            update_date_en = formater_date(today.strftime('%Y-%m-%d'), 'en')
            
            env = Environment(loader=FileSystemLoader('.'))
            template = env.get_template('voyages_index_template.html')
            
            for lang in ['fr', 'en']:
                html = template.render(
                    lang=lang,
                    voyages=voyages_index_data,
                    menu=menu,
                    current_page=f'voyages_index_{lang}.html',
                    other_lang_page=f'voyages_index_{"en" if lang == "fr" else "fr"}.html',
                    update_date=True,
                    update_date_fr=update_date_fr,
                    update_date_en=update_date_en
                )
                with open(f'voyages_index_{lang}.html', 'w', encoding='utf-8') as f:
                    f.write(html)
            
            print(f"   ✓ voyages_index_fr.html / voyages_index_en.html ({len(voyages_index_data)} voyages)")
    
    # ========================================
    # FAMILLES
    # ========================================
    familles_icones = config.get('familles_icones', {}) or {}
    
    if familles_data:
        print(f"\n🦅 Galeries par famille ({len(familles_data)} familles)...")
        
        familles_index_data = []
        total_species_all = 0
        total_photos_all = 0
        
        for famille in familles_data:
            fam_code = famille['family_code']
            file_id = f"gallery_{fam_code.lower()}"
            
            photos = generator.filter_observations(
                limit=LIMITE_FAMILLE,
                families_list=[fam_code],
                verifier_medias_en_ligne=VERIFIER_MEDIAS,
                sort_by='taxonomy'
            )
            
            if photos:
                species_set = set(p.get('scientific_name', '') for p in photos)
                species_count = len(species_set)
                
                # Icône de la famille
                icone_override = familles_icones.get(fam_code, 'last')
                if icone_override == 'last':
                    photos_by_date = sorted(photos, key=lambda x: x.get('date_raw', ''), reverse=True)
                    icone_ml = photos_by_date[0]['ml_catalog_number'] if photos_by_date else photos[0]['ml_catalog_number']
                elif icone_override == 'first':
                    photos_by_date = sorted(photos, key=lambda x: x.get('date_raw', ''))
                    icone_ml = photos_by_date[0]['ml_catalog_number'] if photos_by_date else photos[0]['ml_catalog_number']
                else:
                    icone_ml = icone_override
                
                title_fr = f"Famille des {fam_code}s"
                title_en = f"{fam_code} Family"
                
                subtitle_fr = famille.get('desc_fr', '')
                subtitle_en = famille.get('desc_en', '')
                
                familles_index_data.append({
                    'code': fam_code,
                    'name_fr': subtitle_fr,
                    'name_en': subtitle_en,
                    'file_fr': f"{file_id}_fr.html",
                    'file_en': f"{file_id}_en.html",
                    'species_count': species_count,
                    'photo_count': len(photos),
                    'icone_ml': icone_ml
                })
                total_species_all += species_count
                total_photos_all += len(photos)
                
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
        
        # Page index des familles
        if familles_index_data:
            print(f"\n📑 Page index des familles...")
            today = datetime.now()
            update_date_fr = formater_date(today.strftime('%Y-%m-%d'), 'fr')
            update_date_en = formater_date(today.strftime('%Y-%m-%d'), 'en')
            
            env = Environment(loader=FileSystemLoader('.'))
            template = env.get_template('familles_index_template.html')
            
            for lang in ['fr', 'en']:
                html = template.render(
                    lang=lang,
                    familles=familles_index_data,
                    total_species=total_species_all,
                    total_photos=total_photos_all,
                    menu=menu,
                    current_page=f'familles_index_{lang}.html',
                    other_lang_page=f'familles_index_{"en" if lang == "fr" else "fr"}.html',
                    update_date=True,
                    update_date_fr=update_date_fr,
                    update_date_en=update_date_en
                )
                with open(f'familles_index_{lang}.html', 'w', encoding='utf-8') as f:
                    f.write(html)
            
            print(f"   ✓ familles_index_fr.html / familles_index_en.html ({len(familles_index_data)} familles)")
    
    # ========================================
    # RÉSUMÉ
    # ========================================
    print("\n" + "=" * 60)
    print("✅ GÉNÉRATION TERMINÉE")
    print(f"   📊 {total_galeries} galeries générées")
    print("=" * 60)


# ============================================================================
# VÉRIFICATION DES MÉDIAS
# ============================================================================

def verifier_medias():
    """Vérifie tous les médias et met à jour le cache"""
    config = charger_config()
    fichiers = config.get('fichiers', {})
    
    CSV_FILE = fichiers.get('donnees_ebird', 'MyEBirdData.csv')
    MEDIA_CACHE = fichiers.get('cache_medias', 'media_cache.csv')
    
    print("=" * 60)
    print("🔍 VÉRIFICATION DES MÉDIAS")
    print("=" * 60)
    
    verifier_tous_les_medias(CSV_FILE, MEDIA_CACHE)


# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

def afficher_aide():
    """Affiche l'aide"""
    print("""
🐦 Générateur de galeries eBird v2.0

Usage: python generer_tout.py [commande]

Commandes:
  (aucune)    Génère toutes les galeries
  verifier    Vérifie tous les médias et met à jour le cache
  help        Affiche cette aide

Configuration: config.yaml

Fichiers requis:
  - MyEBirdData.csv (export eBird)
  - eBird_taxonomy_v2025.csv (taxonomie)
  - config.yaml (configuration)

Étapes:
  1. Téléchargez vos données depuis https://ebird.org/downloadMyData
  2. Modifiez config.yaml selon vos besoins
  3. Exécutez: python generer_tout.py verifier (première fois)
  4. Exécutez: python generer_tout.py
""")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        commande = sys.argv[1].lower()
        if commande == 'verifier':
            verifier_medias()
        elif commande == 'help' or commande == '--help' or commande == '-h':
            afficher_aide()
        else:
            print(f"❌ Commande inconnue: {commande}")
            afficher_aide()
    else:
        generer_toutes_galeries()
