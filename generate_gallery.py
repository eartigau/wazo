#!/usr/bin/env python3
"""
Générateur de galeries eBird v2.0
- Support taxonomie eBird (filtrage par famille)
- Bilingue français/anglais
- Formatage des dates selon la langue
- Traduction des pays/régions
"""

import csv
import json
import os
import subprocess
import time
import re
from pathlib import Path
from datetime import datetime
from urllib.request import urlopen, Request
from jinja2 import Environment, FileSystemLoader


# ============================================================================
# CONFIGURATION
# ============================================================================

CACHE_FILE = "media_cache.csv"
TAXONOMY_FILE = "eBird_taxonomy_v2025.csv"
TRADUCTIONS_FILE = "traductions_lieux.csv"
SOUNDS_COMPILATION_FILE = "sons_par_espece.json"
SOUNDS_ASSETS_DIR = "sons_sonogrammes"
SOUNDS_PXPS = 80  # pixels par seconde du sonogramme ; doit correspondre au JS de sounds_template.html
REQUEST_TIMEOUT = 10
DELAY_BETWEEN_REQUESTS = 0.2

# Mois en français et anglais
MOIS_FR = ['', 'janvier', 'février', 'mars', 'avril', 'mai', 'juin', 
           'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']
MOIS_EN = ['', 'January', 'February', 'March', 'April', 'May', 'June',
           'July', 'August', 'September', 'October', 'November', 'December']

# Préfixes à ignorer pour extraire le type d'oiseau
PREFIXES_A_IGNORER = {'Petit', 'Grand', 'Petite', 'Grande'}

# Commentaires à enlever des noms de lieux
COMMENTAIRES_LIEUX = [
    '(restricted access)',
    '(do not report captive species)',
    '(captive birds)',
    '(no public access)',
    '(private property)',
    '(permit required)',
    '(accès restreint)',
    '(espèces captives)',
    '-- please bird from road only',
    '- please bird from road only',
    '--please bird from road only',
    '-please bird from road only',
]

# Substitutions exactes de noms de lieux (nom eBird -> nom affiché)
# La clé est le nom exact tel qu'il apparaît dans eBird (insensible à la casse)
SUBSTITUTIONS_LIEUX = {
    'Rapides Deschênes (incluant Parc)': 'Rapides Deschênes',
    'Rapides Deschenes (incluant Parc)': 'Rapides Deschênes',
    'Parque Bicentenario de Vitacura (no contar cisnes / don\'t count swans)': 'Parque Bicentenario de Vitacura',
}


def nettoyer_nom_lieu(location: str) -> str:
    """
    Nettoie un nom de lieu en enlevant les commentaires eBird.
    Ex: "Zoo de Granby (do not report captive species)" -> "Zoo de Granby"
    """
    if not location:
        return ''
    
    result = location
    
    # Appliquer les substitutions exactes
    for original, remplacement in SUBSTITUTIONS_LIEUX.items():
        if result.strip().lower() == original.lower():
            result = remplacement
            break
    
    # Enlever les commentaires connus (insensible à la casse)
    for commentaire in COMMENTAIRES_LIEUX:
        # Recherche insensible à la casse
        pattern = re.compile(re.escape(commentaire), re.IGNORECASE)
        result = pattern.sub('', result)
    
    # Enlever les commentaires génériques entre parenthèses à la fin
    # qui contiennent des mots-clés comme "restricted", "captive", "private", etc.
    keywords = r'restricted|captive|private|permit|access|restreint|report|do not|please'
    result = re.sub(rf'\s*\([^)]*(?:{keywords})[^)]*\)\s*', '', result, flags=re.IGNORECASE)
    
    # Enlever les commentaires avec double tiret
    result = re.sub(r'\s*--.*$', '', result)
    
    # Nettoyer les espaces multiples et trim
    result = re.sub(r'\s+', ' ', result).strip()
    
    # Enlever les tirets ou virgules en fin de chaîne
    result = re.sub(r'[\s,\-]+$', '', result).strip()
    
    return result


# ============================================================================
# FONCTIONS DE FORMATAGE
# ============================================================================

def normaliser_nom_scientifique(sci_name: str) -> str:
    """
    Normalise le nom scientifique en enlevant la sous-espèce.
    Ex: "Tringa semipalmata (semipalmata)" -> "Tringa semipalmata"
        "Tringa semipalmata inornata" -> "Tringa semipalmata"
    """
    if not sci_name:
        return ''
    # Enlever tout ce qui est entre parenthèses à la fin
    result = re.sub(r'\s*\([^)]+\)\s*$', '', sci_name).strip()
    # Enlever tout ce qui est entre crochets à la fin
    result = re.sub(r'\s*\[[^\]]+\]\s*$', '', result).strip()
    # Si plus de 2 mots, ne garder que les 2 premiers (genre + espèce)
    words = result.split()
    if len(words) > 2:
        result = ' '.join(words[:2])
    return result


def est_taxon_non_identifiable(sci_name: str, common_name: str = '') -> bool:
    """
    Vérifie si le taxon n'est pas identifiable au niveau de l'espèce.
    Ex: "duck sp.", "Anas platyrhynchos x rubripes", "Larus argentatus/glaucoides"
    """
    sci_lower = (sci_name or '').lower()
    common_lower = (common_name or '').lower()
    
    # Patterns indiquant un taxon non identifiable
    patterns = [
        ' sp.',           # spuh: "duck sp."
        ' sp$',           # fin en "sp"
        ' x ',            # hybrid: "Mallard x Black Duck"
        '/',              # slash: "Herring/Iceland Gull"
        'hybrid',         # hybrid
        ' or ',           # "X or Y"
        'undescribed',    # forme non décrite
        '(domestic',      # domestic form
        'domestic)',
    ]
    
    for pattern in patterns:
        if pattern in sci_lower or pattern in common_lower:
            return True
    
    return False


def normaliser_nom_commun(common_name: str) -> str:
    """
    Normalise le nom commun en enlevant la sous-espèce entre parenthèses.
    Ex: "Chevalier semipalmé (semipalmata)" -> "Chevalier semipalmé"
    """
    if not common_name:
        return ''
    return re.sub(r'\s*\([^)]+\)\s*$', '', common_name).strip()

def extraire_type_oiseau(nom_fr: str) -> str:
    """
    Extrait le type d'oiseau du nom français.
    Ex: "Grand Héron" -> "Héron"
        "Canard colvert" -> "Canard"
        "Petite Buse" -> "Buse"
    """
    if not nom_fr:
        return ''
    
    mots = nom_fr.split()
    if not mots:
        return ''
    
    # Si le premier mot est un préfixe à ignorer, prendre le second
    if mots[0] in PREFIXES_A_IGNORER and len(mots) > 1:
        return mots[1]
    
    return mots[0]


def mettre_au_pluriel(mot: str) -> str:
    """
    Met un mot français au pluriel.
    Gère les exceptions courantes pour les noms d'oiseaux.
    """
    if not mot:
        return ''
    
    mot_lower = mot.lower()
    
    # Déjà au pluriel (termine par s, x, z)
    if mot_lower.endswith(('s', 'x', 'z')):
        return mot
    
    # Cas spécial: mots composés avec "bleu" (merlebleu -> merlebleus)
    if mot_lower.endswith('bleu'):
        return mot + 's'
    
    # Exceptions en -ou qui prennent -x
    mots_ou_x = {'hibou', 'chou', 'bijou', 'caillou', 'genou', 'joujou', 'pou'}
    if mot_lower in mots_ou_x:
        return mot + 'x'
    
    # Mots en -eau prennent -x (corbeau, moineau, étourneau, etc.)
    if mot_lower.endswith('eau'):
        return mot + 'x'
    
    # Mots en -eu prennent -x (sauf bleu, pneu, émeu)
    if mot_lower.endswith('eu') and mot_lower not in {'bleu', 'pneu', 'émeu'}:
        return mot + 'x'
    
    # Mots en -al → -aux (cardinal → cardinaux, cheval → chevaux)
    # Exception: bal, carnaval, festival, chacal, etc. gardent -als
    mots_al_als = {'bal', 'carnaval', 'festival', 'chacal', 'récital', 'régal', 'cal', 'serval'}
    if mot_lower.endswith('al') and mot_lower not in mots_al_als:
        return mot[:-2] + 'aux'
    
    # Cas général: ajouter 's'
    return mot + 's'


