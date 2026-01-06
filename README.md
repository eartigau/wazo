# Galerie Photos eBird v2.0

Générateur de galeries photos bilingues (français/anglais) à partir de vos données eBird.

## Fonctionnalités

- **Liste des espèces** avec recherche instantanée
- **Galeries par voyage** avec dates automatiques
- **Galeries par famille taxonomique** avec icônes
- **Ajouts récents** (3 derniers mois ou 50 dernières photos)
- **Meilleures photos** - galerie des photos marquées "best"
- **Lightbox** avec carte de localisation et navigation
- **Bilingue** français/anglais avec basculement facile
- **Page admin** pour la curation des photos (best/inclus/rejeté)

## Installation

### Prérequis

```bash
pip install jinja2 pyyaml
```

### Fichiers requis

1. **MyEBirdData.csv** - Vos données eBird
   - Télécharger depuis: https://ebird.org/downloadMyData
   
2. **eBird_taxonomy_v2025.csv** - Taxonomie officielle
   - Télécharger depuis: https://ebird.org/science/use-ebird-data/the-ebird-taxonomy
   - Mettre à jour annuellement

3. **config.yaml** - Configuration (inclus, à personnaliser)

## Utilisation

### Première utilisation

```bash
# 1. Vérifier les médias (crée le cache)
python generer_tout.py verifier

# 2. Générer toutes les galeries
python generer_tout.py
```

### Curation des photos

La page `admin_photos.html` permet de gérer vos photos :

1. Générez les galeries une première fois
2. Ouvrez `admin_photos.html` dans un navigateur
3. Pour chaque photo, choisissez :
   - ⭐ **Meilleur** : Photo mise en avant (frontispice des voyages/familles, affichée dans la galerie "Meilleures photos")
   - ✓ **Inclus** : Photo normale (défaut)
   - ✗ **Rejeté** : Photo exclue des galeries
4. Cliquez sur "Télécharger photo_curation.csv"
5. Placez le fichier dans le dossier du projet
6. Régénérez les galeries : `python generer_tout.py`

**Note** : Les photos "best" apparaissent automatiquement dans la galerie "Meilleures photos" (triées par ordre taxonomique) et servent de frontispice pour les voyages et les familles.

### Mises à jour

```bash
# Régénérer après mise à jour des données
python generer_tout.py
```

## Configuration

Tous les paramètres sont dans `config.yaml`:

```yaml
# Fichiers source
fichiers:
  donnees_ebird: "MyEBirdData.csv"
  taxonomie: "eBird_taxonomy_v2025.csv"
  curation: "photo_curation.csv"

# Site web
site:
  index: "index.html"
  auteur: "Votre Nom"

# Options
generation:
  verifier_medias_en_ligne: false
  limite_photos_defaut: 300

# Voyages
voyages:
  - id: voyage_floride
    nom_fr: "Floride"
    nom_en: "Florida"
    pays: ["US-FL"]
```

## Fichiers générés

- `species_list_fr.html` / `species_list_en.html` - Liste des espèces
- `gallery_recent_fr.html` / `gallery_recent_en.html` - Ajouts récents
- `gallery_best_fr.html` / `gallery_best_en.html` - Meilleures photos
- `voyages_index_fr.html` / `voyages_index_en.html` - Index des voyages
- `familles_index_fr.html` / `familles_index_en.html` - Index des familles
- `voyage_*_fr.html` / `voyage_*_en.html` - Galeries par voyage
- `gallery_*_fr.html` / `gallery_*_en.html` - Galeries par famille
- `admin_photos.html` - Page admin (non liée dans le menu)

## Structure des fichiers

```
├── config.yaml              # Configuration centralisée
├── generer_tout.py          # Script principal
├── generate_gallery.py      # Moteur de génération
├── gallery.css              # Styles (thème nature)
├── gallery_template.html    # Template galeries
├── species_list_template.html
├── voyages_index_template.html
├── familles_index_template.html
├── admin_template.html      # Template page admin
├── traductions_lieux.csv    # Traductions pays/régions
├── MyEBirdData.csv          # Vos données (à ajouter)
├── eBird_taxonomy_v2025.csv # Taxonomie (à ajouter)
├── media_cache.csv          # Cache médias (généré)
└── photo_curation.csv       # Curation (généré via admin)
```

## Licence

© Étienne Artigau
