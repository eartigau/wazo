#!/usr/bin/env python3
"""
Générateur de page Lifelist eBird
Affiche toutes les observations sur une carte interactive avec liste d'espèces par site

Compatible avec le système de galerie eBird v2.0
"""

import csv
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from jinja2 import Environment, FileSystemLoader

from generate_gallery import (
    EBirdTaxonomy,
    TAXONOMY_FILE,
    CACHE_FILE,
    TRADUCTIONS_FILE,
    charger_traductions_lieux,
    traduire_lieu,
    charger_cache,
    formater_date,
    nettoyer_nom_lieu,
    normaliser_nom_scientifique,
    normaliser_nom_commun,
    est_taxon_non_identifiable
)


class LifelistGenerator:
    """Génère une page de lifelist avec carte interactive et liste d'espèces par site"""
    
    def __init__(self, csv_file: str,
                 taxonomy_file: str = TAXONOMY_FILE,
                 media_cache_file: str = CACHE_FILE,
                 traductions_file: str = TRADUCTIONS_FILE,
                 rejected_lists: list = None):
        
        self.csv_file = csv_file
        self.media_cache_file = media_cache_file
        self.rejected_lists = set(rejected_lists or [])
        
        # Charger la taxonomie
        self.taxonomy = EBirdTaxonomy(taxonomy_file)
        
        # Charger les traductions
        self.traductions = charger_traductions_lieux(traductions_file)
        
        # Charger le cache des médias
        self.media_cache = charger_cache(media_cache_file)
        
        # Charger toutes les observations (pas seulement celles avec photos)
        self.all_observations = []
        self._load_all_observations()
    
    def _load_all_observations(self):
        """Charge TOUTES les observations du fichier CSV eBird"""
        print(f"📂 Chargement des observations pour lifelist: {self.csv_file}...")
        
        rejected_count = 0
        with open(self.csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Filtrer les listes rejetées
                submission_id = row.get('Submission ID', '').strip()
                if submission_id in self.rejected_lists:
                    rejected_count += 1
                    continue
                self.all_observations.append(row)
        
        print(f"   ✓ {len(self.all_observations)} observations totales")
        if rejected_count > 0:
            print(f"   ⚠ {rejected_count} listes rejetées exclues")
    
    def _parse_coord(self, value) -> float:
        """Parse une coordonnée en float"""
        if not value:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def get_sites_with_species(self, curation: dict = None) -> tuple:
        """
        Construit les données des sites avec leurs espèces et photos
        
        Returns:
            tuple: (sites_data, photos_data, stats)
        """
        # Collecter les données par site (Location ID)
        sites_raw = defaultdict(lambda: {
            'location': '',
            'location_id': '',
            'lat': None,
            'lng': None,
            'state_code': '',
            'species': defaultdict(lambda: {
                'sci_name': '',
                'name_fr': '',
                'name_en': '',
                'family': 'Others',
                'taxon_order': 999999,
                'observations': [],
                'photos': []
            })
        })
        
        # Traiter chaque observation
        for obs in self.all_observations:
            sci_name_raw = obs.get('Scientific Name', '').strip()
            common_name_raw = obs.get('Common Name', '').strip()
            location_id = obs.get('Location ID', '').strip()
            
            if not sci_name_raw or not location_id:
                continue
            
            # Exclure les taxons non identifiables
            if est_taxon_non_identifiable(sci_name_raw, common_name_raw):
                continue
            
            # Normaliser le nom scientifique
            sci_name = normaliser_nom_scientifique(sci_name_raw)
            
            # Info du site
            location = nettoyer_nom_lieu(obs.get('Location') or '')
            lat = self._parse_coord(obs.get('Latitude'))
            lng = self._parse_coord(obs.get('Longitude'))
            state_code = obs.get('State/Province') or ''
            
            site = sites_raw[location_id]
            site['location'] = location
            site['location_id'] = location_id
            site['state_code'] = state_code
            if lat and lng:
                site['lat'] = lat
                site['lng'] = lng
            
            # Info de l'espèce
            taxon_info = self.taxonomy.get_species_info(sci_name)
            common_name_fr = normaliser_nom_commun(obs.get('Common Name', ''))
            common_name_en = normaliser_nom_commun(taxon_info.get('common_name_en') or obs.get('Common Name', ''))
            family_full = taxon_info.get('family_full', 'Others')
            
            sp = site['species'][sci_name]
            sp['sci_name'] = sci_name
            sp['name_fr'] = common_name_fr
            sp['name_en'] = common_name_en
            sp['taxon_order'] = taxon_info.get('taxon_order', 999999)
            sp['family'] = family_full
            
            # Ajouter l'observation
            obs_date = obs.get('Date') or ''
            count = obs.get('Count') or 'X'
            
            # Info province et pays pour l'observation
            country_code = state_code.split('-')[0] if '-' in state_code else state_code
            region_fr = traduire_lieu(state_code, self.traductions, 'fr')
            region_en = traduire_lieu(state_code, self.traductions, 'en')
            country_fr = traduire_lieu(country_code, self.traductions, 'fr')
            country_en = traduire_lieu(country_code, self.traductions, 'en')
            
            # Construire province + pays
            if region_fr and country_fr and region_fr != country_fr:
                province_country_fr = f"{region_fr}, {country_fr}"
            else:
                province_country_fr = country_fr or region_fr or ''
            
            if region_en and country_en and region_en != country_en:
                province_country_en = f"{region_en}, {country_en}"
            else:
                province_country_en = country_en or region_en or ''
            
            sp['observations'].append({
                'date_raw': obs_date,
                'date_fr': formater_date(obs_date, 'fr'),
                'date_en': formater_date(obs_date, 'en'),
                'count': count,
                'checklist_id': obs.get('Submission ID', ''),
                'province_country_fr': province_country_fr,
                'province_country_en': province_country_en
            })
            
            # Ajouter les photos si disponibles
            ml_string = obs.get('ML Catalog Numbers') or ''
            ml_numbers = [n.strip() for n in ml_string.replace(',', ' ').split() if n.strip()]
            
            for ml in ml_numbers:
                # Vérifier que c'est une image valide
                if ml not in self.media_cache or self.media_cache[ml]['status'] != 'image':
                    continue
                
                # Vérifier la curation
                if curation and curation.get(ml) == 'reject':
                    continue
                
                # Info lieu complet pour la photo
                country_code = state_code.split('-')[0] if '-' in state_code else state_code
                region_fr = traduire_lieu(state_code, self.traductions, 'fr')
                region_en = traduire_lieu(state_code, self.traductions, 'en')
                country_fr = traduire_lieu(country_code, self.traductions, 'fr')
                country_en = traduire_lieu(country_code, self.traductions, 'en')
                
                if region_fr and country_fr and region_fr != country_fr:
                    lieu_complet_fr = f"{location}, {region_fr}, {country_fr}" if location else f"{region_fr}, {country_fr}"
                else:
                    lieu_complet_fr = f"{location}, {country_fr}" if location and country_fr else location or country_fr
                
                if region_en and country_en and region_en != country_en:
                    lieu_complet_en = f"{location}, {region_en}, {country_en}" if location else f"{region_en}, {country_en}"
                else:
                    lieu_complet_en = f"{location}, {country_en}" if location and country_en else location or country_en
                
                sp['photos'].append({
                    'ml': ml,
                    'name_fr': common_name_fr,
                    'name_en': common_name_en,
                    'sci_name': sci_name,
                    'location_fr': lieu_complet_fr,
                    'location_en': lieu_complet_en,
                    'date_raw': obs_date,
                    'date_fr': formater_date(obs_date, 'fr'),
                    'date_en': formater_date(obs_date, 'en'),
                    'curation_status': curation.get(ml, 'include') if curation else 'include'
                })
        
        # Convertir en format final
        sites_data = []
        total_species = set()
        total_observations = 0
        
        for location_id, site in sites_raw.items():
            if not site['lat'] or not site['lng']:
                continue
            
            # Convertir les espèces
            species_list = []
            for sci_name, sp_data in site['species'].items():
                total_species.add(sci_name)
                total_observations += len(sp_data['observations'])
                
                # Trier les observations par date (plus récente d'abord)
                sp_data['observations'].sort(key=lambda x: x['date_raw'], reverse=True)
                
                # Trier les photos: best d'abord, puis par date
                best_photos = sorted(
                    [p for p in sp_data['photos'] if p.get('curation_status') == 'best'],
                    key=lambda x: x['date_raw'], reverse=True
                )
                other_photos = sorted(
                    [p for p in sp_data['photos'] if p.get('curation_status') != 'best'],
                    key=lambda x: x['date_raw'], reverse=True
                )
                sp_data['photos'] = best_photos + other_photos
                
                # Dédupliquer les photos (par ML number)
                seen_ml = set()
                unique_photos = []
                for p in sp_data['photos']:
                    if p['ml'] not in seen_ml:
                        seen_ml.add(p['ml'])
                        unique_photos.append(p)
                sp_data['photos'] = unique_photos
                
                species_list.append({
                    'sci_name': sp_data['sci_name'],
                    'name_fr': sp_data['name_fr'],
                    'name_en': sp_data['name_en'],
                    'family': sp_data.get('family', 'Others'),
                    'taxon_order': sp_data['taxon_order'],
                    'observations': sp_data['observations'],
                    'photos': sp_data['photos']
                })
            
            # Trier les espèces par ordre taxonomique
            species_list.sort(key=lambda x: x['taxon_order'])
            
            sites_data.append({
                'location': site['location'],
                'location_id': site['location_id'],
                'lat': site['lat'],
                'lng': site['lng'],
                'state_code': site['state_code'],
                'species': species_list
            })
        
        # Statistiques
        stats = {
            'total_species': len(total_species),
            'total_sites': len(sites_data),
            'total_observations': total_observations
        }
        
        print(f"   ✓ {stats['total_species']} espèces sur {stats['total_sites']} sites")
        
        return sites_data, stats
    
    def _compute_advanced_stats(self, sites_data) -> dict:
        """
        Calcule des statistiques avancées pour la lifelist
        
        Returns:
            dict: Statistiques avancées
        """
        # Collecter toutes les observations avec leurs métadonnées
        all_obs = []  # liste de dict {date, species, count, location, checklist_id, province_country_fr, province_country_en}
        species_counts = defaultdict(int)  # espèce -> nombre d'observations
        location_counts = defaultdict(int)  # location -> nombre d'observations
        date_species = defaultdict(set)  # date -> set d'espèces
        checklist_dates = {}  # checklist_id -> date
        site_checklists = defaultdict(set)  # location -> set de checklists
        site_species = defaultdict(set)  # location -> set d'espèces
        year_species = defaultdict(set)  # année -> set d'espèces
        
        for site in sites_data:
            for sp in site['species']:
                site_species[site['location']].add(sp['sci_name'])
                for obs in sp['observations']:
                    date = obs['date_raw']
                    year = date[:4] if date else ''
                    all_obs.append({
                        'date': date,
                        'species': sp['sci_name'],
                        'name_fr': sp['name_fr'],
                        'name_en': sp['name_en'],
                        'count': obs['count'],
                        'location': site['location'],
                        'checklist_id': obs['checklist_id'],
                        'province_country_fr': obs.get('province_country_fr', ''),
                        'province_country_en': obs.get('province_country_en', '')
                    })
                    species_counts[sp['sci_name']] += 1
                    location_counts[site['location']] += 1
                    date_species[date].add(sp['sci_name'])
                    if obs['checklist_id']:
                        checklist_dates[obs['checklist_id']] = date
                        site_checklists[site['location']].add(obs['checklist_id'])
                    if year:
                        year_species[year].add(sp['sci_name'])
        
        # Espèce la plus observée
        if species_counts:
            most_obs_species_sci = max(species_counts.keys(), key=lambda k: species_counts[k])
            most_obs_species_count = species_counts[most_obs_species_sci]
            # Trouver les noms communs
            most_obs_species_fr = most_obs_species_sci
            most_obs_species_en = most_obs_species_sci
            for obs in all_obs:
                if obs['species'] == most_obs_species_sci:
                    most_obs_species_fr = obs['name_fr']
                    most_obs_species_en = obs['name_en']
                    break
        else:
            most_obs_species_fr = ''
            most_obs_species_en = ''
            most_obs_species_count = 0
        
        # Lieu le plus visité
        if location_counts:
            most_visited_location = max(location_counts.keys(), key=lambda k: location_counts[k])
            most_visited_count = location_counts[most_visited_location]
        else:
            most_visited_location = ''
            most_visited_count = 0
        
        # Jour avec le plus d'espèces
        if date_species:
            best_day = max(date_species.keys(), key=lambda k: len(date_species[k]))
            best_day_species_count = len(date_species[best_day])
            best_day_fr = formater_date(best_day, 'fr')
            best_day_en = formater_date(best_day, 'en')
        else:
            best_day = ''
            best_day_species_count = 0
            best_day_fr = ''
            best_day_en = ''
        
        # Plus longue séquence ininterrompue de jours avec listes
        unique_dates = sorted(set(checklist_dates.values()))
        longest_streak = 0
        current_streak = 0
        streak_start = None
        streak_end = None
        best_streak_start = None
        best_streak_end = None
        prev_date = None
        
        for date_str in unique_dates:
            try:
                current_date = datetime.strptime(date_str, '%Y-%m-%d')
                if prev_date is None:
                    current_streak = 1
                    streak_start = date_str
                elif (current_date - prev_date).days == 1:
                    current_streak += 1
                else:
                    if current_streak > longest_streak:
                        longest_streak = current_streak
                        best_streak_start = streak_start
                        best_streak_end = prev_date.strftime('%Y-%m-%d')
                    current_streak = 1
                    streak_start = date_str
                streak_end = date_str
                prev_date = current_date
            except ValueError:
                continue
        
        # Vérifier la dernière séquence
        if current_streak > longest_streak:
            longest_streak = current_streak
            best_streak_start = streak_start
            best_streak_end = streak_end
        
        # Nombre total d'individus comptés
        total_individuals = 0
        for obs in all_obs:
            count = obs['count']
            if count != 'X' and count.isdigit():
                total_individuals += int(count)
        
        # Nombre de pays différents
        countries = set()
        for site in sites_data:
            state_code = site.get('state_code', '')
            country_code = state_code.split('-')[0] if '-' in state_code else state_code
            if country_code:
                countries.add(country_code)
        
        # Nombre de jours d'observation
        unique_observation_days = len(unique_dates)
        
        # Premier et dernier jour d'observation
        if unique_dates:
            first_obs_date = unique_dates[0]
            last_obs_date = unique_dates[-1]
            first_obs_date_fr = formater_date(first_obs_date, 'fr')
            first_obs_date_en = formater_date(first_obs_date, 'en')
            last_obs_date_fr = formater_date(last_obs_date, 'fr')
            last_obs_date_en = formater_date(last_obs_date, 'en')
        else:
            first_obs_date_fr = ''
            first_obs_date_en = ''
            last_obs_date_fr = ''
            last_obs_date_en = ''
        
        # Nombre moyen d'espèces par jour
        if unique_observation_days > 0:
            avg_species_per_day = round(sum(len(s) for s in date_species.values()) / unique_observation_days, 1)
        else:
            avg_species_per_day = 0
        
        # Site avec le plus de listes (checklists)
        if site_checklists:
            most_lists_site = max(site_checklists.keys(), key=lambda k: len(site_checklists[k]))
            most_lists_count = len(site_checklists[most_lists_site])
        else:
            most_lists_site = ''
            most_lists_count = 0
        
        # Site avec le plus d'espèces
        if site_species:
            most_species_site = max(site_species.keys(), key=lambda k: len(site_species[k]))
            most_species_site_count = len(site_species[most_species_site])
        else:
            most_species_site = ''
            most_species_site_count = 0
        
        # Meilleure année (plus d'espèces nouvelles/observées)
        if year_species:
            best_year = max(year_species.keys(), key=lambda k: len(year_species[k]))
            best_year_species_count = len(year_species[best_year])
        else:
            best_year = ''
            best_year_species_count = 0
        
        return {
            'most_observed_species_fr': most_obs_species_fr,
            'most_observed_species_en': most_obs_species_en,
            'most_observed_species_count': most_obs_species_count,
            'most_visited_location': most_visited_location,
            'most_visited_count': most_visited_count,
            'best_day_date_fr': best_day_fr,
            'best_day_date_en': best_day_en,
            'best_day_species_count': best_day_species_count,
            'longest_streak': longest_streak,
            'streak_start_fr': formater_date(best_streak_start, 'fr') if best_streak_start else '',
            'streak_start_en': formater_date(best_streak_start, 'en') if best_streak_start else '',
            'streak_end_fr': formater_date(best_streak_end, 'fr') if best_streak_end else '',
            'streak_end_en': formater_date(best_streak_end, 'en') if best_streak_end else '',
            'total_individuals': total_individuals,
            'countries_count': len(countries),
            'observation_days_count': unique_observation_days,
            'first_obs_date_fr': first_obs_date_fr,
            'first_obs_date_en': first_obs_date_en,
            'last_obs_date_fr': last_obs_date_fr,
            'last_obs_date_en': last_obs_date_en,
            'avg_species_per_day': avg_species_per_day,
            'most_lists_site': most_lists_site,
            'most_lists_count': most_lists_count,
            'most_species_site': most_species_site,
            'most_species_site_count': most_species_site_count,
            'best_year': best_year,
            'best_year_species_count': best_year_species_count
        }
    
    def generate_lifelist_page(self,
                               output_base: str = 'lifelist',
                               template_file: str = 'lifelist_template.html',
                               menu: list = None,
                               curation: dict = None,
                               author: str = 'Étienne Artigau'):
        """
        Génère les pages HTML de la lifelist en français et anglais
        
        Args:
            output_base: Nom de base sans extension
            template_file: Fichier template Jinja2
            menu: Structure du menu
            curation: Dict {ml_number: 'best'|'include'|'reject'}
            author: Nom de l'auteur pour le copyright
        """
        output_fr = f"{output_base}_fr.html"
        output_en = f"{output_base}_en.html"
        
        # Obtenir les données
        sites_data, stats = self.get_sites_with_species(curation=curation)
        
        # Calculer les statistiques avancées
        advanced_stats = self._compute_advanced_stats(sites_data)
        
        # Convertir en JSON pour le JavaScript
        sites_json = json.dumps(sites_data, ensure_ascii=False)
        advanced_stats_json = json.dumps(advanced_stats, ensure_ascii=False)
        
        # Photos indexées par espèce (pour toutes les photos de la lifelist)
        # Note: les photos sont déjà dans sites_data, mais on les passe aussi
        # séparément pour faciliter l'accès côté JS
        photos_json = json.dumps({}, ensure_ascii=False)
        
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template(template_file)
        
        # Date de mise à jour
        today = datetime.now()
        update_date_fr = formater_date(today.strftime('%Y-%m-%d'), 'fr')
        update_date_en = formater_date(today.strftime('%Y-%m-%d'), 'en')
        
        # Version française
        html_fr = template.render(
            lang='fr',
            menu=menu or [],
            current_page=output_fr,
            other_lang_page=output_en,
            total_species=stats['total_species'],
            total_sites=stats['total_sites'],
            total_observations=stats['total_observations'],
            sites_json=sites_json,
            photos_json=photos_json,
            advanced_stats_json=advanced_stats_json,
            author=author,
            update_date=True,
            update_date_fr=update_date_fr,
            update_date_en=update_date_en
        )
        
        with open(output_fr, 'w', encoding='utf-8') as f:
            f.write(html_fr)
        
        # Version anglaise
        html_en = template.render(
            lang='en',
            menu=menu or [],
            current_page=output_en,
            other_lang_page=output_fr,
            total_species=stats['total_species'],
            total_sites=stats['total_sites'],
            total_observations=stats['total_observations'],
            sites_json=sites_json,
            photos_json=photos_json,
            advanced_stats_json=advanced_stats_json,
            author=author,
            update_date=True,
            update_date_fr=update_date_fr,
            update_date_en=update_date_en
        )
        
        with open(output_en, 'w', encoding='utf-8') as f:
            f.write(html_en)
        
        print(f"   ✓ {output_fr} / {output_en} ({stats['total_species']} espèces, {stats['total_sites']} sites)")
        
        return output_fr, output_en


def main():
    """Fonction principale pour tester le générateur"""
    import sys
    
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "MyEBirdData.csv"
    
    print("=" * 60)
    print("🗺️ GÉNÉRATEUR DE LIFELIST eBird")
    print("=" * 60)
    
    generator = LifelistGenerator(csv_file)
    generator.generate_lifelist_page()
    
    print("\n✅ Génération terminée!")


if __name__ == "__main__":
    main()