def generer_description_groupe_fr(noms_fr: list) -> str:
    """
    Génère une description de groupe en français à partir des noms d'espèces.
    Prend les types les plus fréquents et les met au pluriel.
    Si plus de 5 types: affiche les 3 plus fréquents + "etc."
    Sinon: affiche jusqu'à 5 types par fréquence décroissante.
    """
    if not noms_fr:
        return ''
    
    # Compter les occurrences de chaque type
    type_counts = {}
    for nom in noms_fr:
        type_oiseau = extraire_type_oiseau(nom)
        if type_oiseau:
            type_counts[type_oiseau] = type_counts.get(type_oiseau, 0) + 1
    
    if not type_counts:
        return ''
    
    # Trier par fréquence décroissante
    sorted_types = sorted(type_counts.items(), key=lambda x: (-x[1], x[0]))
    
    # Mettre au pluriel
    if len(sorted_types) > 5:
        # Plus de 5 types: les 3 plus fréquents + etc.
        top_types = [mettre_au_pluriel(t[0]) for t in sorted_types[:3]]
        return ', '.join(top_types) + ', etc.'
    else:
        # 5 ou moins: tous les types
        types_list = [mettre_au_pluriel(t[0]) for t in sorted_types]
        
        if len(types_list) == 1:
            return types_list[0]
        elif len(types_list) == 2:
            return f"{types_list[0]} et {types_list[1]}"
        else:
            return ', '.join(types_list[:-1]) + ' et ' + types_list[-1]


def formater_jour_ordinal(jour: int, langue: str = 'fr') -> str:
    """
    Formate un jour avec son suffixe ordinal en superscript HTML.
    FR: 1 -> "1<sup>er</sup>", autres -> "2", "3", etc.
    EN: 1 -> "1<sup>st</sup>", 2 -> "2<sup>nd</sup>", 3 -> "3<sup>rd</sup>", autres -> "4<sup>th</sup>"
    """
    if langue == 'fr':
        if jour == 1:
            return f"1<sup>er</sup>"
        else:
            return str(jour)
    else:
        # Anglais: 1st, 2nd, 3rd, 4th-20th, 21st, 22nd, 23rd, 24th-30th, 31st
        if jour in (11, 12, 13):
            suffix = "th"
        elif jour % 10 == 1:
            suffix = "st"
        elif jour % 10 == 2:
            suffix = "nd"
        elif jour % 10 == 3:
            suffix = "rd"
        else:
            suffix = "th"
        return f"{jour}<sup>{suffix}</sup>"


def formater_date(date_str: str, langue: str = 'fr') -> str:
    """
    Formate une date YYYY-MM-DD en format lisible
    FR: 1er janvier 2025, 13 janvier 2025
    EN: January 1st, 2025, January 13th, 2025
    """
    if not date_str:
        return ''
    
    try:
        parts = date_str.split('-')
        if len(parts) != 3:
            return date_str
        
        annee, mois, jour = int(parts[0]), int(parts[1]), int(parts[2])
        jour_fmt = formater_jour_ordinal(jour, langue)
        
        if langue == 'fr':
            return f"{jour_fmt} {MOIS_FR[mois]} {annee}"
        else:
            return f"{MOIS_EN[mois]} {jour_fmt}, {annee}"
    except (ValueError, IndexError):
        return date_str


def formater_plage_dates(date_debut: str, date_fin: str, langue: str = 'fr') -> str:
    """
    Formate une plage de dates de manière intelligente.
    FR: "2 au 10 mars 2015" ou "1er mars au 15 avril 2015" ou "30 décembre 2024 au 1er janvier 2025"
    EN: "March 2nd-10th, 2015" ou "March 1st – April 15th, 2015"
    """
    if not date_debut or not date_fin:
        return ''
    
    try:
        p1 = date_debut.split('-')
        p2 = date_fin.split('-')
        if len(p1) != 3 or len(p2) != 3:
            return ''
        
        a1, m1, j1 = int(p1[0]), int(p1[1]), int(p1[2])
        a2, m2, j2 = int(p2[0]), int(p2[1]), int(p2[2])
        
        j1_fmt = formater_jour_ordinal(j1, langue)
        j2_fmt = formater_jour_ordinal(j2, langue)
        
        if langue == 'fr':
            if a1 == a2 and m1 == m2:
                # Même mois et année: "2 au 10 mars 2015" ou "1er au 10 mars 2015"
                return f"{j1_fmt} au {j2_fmt} {MOIS_FR[m2]} {a2}"
            elif a1 == a2:
                # Même année, mois différents: "1er mars au 15 avril 2015"
                return f"{j1_fmt} {MOIS_FR[m1]} au {j2_fmt} {MOIS_FR[m2]} {a2}"
            else:
                # Années différentes: "30 décembre 2024 au 1er janvier 2025"
                return f"{j1_fmt} {MOIS_FR[m1]} {a1} au {j2_fmt} {MOIS_FR[m2]} {a2}"
        else:
            if a1 == a2 and m1 == m2:
                # Same month and year: "March 2nd-10th, 2015"
                return f"{MOIS_EN[m1]} {j1_fmt}–{j2_fmt}, {a1}"
            elif a1 == a2:
                # Same year, different months: "March 1st – April 15th, 2015"
                return f"{MOIS_EN[m1]} {j1_fmt} – {MOIS_EN[m2]} {j2_fmt}, {a1}"
            else:
                # Different years: "December 30th, 2024 – January 1st, 2025"
                return f"{MOIS_EN[m1]} {j1_fmt}, {a1} – {MOIS_EN[m2]} {j2_fmt}, {a2}"
    except (ValueError, IndexError):
        return ''


def charger_traductions_lieux(fichier: str = TRADUCTIONS_FILE) -> dict:
    """Charge les traductions des pays/régions depuis le CSV"""
    traductions = {'fr': {}, 'en': {}}
    
    if not os.path.exists(fichier):
        print(f"⚠ Fichier de traductions non trouvé: {fichier}")
        return traductions
    
    try:
        with open(fichier, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = (row.get('code') or '').strip()
                if code and not code.startswith('#'):
                    traductions['fr'][code] = row.get('fr', code)
                    traductions['en'][code] = row.get('en', code)
    except Exception as e:
        print(f"⚠ Erreur lecture traductions: {e}")
    
    return traductions


def traduire_lieu(code: str, traductions: dict, langue: str = 'fr') -> str:
    """Traduit un code de lieu (pays ou région)"""
    if not code:
        return ''
    
    # Essayer le code complet d'abord
    if code in traductions.get(langue, {}):
        return traductions[langue][code]
    
    # Essayer juste le code pays (2 premières lettres)
    code_pays = code.split('-')[0] if '-' in code else code
    if code_pays in traductions.get(langue, {}):
        return traductions[langue][code_pays]
    
    return code


# ============================================================================
# TAXONOMIE eBird
# ============================================================================

class EBirdTaxonomy:
    """Gère la taxonomie eBird pour le filtrage par famille"""
    
    def __init__(self, taxonomy_file: str = TAXONOMY_FILE):
        self.taxonomy_file = taxonomy_file
        self.species = {}  # sci_name -> {data}
        self.families = {}  # family_code -> [sci_names]
        self.family_names = {}  # family_code -> family_full_name
        self.family_order = {}  # family_code -> min taxon_order (pour tri)
        
        self._load_taxonomy()
    
    def _extract_family_code(self, family_raw: str) -> str:
        """Extrait le code famille (ex: 'Anatidae' de 'Anatidae (Ducks...)')"""
        match = re.match(r'^(\w+)', family_raw)
        return match.group(1) if match else family_raw
    
    def _load_taxonomy(self):
        """Charge la taxonomie depuis le CSV"""
        if not os.path.exists(self.taxonomy_file):
            print(f"⚠ Fichier taxonomie non trouvé: {self.taxonomy_file}")
            return
        
        print(f"📚 Chargement taxonomie: {self.taxonomy_file}...")
        
        try:
            with open(self.taxonomy_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    category = row.get('CATEGORY', '')
                    # Charger les espèces et sous-espèces identifiables
                    if category not in ('species', 'issf'):
                        continue
                    
                    sci_name = row.get('SCI_NAME', '').strip()
                    family_raw = row.get('FAMILY', '').strip()
                    family_code = self._extract_family_code(family_raw)
                    taxon_order = int(row.get('TAXON_ORDER', 0) or 0)
                    
                    if sci_name:
                        # Pour les sous-espèces, normaliser le nom pour le lookup
                        sci_name_normalized = normaliser_nom_scientifique(sci_name)
                        
                        # Stocker avec le nom original
                        self.species[sci_name] = {
                            'taxon_order': taxon_order,
                            'common_name_en': normaliser_nom_commun(row.get('PRIMARY_COM_NAME', '')),
                            'sci_name': sci_name,
                            'sci_name_normalized': sci_name_normalized,
                            'order': row.get('ORDER', ''),
                            'family': family_code,
                            'family_full': family_raw,
                            'species_code': row.get('SPECIES_CODE', ''),
                            'category': category
                        }
                        
                        # Stocker aussi avec le nom normalisé (si différent et pas déjà présent)
                        if sci_name_normalized != sci_name and sci_name_normalized not in self.species:
                            self.species[sci_name_normalized] = self.species[sci_name]
                        
                        # Indexer par famille (seulement pour les espèces, pas les sous-espèces)
                        if category == 'species':
                            if family_code not in self.families:
                                self.families[family_code] = []
                                self.family_names[family_code] = family_raw
                                self.family_order[family_code] = taxon_order
                            self.families[family_code].append(sci_name)
                            
                            # Garder l'ordre le plus petit pour la famille
                            if taxon_order < self.family_order[family_code]:
                                self.family_order[family_code] = taxon_order
            
            num_species = sum(1 for v in self.species.values() if v.get('category') == 'species')
            print(f"   ✓ {num_species} espèces, {len(self.families)} familles")
            
        except Exception as e:
            print(f"⚠ Erreur chargement taxonomie: {e}")
    
    def get_species_in_family(self, family_code: str) -> list:
        """Retourne la liste des noms scientifiques d'une famille"""
        return self.families.get(family_code, [])
    
    def get_species_in_families(self, family_codes: list) -> set:
        """Retourne l'ensemble des noms scientifiques de plusieurs familles"""
        result = set()
        for fam in family_codes:
            result.update(self.families.get(fam, []))
        return result
    
    def get_species_info(self, sci_name: str) -> dict:
        """Retourne les infos d'une espèce par son nom scientifique"""
        # Essayer le nom direct
        if sci_name in self.species:
            return self.species[sci_name]
        # Essayer le nom normalisé
        normalized = normaliser_nom_scientifique(sci_name)
        if normalized in self.species:
            return self.species[normalized]
        return {}
    
    def get_family_name(self, family_code: str) -> str:
        """Retourne le nom complet d'une famille"""
        return self.family_names.get(family_code, family_code)
    
    def get_english_name(self, sci_name: str) -> str:
        """Retourne le nom anglais d'une espèce"""
        info = self.species.get(sci_name, {})
        return info.get('common_name_en', '')
    
    def get_taxon_order(self, sci_name: str) -> int:
        """Retourne l'ordre taxonomique d'une espèce"""
        info = self.species.get(sci_name, {})
        return info.get('taxon_order', 999999)
    
    def get_family_order(self, family_code: str) -> int:
        """Retourne l'ordre taxonomique d'une famille"""
        return self.family_order.get(family_code, 999999)


# ============================================================================
# VÉRIFICATION DES MÉDIAS
# ============================================================================

def _content_type_cdn(ml_catalog_number: str, suffix: str) -> str:
    """Retourne le Content-Type d'un suffixe d'asset Macaulay Library, ou '' si absent/erreur."""
    url = f"https://cdn.download.ams.birds.cornell.edu/api/v2/asset/{ml_catalog_number}/{suffix}"
    try:
        request = Request(url, method='HEAD')
        request.add_header('User-Agent', 'Mozilla/5.0 (compatible; eBird Gallery)')
        with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            return response.headers.get('Content-Type', '').lower()
    except Exception:
        return ''


def verifier_image_existe(ml_catalog_number: str) -> bool:
    """Vérifie si une image existe en taille 480 sur Macaulay Library (conservé pour compatibilité)."""
    return 'image' in _content_type_cdn(ml_catalog_number, '480')


def verifier_type_media(ml_catalog_number: str) -> str:
    """
    Détermine le type d'un média Macaulay Library : 'image', 'son', 'video' ou 'inconnu'.
    Essaie d'abord /480 (photos, cas le plus fréquent), puis /mp3 (sons), puis quelques
    suffixes vidéo courants (pas encore rencontrés dans ce catalogue, mais prévus).
    """
    if 'image' in _content_type_cdn(ml_catalog_number, '480'):
        return 'image'

    if 'audio' in _content_type_cdn(ml_catalog_number, 'mp3'):
        return 'son'

    for suffix in ('720p', '1080p', '480p', 'mp4'):
        content_type = _content_type_cdn(ml_catalog_number, suffix)
        if 'video' in content_type:
            return 'video'

    return 'inconnu'


def charger_cache(fichier_cache: str = CACHE_FILE) -> dict:
    """Charge le cache depuis le fichier CSV"""
    cache = {}
    
    if not os.path.exists(fichier_cache):
        return cache
    
    try:
        with open(fichier_cache, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ml_number = (row.get('ml_number') or '').strip()
                if ml_number and not ml_number.startswith('#'):
                    cache[ml_number] = {
                        'status': row.get('status') or 'inconnu',
                        'raison': row.get('raison') or '',
                        'date_verification': row.get('date_verification') or ''
                    }
    except Exception as e:
        print(f"⚠ Erreur lecture cache: {e}")
    
    return cache


def sauvegarder_cache(cache: dict, fichier_cache: str = CACHE_FILE):
    """Sauvegarde le cache dans le fichier CSV"""
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


def verifier_medias(ml_numbers: list, fichier_cache: str = CACHE_FILE,
                   forcer_verification: bool = False) -> dict:
    """Vérifie une liste de numéros ML et retourne leur statut"""
    cache = charger_cache(fichier_cache)
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    images = []
    exclus = []
    a_verifier = []
    
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
    
    if a_verifier:
        print(f"\n🔍 Vérification de {len(a_verifier)} médias...")

        raisons = {
            'image': 'vérifié automatiquement',
            'son': 'pas d\'image 480 disponible, audio détecté',
            'video': 'vidéo détectée',
            'inconnu': 'type non identifié (ni image, ni audio, ni vidéo)'
        }

        for i, ml_number in enumerate(a_verifier, 1):
            if i % 50 == 0:
                print(f"  ... {i}/{len(a_verifier)}")

            type_media = verifier_type_media(ml_number)

            cache[ml_number] = {
                'status': type_media,
                'raison': raisons[type_media],
                'date_verification': date_now
            }
            if type_media == 'image':
                images.append(ml_number)
            else:
                exclus.append(ml_number)

            time.sleep(DELAY_BETWEEN_REQUESTS)
        
        sauvegarder_cache(cache, fichier_cache)
    
    return {'images': images, 'exclus': exclus, 'cache': cache}


# ============================================================================
# DONNÉES DU FEED PLEIN ÉCRAN (fichier JSON séparé, chargé en fetch() côté client)
# ============================================================================

def construire_donnees_feed(photos: list) -> list:
    """
    Construit la liste de dictionnaires pour le JSON du feed plein écran, avec les mêmes
    champs que l'ancien bloc JS en ligne dans gallery_feed_template.html (photosData).
    """
    data = []
    for photo in photos:
        lat = photo.get('latitude')
        lng = photo.get('longitude')
        data.append({
            'ml': photo.get('ml_catalog_number', ''),
            'name_fr': photo.get('common_name_fr', ''),
            'name_en': photo.get('common_name_en', ''),
            'scientific': photo.get('scientific_name', ''),
            'location': photo.get('location', '') or '',
            'location_fr': photo.get('location_full_fr', '') or '',
            'location_en': photo.get('location_full_en', '') or '',
            'date_fr': photo.get('date_fr', ''),
            'date_en': photo.get('date_en', ''),
            'lat': lat if lat else None,
            'lng': lng if lng else None,
            'checklist_id': photo.get('checklist_id', ''),
            'iucn_status': photo.get('iucn_status', '') or '',
        })
    return data


def ecrire_feed_json(photos: list, chemin_fichier: str):
    """Écrit le JSON des données photo du feed plein écran (une fois par langue, mêmes données)."""
    with open(chemin_fichier, 'w', encoding='utf-8') as f:
        json.dump(construire_donnees_feed(photos), f, ensure_ascii=False, separators=(',', ':'))


# ============================================================================
# CLASSE PRINCIPALE
# ============================================================================

class EBirdGalleryGenerator:
    """Générateur de galeries photo bilingue avec support taxonomie"""
    
    def __init__(self, csv_file: str, 
                 taxonomy_file: str = TAXONOMY_FILE,
                 media_cache_file: str = CACHE_FILE,
                 traductions_file: str = TRADUCTIONS_FILE):
        
        self.csv_file = csv_file
        self.media_cache_file = media_cache_file
        self.observations = []
        self.media_cache = {}
        
        # Charger la taxonomie
        self.taxonomy = EBirdTaxonomy(taxonomy_file)
        
        # Charger les traductions
        self.traductions = charger_traductions_lieux(traductions_file)
        
        self._load_data()
        self._load_media_cache()
    
    def _load_data(self):
        """Charge les données du fichier CSV eBird"""
        print(f"📂 Chargement de {self.csv_file}...")

        with open(self.csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ml_numbers = row.get('ML Catalog Numbers') or ''
                ml_numbers = ml_numbers.strip()
                if ml_numbers:
                    # Nettoyer les noms dès la lecture, une fois pour toutes : enlever tout
                    # segment entre parenthèses du nom commun et entre crochets/parenthèses
                    # du nom scientifique, ex. "Cormoran impérial (groupe atriceps)" ->
                    # "Cormoran impérial". Tout le reste du code lit ensuite des noms déjà propres.
                    if row.get('Common Name'):
                        row['Common Name'] = normaliser_nom_commun(row['Common Name'])
                    if row.get('Scientific Name'):
                        row['Scientific Name'] = normaliser_nom_scientifique(row['Scientific Name'])
                    self.observations.append(row)

        print(f"   ✓ {len(self.observations)} observations avec médias")
    
    def _load_media_cache(self):
        """Charge le cache des médias vérifiés"""
        self.media_cache = charger_cache(self.media_cache_file)
        if self.media_cache:
            images = sum(1 for v in self.media_cache.values() if v['status'] == 'image')
            sons = sum(1 for v in self.media_cache.values() if v['status'] == 'son')
            print(f"   ✓ Cache médias: {images} photos, {sons} sons")
    
    def _parse_coord(self, value) -> float:
        """Parse une coordonnée en float"""
        if not value:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _build_photo_data(self, obs: dict, ml: str) -> dict:
        """Construit les données d'une photo avec traductions"""
        sci_name = obs.get('Scientific Name', '').strip()
        taxon_info = self.taxonomy.get_species_info(sci_name)
        
        # Infos lieu (nettoyer les commentaires eBird)
        state_code = obs.get('State/Province') or ''
        location = nettoyer_nom_lieu(obs.get('Location') or '')
        country_code = state_code.split('-')[0] if '-' in state_code else state_code
        
        region_fr = traduire_lieu(state_code, self.traductions, 'fr')
        region_en = traduire_lieu(state_code, self.traductions, 'en')
        country_fr = traduire_lieu(country_code, self.traductions, 'fr')
        country_en = traduire_lieu(country_code, self.traductions, 'en')
        
        # Construire lieu complet
        if region_fr and country_fr and region_fr != country_fr:
            lieu_complet_fr = f"{location}, {region_fr}, {country_fr}" if location else f"{region_fr}, {country_fr}"
        else:
            lieu_complet_fr = f"{location}, {country_fr}" if location and country_fr else location or country_fr
        
        if region_en and country_en and region_en != country_en:
            lieu_complet_en = f"{location}, {region_en}, {country_en}" if location else f"{region_en}, {country_en}"
        else:
            lieu_complet_en = f"{location}, {country_en}" if location and country_en else location or country_en
        
        return {
            'ml_catalog_number': ml,
            'common_name_fr': obs.get('Common Name') or 'Inconnu',
            'common_name_en': taxon_info.get('common_name_en') or obs.get('Common Name') or 'Unknown',
            'scientific_name': sci_name,
            'family': taxon_info.get('family', ''),
            'family_full': taxon_info.get('family_full', ''),
            'taxon_order': taxon_info.get('taxon_order', 999999),
            'location': location,
            'location_full_fr': lieu_complet_fr,
            'location_full_en': lieu_complet_en,
            'region_fr': region_fr,
            'region_en': region_en,
            'country_fr': country_fr,
            'country_en': country_en,
            'state_code': state_code,
            'date_raw': obs.get('Date') or '',
            'date_fr': formater_date(obs.get('Date'), 'fr'),
            'date_en': formater_date(obs.get('Date'), 'en'),
            'latitude': self._parse_coord(obs.get('Latitude')),
            'longitude': self._parse_coord(obs.get('Longitude')),
            'checklist_id': obs.get('Submission ID') or ''
        }
    
    def get_species_list(self, curation: dict = None) -> list:
        """
        Retourne la liste de toutes les espèces photographiées
        triée par ordre phylogénétique avec infos famille, lieu et coordonnées.
        Filtre les espèces qui n'ont que des sons (pas d'image valide).
        Fusionne les sous-espèces avec l'espèce principale.
        Exclut les taxons non identifiables (sp., slash, hybrid).
        Collecte TOUTES les photos de chaque espèce.
        
        Args:
            curation: Dict {ml_number: 'best'|'include'|'reject'} pour filtrer/sélectionner
        """
        species_data = {}  # sci_name_normalized -> {'info': {...}, 'photos': [...]}
        
        for obs in self.observations:
            sci_name_raw = obs.get('Scientific Name', '').strip()
            common_name_raw = obs.get('Common Name', '').strip()
            if not sci_name_raw:
                continue
            
            # Exclure les taxons non identifiables au niveau espèce
            if est_taxon_non_identifiable(sci_name_raw, common_name_raw):
                continue
            
            # Normaliser le nom (enlever sous-espèce)
            sci_name = normaliser_nom_scientifique(sci_name_raw)
            
            obs_date = obs.get('Date', '')
            ml_string = obs.get('ML Catalog Numbers') or ''
            ml_numbers = [n.strip() for n in ml_string.replace(',', ' ').split() if n.strip()]
            
            # Collecter TOUTES les images valides de cette observation
            for ml in ml_numbers:
                if ml not in self.media_cache or self.media_cache[ml]['status'] != 'image':
                    continue
                
                # Vérifier la curation (exclure les 'reject')
                if curation and curation.get(ml) == 'reject':
                    continue
                
                # Infos lieu (nettoyer les commentaires eBird)
                state_code = obs.get('State/Province') or ''
                location = nettoyer_nom_lieu(obs.get('Location') or '')
                country_code = state_code.split('-')[0] if '-' in state_code else state_code
                
                region_fr = traduire_lieu(state_code, self.traductions, 'fr')
                region_en = traduire_lieu(state_code, self.traductions, 'en')
                country_fr = traduire_lieu(country_code, self.traductions, 'fr')
                country_en = traduire_lieu(country_code, self.traductions, 'en')
                
                # Lieu complet
                if region_fr and country_fr and region_fr != country_fr:
                    lieu_complet_fr = f"{location}, {region_fr}, {country_fr}" if location else f"{region_fr}, {country_fr}"
                else:
                    lieu_complet_fr = f"{location}, {country_fr}" if location and country_fr else location or country_fr
                
                if region_en and country_en and region_en != country_en:
                    lieu_complet_en = f"{location}, {region_en}, {country_en}" if location else f"{region_en}, {country_en}"
                else:
                    lieu_complet_en = f"{location}, {country_en}" if location and country_en else location or country_en
                
                # Statut de curation
                curation_status = curation.get(ml, 'include') if curation else 'include'
                
                photo_data = {
                    'ml_catalog_number': ml,
                    'date_raw': obs_date,
                    'date_fr': formater_date(obs_date, 'fr'),
                    'date_en': formater_date(obs_date, 'en'),
                    'location': location,
                    'location_full_fr': lieu_complet_fr,
                    'location_full_en': lieu_complet_en,
                    'latitude': self._parse_coord(obs.get('Latitude')),
                    'longitude': self._parse_coord(obs.get('Longitude')),
                    'checklist_id': obs.get('Submission ID') or '',
                    'curation_status': curation_status
                }
                
                if sci_name not in species_data:
                    taxon_info = self.taxonomy.get_species_info(sci_name)
                    # Normaliser aussi le nom commun
                    common_name_fr = normaliser_nom_commun(obs.get('Common Name', ''))
                    common_name_en = normaliser_nom_commun(taxon_info.get('common_name_en') or obs.get('Common Name', ''))
                    
                    species_data[sci_name] = {
                        'info': {
                            'sci_name': sci_name,
                            'common_name_fr': common_name_fr,
                            'common_name_en': common_name_en,
                            'taxon_order': taxon_info.get('taxon_order', 999999),
                            'family': taxon_info.get('family', ''),
                            'family_full': taxon_info.get('family_full', '')
                        },
                        'photos': []
                    }
                
                species_data[sci_name]['photos'].append(photo_data)
        
        # Construire la liste finale
        species_list = []
        for sci_name, data in species_data.items():
            info = data['info']
            photos = data['photos']
            
            if not photos:
                continue
            
            # Sélectionner la photo représentative:
            # 1. Photo 'best' la plus récente
            # 2. Sinon, photo la plus récente
            best_photos = [p for p in photos if p.get('curation_status') == 'best']
            if best_photos:
                best_photos.sort(key=lambda x: x['date_raw'], reverse=True)
                representative = best_photos[0]
            else:
                photos.sort(key=lambda x: x['date_raw'], reverse=True)
                representative = photos[0]
            
            # Trier toutes les photos: best d'abord (par date desc), puis autres (par date desc)
            best_sorted = sorted([p for p in photos if p.get('curation_status') == 'best'], 
                                key=lambda x: x['date_raw'], reverse=True)
            other_sorted = sorted([p for p in photos if p.get('curation_status') != 'best'], 
                                 key=lambda x: x['date_raw'], reverse=True)
            all_photos_sorted = best_sorted + other_sorted
            
            species_list.append({
                'sci_name': info['sci_name'],
                'common_name_fr': info['common_name_fr'],
                'common_name_en': info['common_name_en'],
                'taxon_order': info['taxon_order'],
                'family': info['family'],
                'family_full': info['family_full'],
                # Photo représentative (best ou plus récente)
                'ml_catalog_number': representative['ml_catalog_number'],
                'date_raw': representative['date_raw'],
                'date_fr': representative['date_fr'],
                'date_en': representative['date_en'],
                'location_full_fr': representative['location_full_fr'],
                'location_full_en': representative['location_full_en'],
                'latitude': representative['latitude'],
                'longitude': representative['longitude'],
                'checklist_id': representative['checklist_id'],
                # Toutes les photos (triées: best d'abord)
                'all_photos': all_photos_sorted,
                'photo_count': len(all_photos_sorted)
            })
        
        # Trier par ordre phylogénétique
        species_list.sort(key=lambda x: x['taxon_order'])
        
        return species_list
    
    def get_families_with_photos(self) -> list:
        """Retourne la liste des familles qui ont des photos, triées par ordre phylogénétique"""
        species_list = self.get_species_list()
        families = {}
        
        for sp in species_list:
            fam = sp['family']
            if fam and fam not in families:
                families[fam] = {
                    'code': fam,
                    'name': sp['family_full'],
                    'order': self.taxonomy.get_family_order(fam)
                }
        
        return sorted(families.values(), key=lambda x: x['order'])
    
    def get_sounds_list(self, curation: dict = None) -> list:
        """
        Retourne la liste de tous les sons enregistrés,
        triée par ordre phylogénétique avec infos espèce, lieu et coordonnées.
        Pour chaque espèce avec des sons, inclut aussi la meilleure photo si disponible.
        
        Args:
            curation: Dict {ml_number: 'best'|'include'|'reject'} pour filtrer
        """
        # D'abord, collecter les meilleures photos par espèce
        species_best_photo = {}  # sci_name -> ml_number de la meilleure photo
        species_list = self.get_species_list(curation=curation)
        for sp in species_list:
            species_best_photo[sp['sci_name']] = sp['ml_catalog_number']
        
        # Collecter tous les sons
        sounds_data = {}  # sci_name_normalized -> {'info': {...}, 'sounds': [...]}
        
        for obs in self.observations:
            sci_name_raw = obs.get('Scientific Name', '').strip()
            common_name_raw = obs.get('Common Name', '').strip()
            if not sci_name_raw:
                continue
            
            # Exclure les taxons non identifiables au niveau espèce
            if est_taxon_non_identifiable(sci_name_raw, common_name_raw):
                continue
            
            # Normaliser le nom (enlever sous-espèce)
            sci_name = normaliser_nom_scientifique(sci_name_raw)
            
            obs_date = obs.get('Date', '')
            ml_string = obs.get('ML Catalog Numbers') or ''
            ml_numbers = [n.strip() for n in ml_string.replace(',', ' ').split() if n.strip()]
            
            # Collecter les SONS de cette observation
            for ml in ml_numbers:
                # Vérifier que c'est un son (pas une image)
                if ml not in self.media_cache or self.media_cache[ml]['status'] != 'son':
                    continue
                
                # Vérifier la curation (exclure les 'reject')
                if curation and curation.get(ml) == 'reject':
                    continue
                
                # Infos lieu
                state_code = obs.get('State/Province') or ''
                location = nettoyer_nom_lieu(obs.get('Location') or '')
                country_code = state_code.split('-')[0] if '-' in state_code else state_code
                
                region_fr = traduire_lieu(state_code, self.traductions, 'fr')
                region_en = traduire_lieu(state_code, self.traductions, 'en')
                country_fr = traduire_lieu(country_code, self.traductions, 'fr')
                country_en = traduire_lieu(country_code, self.traductions, 'en')
                
                # Lieu complet
                if region_fr and country_fr and region_fr != country_fr:
                    lieu_complet_fr = f"{location}, {region_fr}, {country_fr}" if location else f"{region_fr}, {country_fr}"
                else:
                    lieu_complet_fr = f"{location}, {country_fr}" if location and country_fr else location or country_fr
                
                if region_en and country_en and region_en != country_en:
                    lieu_complet_en = f"{location}, {region_en}, {country_en}" if location else f"{region_en}, {country_en}"
                else:
                    lieu_complet_en = f"{location}, {country_en}" if location and country_en else location or country_en
                
                # Statut de curation
                curation_status = curation.get(ml, 'include') if curation else 'include'
                
                sound_data = {
                    'ml_catalog_number': ml,
                    'date_raw': obs_date,
                    'date_fr': formater_date(obs_date, 'fr'),
                    'date_en': formater_date(obs_date, 'en'),
                    'location': location,
                    'location_full_fr': lieu_complet_fr,
                    'location_full_en': lieu_complet_en,
                    'latitude': self._parse_coord(obs.get('Latitude')),
                    'longitude': self._parse_coord(obs.get('Longitude')),
                    'checklist_id': obs.get('Submission ID') or '',
                    'curation_status': curation_status
                }
                
                if sci_name not in sounds_data:
                    taxon_info = self.taxonomy.get_species_info(sci_name)
                    common_name_fr = normaliser_nom_commun(obs.get('Common Name', ''))
                    common_name_en = normaliser_nom_commun(taxon_info.get('common_name_en') or obs.get('Common Name', ''))
                    
                    sounds_data[sci_name] = {
                        'info': {
                            'sci_name': sci_name,
                            'common_name_fr': common_name_fr,
                            'common_name_en': common_name_en,
                            'taxon_order': taxon_info.get('taxon_order', 999999),
                            'family': taxon_info.get('family', ''),
                            'family_full': taxon_info.get('family_full', ''),
                            'best_photo_ml': species_best_photo.get(sci_name)  # Photo de l'espèce si disponible
                        },
                        'sounds': []
                    }
                
                sounds_data[sci_name]['sounds'].append(sound_data)
        
        # Construire la liste finale
        sounds_list = []
        for sci_name, data in sounds_data.items():
            info = data['info']
            sounds = data['sounds']
            
            if not sounds:
                continue
            
            # Trier les sons: best d'abord, puis par date
            best_sounds = sorted([s for s in sounds if s.get('curation_status') == 'best'], 
                                key=lambda x: x['date_raw'], reverse=True)
            other_sounds = sorted([s for s in sounds if s.get('curation_status') != 'best'], 
                                 key=lambda x: x['date_raw'], reverse=True)
            all_sounds_sorted = best_sounds + other_sounds
            
            sounds_list.append({
                'sci_name': info['sci_name'],
                'common_name_fr': info['common_name_fr'],
                'common_name_en': info['common_name_en'],
                'taxon_order': info['taxon_order'],
                'family': info['family'],
                'family_full': info['family_full'],
                'best_photo_ml': info['best_photo_ml'],
                'all_sounds': all_sounds_sorted,
                'sound_count': len(all_sounds_sorted)
            })
        
        # Trier par ordre phylogénétique
        sounds_list.sort(key=lambda x: x['taxon_order'])
        
        return sounds_list
    
    def generate_sounds_gallery(self,
                               output_base: str = 'sounds_gallery',
                               template_file: str = 'sounds_template.html',
                               menu: list = None,
                               curation: dict = None):
        """Génère la galerie des sons"""
        
        output_fr = f"{output_base}_fr.html"
        output_en = f"{output_base}_en.html"
        
        sounds_list = self.get_sounds_list(curation=curation)

        # Compter le total de sons
        total_sounds = sum(sp['sound_count'] for sp in sounds_list)

        # Générer (ou réutiliser depuis le cache disque) le sonogramme de chaque son
        print(f"   🎙️ Sonogrammes ({total_sounds} sons)...")
        for sp in sounds_list:
            for sound in sp['all_sounds']:
                resultat = generer_sonogramme(sound['ml_catalog_number'])
                sound['sonogram_path'] = resultat['path'] if resultat else None
                sound['duration'] = resultat['duration'] if resultat else None

        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template(template_file)
        
        # Date de mise à jour
        today = datetime.now()
        heure = today.strftime('%-Hh%M')
        update_date_fr = formater_date(today.strftime('%Y-%m-%d'), 'fr') + f' ({heure})'
        update_date_en = formater_date(today.strftime('%Y-%m-%d'), 'en') + f' ({heure})'
        
        # Version française
        html_fr = template.render(
            lang='fr',
            species_list=sounds_list,
            total_species=len(sounds_list),
            total_sounds=total_sounds,
            menu=menu or [],
            current_page=output_fr,
            other_lang_page=output_en,
            update_date=True,
            update_date_fr=update_date_fr,
            update_date_en=update_date_en
        )
        
        with open(output_fr, 'w', encoding='utf-8') as f:
            f.write(html_fr)
        
        # Version anglaise
        html_en = template.render(
            lang='en',
            species_list=sounds_list,
            total_species=len(sounds_list),
            total_sounds=total_sounds,
            menu=menu or [],
            current_page=output_en,
            other_lang_page=output_fr,
            update_date=True,
            update_date_fr=update_date_fr,
            update_date_en=update_date_en
        )
        
        with open(output_en, 'w', encoding='utf-8') as f:
            f.write(html_en)
        
        print(f"   ✓ {output_fr} / {output_en} ({total_sounds} sons, {len(sounds_list)} espèces)")
        return output_fr, output_en
    
    def filter_observations(self, 
                           limit: int = None,
                           species: list = None,
                           family: str = None,
                           families_list: list = None,
                           countries: list = None,
                           regions: list = None,
                           date_start: str = None,
                           date_end: str = None,
                           verifier_medias_en_ligne: bool = False,
                           sort_by: str = 'date',
                           curation: dict = None,
                           prioritize_best: bool = True) -> list:
        """
        Filtre les observations selon les critères
        
        Args:
            limit: Nombre maximum de photos
            species: Liste de noms d'espèces
            family: Code famille taxonomique (ex: 'Anatidae')
            families_list: Liste de codes familles
            countries: Liste de codes pays (ex: ['CA-QC', 'US-FL'])
            regions: Liste de codes région
            date_start: Date de début (YYYY-MM-DD)
            date_end: Date de fin (YYYY-MM-DD)
            verifier_medias_en_ligne: Si True, vérifie les médias non-cachés
            sort_by: 'date' (chronologique inverse) ou 'taxonomy' (ordre taxonomique)
            curation: Dict {ml_number: 'best'|'include'|'reject'} pour filtrer/trier
            prioritize_best: Si True, met les photos 'best' en premier (défaut: True)
        """
        photos = []
        ml_a_verifier = []
        
        # Si famille spécifiée, obtenir la liste des espèces
        family_species = set()
        if family:
            family_species = set(self.taxonomy.get_species_in_family(family))
        if families_list:
            family_species = self.taxonomy.get_species_in_families(families_list)
        
        for obs in self.observations:
            sci_name = obs.get('Scientific Name', '').strip()
            common_name = obs.get('Common Name', '').strip()
            
            # Exclure les taxons non identifiables au niveau espèce
            if est_taxon_non_identifiable(sci_name, common_name):
                continue
            
            # Filtre par espèce
            if species and common_name not in species:
                continue
            
            # Filtre par famille (via taxonomie) - utiliser le nom normalisé
            sci_name_normalized = normaliser_nom_scientifique(sci_name)
            if family_species and sci_name_normalized not in family_species:
                continue
            
            # Filtre par pays/région
            if countries:
                state_code = obs.get('State/Province') or ''
                # Extraire le code pays (partie avant le tiret, ou le code entier)
                obs_country = state_code.split('-')[0] if '-' in state_code else state_code
                # Vérifier si le pays correspond exactement OU si c'est une région spécifique demandée
                if not any(c == obs_country or state_code == c or state_code.startswith(c + '-') for c in countries):
                    continue
            
            if regions:
                region = obs.get('State/Province') or ''
                if region not in regions:
                    continue
            
            # Filtre par date
            if date_start or date_end:
                obs_date = obs.get('Date') or ''
                if date_start and obs_date < date_start:
                    continue
                if date_end and obs_date > date_end:
                    continue
            
            # Extraire les numéros ML
            ml_string = obs.get('ML Catalog Numbers') or ''
            ml_numbers = [n.strip() for n in ml_string.replace(',', ' ').split() if n.strip()]
            
            for ml in ml_numbers:
                # Vérifier le cache
                if ml in self.media_cache:
                    if self.media_cache[ml]['status'] != 'image':
                        continue
                else:
                    ml_a_verifier.append(ml)
                
                photo = self._build_photo_data(obs, ml)
                
                # Ajouter le statut de curation
                if curation:
                    photo['curation_status'] = curation.get(ml, 'include')
                else:
                    photo['curation_status'] = 'include'
                
                photos.append(photo)
        
        # Vérifier les médias non-cachés
        if verifier_medias_en_ligne and ml_a_verifier:
            print(f"\n🔍 Vérification de {len(ml_a_verifier)} nouveaux médias...")
            resultats = verifier_medias(ml_a_verifier, self.media_cache_file)
            self.media_cache = charger_cache(self.media_cache_file)
            
            photos = [p for p in photos 
                     if p['ml_catalog_number'] in resultats['images'] 
                     or (p['ml_catalog_number'] in self.media_cache 
                         and self.media_cache[p['ml_catalog_number']]['status'] == 'image')]
        
        # Filtrer les photos rejetées par curation
        if curation:
            photos = [p for p in photos if p.get('curation_status') != 'reject']
        
        # Supprimer les doublons
        seen = set()
        unique_photos = []
        for photo in photos:
            if photo['ml_catalog_number'] not in seen:
                seen.add(photo['ml_catalog_number'])
                unique_photos.append(photo)
        
        # Trier selon le mode choisi
        if sort_by == 'taxonomy':
            # Tri par ordre taxonomique, avec date décroissante à l'intérieur de chaque espèce
            # et les 'best' en premier dans chaque groupe (si prioritize_best)
            
            # D'abord trier par date décroissante
            unique_photos.sort(key=lambda x: x.get('date_raw', ''), reverse=True)
            
            # Puis par statut best (si prioritize_best)
            if prioritize_best:
                unique_photos.sort(key=lambda x: 0 if x.get('curation_status') == 'best' else 1)
            
            # Puis tri stable par taxon_order (préserve l'ordre dans chaque groupe)
            unique_photos.sort(key=lambda x: x.get('taxon_order', 999999))
        else:
            # Tri par date décroissante (défaut)
            if prioritize_best:
                # Séparer best et autres, best en premier
                best_photos = [p for p in unique_photos if p.get('curation_status') == 'best']
                other_photos = [p for p in unique_photos if p.get('curation_status') != 'best']
                best_photos.sort(key=lambda x: x.get('date_raw', ''), reverse=True)
                other_photos.sort(key=lambda x: x.get('date_raw', ''), reverse=True)
                unique_photos = best_photos + other_photos
            else:
                # Tri simple par date décroissante, sans priorité aux best
                unique_photos.sort(key=lambda x: x.get('date_raw', ''), reverse=True)
        
        if limit:
            unique_photos = unique_photos[:limit]
        
        return unique_photos
    
    def get_best_photos(self, curation: dict = None) -> list:
        """
        Retourne toutes les photos marquées comme 'best' dans la curation,
        triées par ordre taxonomique.
        
        Args:
            curation: Dict {ml_number: 'best'|'include'|'reject'}
        
        Returns:
            Liste des photos avec statut 'best'
        """
        if not curation:
            return []
        
        # Obtenir les ML numbers des photos best
        best_ml_numbers = {ml for ml, status in curation.items() if status == 'best'}
        
        if not best_ml_numbers:
            return []
        
        photos = []
        
        for obs in self.observations:
            sci_name = obs.get('Scientific Name', '').strip()
            common_name = obs.get('Common Name', '').strip()
            
            # Exclure les taxons non identifiables
            if est_taxon_non_identifiable(sci_name, common_name):
                continue
            
            ml_string = obs.get('ML Catalog Numbers') or ''
            ml_numbers = [n.strip() for n in ml_string.replace(',', ' ').split() if n.strip()]
            
            for ml in ml_numbers:
                if ml in best_ml_numbers:
                    # Vérifier que c'est une image
                    if ml in self.media_cache and self.media_cache[ml]['status'] == 'image':
                        photo = self._build_photo_data(obs, ml)
                        photo['curation_status'] = 'best'
                        photos.append(photo)
        
        # Supprimer les doublons
        seen = set()
        unique_photos = []
        for photo in photos:
            if photo['ml_catalog_number'] not in seen:
                seen.add(photo['ml_catalog_number'])
                unique_photos.append(photo)
        
        # Trier par ordre taxonomique
        unique_photos.sort(key=lambda x: x.get('taxon_order', 999999))
        
        return unique_photos
    
    def generate_gallery(self,
                        output_base: str,
                        title_fr: str,
                        title_en: str,
                        photos: list,
                        template_file: str = 'gallery_template.html',
                        menu: list = None,
                        gallery_id: str = None,
                        subtitle_fr: str = None,
                        subtitle_en: str = None,
                        species_count: int = None,
                        show_date_in_overlay: bool = False,
                        trip_locations: list = None,
                        back_link_fr: str = None,
                        back_link_en: str = None,
                        back_text_fr: str = None,
                        back_text_en: str = None,
                        iucn_statuts: dict = None):
        """
        Génère les pages HTML de galerie en français et anglais
        
        Args:
            output_base: Nom de base sans extension (ex: 'gallery_anatidae')
            title_fr: Titre en français
            title_en: Titre en anglais
            photos: Liste de photos
            template_file: Fichier template Jinja2
            menu: Structure du menu
            gallery_id: ID unique pour cette galerie (pour liens depuis liste espèces)
            subtitle_fr: Sous-titre en français (optionnel)
            subtitle_en: Sous-titre en anglais (optionnel)
            species_count: Nombre d'espèces (optionnel, pour affichage)
            show_date_in_overlay: Afficher la date dans l'overlay (défaut: False)
            trip_locations: Liste de lieux pour la carte du voyage (optionnel)
            back_link_fr: Lien de retour version française (optionnel)
            back_link_en: Lien de retour version anglaise (optionnel)
            back_text_fr: Texte du lien de retour en français (optionnel)
            back_text_en: Texte du lien de retour en anglais (optionnel)
            iucn_statuts: Dictionnaire {nom_scientifique: code_statut} (optionnel)
        """
        output_fr = f"{output_base}_fr.html"
        output_en = f"{output_base}_en.html"
        
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template(template_file)
        
        if gallery_id is None:
            gallery_id = output_base
        
        # Ajouter statut IUCN à chaque photo
        if iucn_statuts:
            for photo in photos:
                sci_name = photo.get('scientific_name', '')
                photo['iucn_status'] = iucn_statuts.get(sci_name, '')
        
        # Date de mise à jour (aujourd'hui)
        today = datetime.now()
        heure = today.strftime('%-Hh%M')
        update_date_fr = formater_date(today.strftime('%Y-%m-%d'), 'fr') + f' ({heure})'
        update_date_en = formater_date(today.strftime('%Y-%m-%d'), 'en') + f' ({heure})'
        
        # Version française
        html_fr = template.render(
            lang='fr',
            gallery_title=title_fr,
            gallery_subtitle=subtitle_fr,
            gallery_id=gallery_id,
            photos=photos,
            menu=menu or [],
            current_page=output_fr,
            other_lang_page=output_en,
            species_count=species_count,
            show_date_in_overlay=show_date_in_overlay,
            trip_locations=trip_locations,
            update_date=True,
            update_date_fr=update_date_fr,
            update_date_en=update_date_en,
            back_link=back_link_fr,
            back_text_fr=back_text_fr or 'Retour',
            back_text_en=back_text_en or 'Back'
        )
        
        with open(output_fr, 'w', encoding='utf-8') as f:
            f.write(html_fr)
        
        # Version anglaise
        html_en = template.render(
            lang='en',
            gallery_title=title_en,
            gallery_subtitle=subtitle_en,
            gallery_id=gallery_id,
            photos=photos,
            menu=menu or [],
            current_page=output_en,
            other_lang_page=output_fr,
            species_count=species_count,
            show_date_in_overlay=show_date_in_overlay,
            trip_locations=trip_locations,
            update_date=True,
            update_date_fr=update_date_fr,
            update_date_en=update_date_en,
            back_link=back_link_en,
            back_text_fr=back_text_fr or 'Retour',
            back_text_en=back_text_en or 'Back'
        )
        
        with open(output_en, 'w', encoding='utf-8') as f:
            f.write(html_en)

        print(f"   ✓ {output_fr} / {output_en} ({len(photos)} photos)")

        # Galerie plein écran "infinite scroll" associée : mêmes photos, un feed style
        # Reels au lieu de la grille. La grille redirige vers ce feed au clic sur une espèce.
        # Les données photo vont dans un JSON séparé (chargé en fetch() côté client) plutôt
        # que dans le HTML : pour les grosses galeries, ça évite de bloquer le rendu initial
        # le temps de parser un gros bloc JS en ligne.
        feed_template = env.get_template('gallery_feed_template.html')
        feed_fr = f"{output_base}_feed_fr.html"
        feed_en = f"{output_base}_feed_en.html"
        feed_data_file = f"{output_base}_feed_data.json"

        ecrire_feed_json(photos, feed_data_file)

        with open(feed_fr, 'w', encoding='utf-8') as f:
            f.write(feed_template.render(
                lang='fr', gallery_title=title_fr, photos=photos, back_url=output_fr,
                data_url=feed_data_file
            ))

        with open(feed_en, 'w', encoding='utf-8') as f:
            f.write(feed_template.render(
                lang='en', gallery_title=title_en, photos=photos, back_url=output_en,
                data_url=feed_data_file
            ))

        print(f"   ✓ {feed_fr} / {feed_en} (feed plein écran)")

        return output_fr, output_en
    
    def generate_species_list(self,
                             output_base: str = 'species_list',
                             template_file: str = 'species_list_template.html',
                             menu: list = None,
                             curation: dict = None,
                             iucn_statuts: dict = None):
        """Génère la page liste des espèces par famille"""
        
        output_fr = f"{output_base}_fr.html"
        output_en = f"{output_base}_en.html"
        
        species_list = self.get_species_list(curation=curation)
        
        # Ajouter statut IUCN à chaque espèce
        if iucn_statuts:
            for sp in species_list:
                sci_name = sp.get('sci_name', '')
                sp['iucn_status'] = iucn_statuts.get(sci_name, '')
        
        # Grouper par famille
        families = {}
        for sp in species_list:
            fam = sp['family'] or 'Unknown'
            if fam not in families:
                # Extraire le nom anglais entre parenthèses
                family_full = sp['family_full'] or fam
                name_en_match = re.search(r'\(([^)]+)\)', family_full)
                name_en = name_en_match.group(1) if name_en_match else ''
                
                # Gérer le cas "Unknown"
                if fam == 'Unknown':
                    code_display = 'Autres'  # Sera adapté selon la langue dans le template
                    name_en = 'Others'
                else:
                    code_display = fam
                
                families[fam] = {
                    'code': fam,
                    'code_display_fr': 'Autres' if fam == 'Unknown' else fam,
                    'code_display_en': 'Others' if fam == 'Unknown' else fam,
                    'name_en': name_en,
                    'name_fr': '',  # Sera généré après
                    'order': self.taxonomy.get_family_order(fam) if fam != 'Unknown' else 999999,
                    'species': []
                }
            families[fam]['species'].append(sp)
        
        # Générer les descriptions françaises à partir des noms d'espèces
        for fam_data in families.values():
            if fam_data['code'] != 'Unknown':
                noms_fr = [sp['common_name_fr'] for sp in fam_data['species']]
                fam_data['name_fr'] = generer_description_groupe_fr(noms_fr)
            else:
                fam_data['name_fr'] = ''
        
        # Trier les familles par ordre phylogénétique
        sorted_families = sorted(families.values(), key=lambda x: x['order'])
        
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template(template_file)
        
        # Date de mise à jour (aujourd'hui)
        today = datetime.now()
        heure = today.strftime('%-Hh%M')
        update_date_fr = formater_date(today.strftime('%Y-%m-%d'), 'fr') + f' ({heure})'
        update_date_en = formater_date(today.strftime('%Y-%m-%d'), 'en') + f' ({heure})'
        
        # Version française
        html_fr = template.render(
            lang='fr',
            families=sorted_families,
            total_species=len(species_list),
            total_families=len(sorted_families),
            menu=menu or [],
            current_page=output_fr,
            other_lang_page=output_en,
            output_base=output_base,
            update_date=True,
            update_date_fr=update_date_fr,
            update_date_en=update_date_en
        )

        with open(output_fr, 'w', encoding='utf-8') as f:
            f.write(html_fr)

        # Version anglaise
        html_en = template.render(
            lang='en',
            families=sorted_families,
            total_species=len(species_list),
            total_families=len(sorted_families),
            menu=menu or [],
            current_page=output_en,
            other_lang_page=output_fr,
            output_base=output_base,
            update_date=True,
            update_date_fr=update_date_fr,
            update_date_en=update_date_en
        )
        
        with open(output_en, 'w', encoding='utf-8') as f:
            f.write(html_en)

        print(f"   ✓ {output_fr} / {output_en} ({len(species_list)} espèces, {len(sorted_families)} familles)")

        # Feed plein écran couvrant TOUTES les espèces, dans l'ordre des familles (phylogénétique)
        feed_photos = []
        for fam_data in sorted_families:
            for sp in fam_data['species']:
                for photo in sp['all_photos']:
                    feed_photos.append({
                        'ml_catalog_number': photo['ml_catalog_number'],
                        'common_name_fr': sp['common_name_fr'],
                        'common_name_en': sp['common_name_en'],
                        'scientific_name': sp['sci_name'],
                        'location': photo.get('location', ''),
                        'location_full_fr': photo['location_full_fr'],
                        'location_full_en': photo['location_full_en'],
                        'date_fr': photo['date_fr'],
                        'date_en': photo['date_en'],
                        'latitude': photo['latitude'],
                        'longitude': photo['longitude'],
                        'checklist_id': photo['checklist_id'],
                        'iucn_status': sp.get('iucn_status', '')
                    })

        feed_template = env.get_template('gallery_feed_template.html')
        feed_fr = f"{output_base}_feed_fr.html"
        feed_en = f"{output_base}_feed_en.html"
        feed_data_file = f"{output_base}_feed_data.json"

        # Données dans un JSON séparé (fetch() côté client) : cette galerie couvre TOUTES
        # les espèces du site (des milliers de photos), un bloc JS en ligne de cette taille
        # bloquait le rendu initial le temps d'être parsé au complet.
        ecrire_feed_json(feed_photos, feed_data_file)

        with open(feed_fr, 'w', encoding='utf-8') as f:
            f.write(feed_template.render(
                lang='fr', gallery_title='Toutes les espèces', photos=feed_photos, back_url=output_fr,
                data_url=feed_data_file
            ))

        with open(feed_en, 'w', encoding='utf-8') as f:
            f.write(feed_template.render(
                lang='en', gallery_title='All species', photos=feed_photos, back_url=output_en,
                data_url=feed_data_file
            ))

        print(f"   ✓ {feed_fr} / {feed_en} (feed plein écran, {len(feed_photos)} photos)")

        return output_fr, output_en


def verifier_tous_les_medias(csv_file: str, cache_file: str = CACHE_FILE,
                              sounds_file: str = SOUNDS_COMPILATION_FILE,
                              taxonomy_file: str = TAXONOMY_FILE):
    """Vérifie tous les médias du fichier CSV. Les numéros ML qui ne sont pas des
    images (donc des sons) sont compilés par espèce dans sounds_file."""
    print("=" * 60)
    print("🔍 VÉRIFICATION COMPLÈTE DES MÉDIAS")
    print("=" * 60)

    all_ml_numbers = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ml_string = row.get('ML Catalog Numbers') or ''
            ml_string = ml_string.strip()
            if ml_string:
                for ml in ml_string.replace(',', ' ').split():
                    ml = ml.strip()
                    if ml:
                        all_ml_numbers.append(ml)

    all_ml_numbers = list(set(all_ml_numbers))
    print(f"\nTotal de médias uniques: {len(all_ml_numbers)}")

    resultats = verifier_medias(all_ml_numbers, cache_file)

    # Afficher les statistiques
    cache = resultats['cache']
    images = sum(1 for v in cache.values() if v.get('status') == 'image')
    sons = sum(1 for v in cache.values() if v.get('status') == 'son')
    videos = sum(1 for v in cache.values() if v.get('status') == 'video')
    inconnus = sum(1 for v in cache.values() if v.get('status') == 'inconnu')

    print("\n" + "=" * 60)
    print("✅ VÉRIFICATION TERMINÉE")
    print(f"   📷 {images} photos")
    print(f"   🎵 {sons} sons")
    if videos:
        print(f"   🎬 {videos} vidéos")
    if inconnus:
        print(f"   ❓ {inconnus} non identifiés")
    print("=" * 60)

    if sons:
        generator = EBirdGalleryGenerator(csv_file, media_cache_file=cache_file,
                                           taxonomy_file=taxonomy_file)
        sounds_list = generator.get_sounds_list()
        ecrire_sons_par_espece(sounds_list, sounds_file)
        print(f"   🎶 Compilation sons/espèce : {len(sounds_list)} espèces -> {sounds_file}")

    return resultats


def ecrire_sons_par_espece(sounds_list: list, chemin_fichier: str):
    """Écrit la compilation des sons regroupés par espèce (issue de get_sounds_list)."""
    with open(chemin_fichier, 'w', encoding='utf-8') as f:
        json.dump(sounds_list, f, ensure_ascii=False, indent=2)


def generer_sonogramme(ml_catalog_number: str, dest_dir: str = SOUNDS_ASSETS_DIR,
                        pxps: int = SOUNDS_PXPS) -> dict:
    """
    Génère (et met en cache sur disque) le sonogramme en niveaux de gris d'un son,
    à largeur exacte en pixels/seconde. Le sonogramme CDN de Cornell (/640) ne
    correspond pas dans le temps au fichier mp3 téléchargeable (probablement généré
    depuis un extrait différent) ; on génère donc le nôtre depuis le vrai fichier
    joué, avec ffmpeg, pour garantir une synchronisation exacte à la lecture.

    Retourne {'path': ..., 'duration': ...} ou None si échec (mp3 introuvable,
    ffmpeg absent, etc.) : dans ce cas sounds_template.html doit pouvoir s'en passer.
    """
    os.makedirs(dest_dir, exist_ok=True)
    image_path = os.path.join(dest_dir, f"{ml_catalog_number}.jpg")
    meta_path = os.path.join(dest_dir, f"{ml_catalog_number}.json")

    if os.path.exists(image_path) and os.path.exists(meta_path):
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                return {'path': image_path, 'duration': json.load(f)['duration']}
        except Exception:
            pass  # métadonnées corrompues : régénérer

    mp3_url = f"https://cdn.download.ams.birds.cornell.edu/api/v2/asset/{ml_catalog_number}/mp3"
    tmp_mp3 = os.path.join(dest_dir, f"_tmp_{ml_catalog_number}.mp3")

    try:
        request = Request(mp3_url)
        request.add_header('User-Agent', 'Mozilla/5.0 (compatible; eBird Gallery)')
        with urlopen(request, timeout=30) as response, open(tmp_mp3, 'wb') as out:
            out.write(response.read())

        probe = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', tmp_mp3],
            capture_output=True, text=True, timeout=30, check=True
        )
        duration = float(probe.stdout.strip())
        width = max(640, round(duration * pxps))

        subprocess.run(
            ['ffmpeg', '-y', '-i', tmp_mp3, '-lavfi',
             f'showspectrumpic=s={width}x220:legend=0,hue=s=0,negate',
             '-update', '1', '-frames:v', '1', image_path],
            capture_output=True, timeout=60, check=True
        )

        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump({'duration': duration}, f)

        time.sleep(0.1)  # ne pas marteler le CDN
        return {'path': image_path, 'duration': duration}

    except Exception as e:
        print(f"  ⚠ Sonogramme impossible pour ML{ml_catalog_number}: {e}")
        return None
    finally:
        if os.path.exists(tmp_mp3):
            os.remove(tmp_mp3)


if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("🐦 GÉNÉRATEUR DE GALERIES eBird v2.0")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        csv_file = sys.argv[2] if len(sys.argv) > 2 else "MyEBirdData.csv"
        
        if cmd == "verifier":
            verifier_tous_les_medias(csv_file)
        else:
            print(f"Commande inconnue: {cmd}")
    else:
        print("""
Usage:
    python generate_gallery.py verifier [fichier.csv]
        → Vérifie tous les médias et met à jour le cache
    
Pour générer des galeries, utilisez generer_tout.py
""")
