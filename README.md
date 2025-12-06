# Galerie Photos eBird v2.0

Générateur de galeries photos bilingues (français/anglais) à partir de vos données eBird.

## Fonctionnalités

- **Liste des espèces** avec recherche instantanée
- **Galeries par voyage** avec dates et images de couverture personnalisables
- **Galeries par famille taxonomique** avec icônes
- **Ajouts récents** (3 derniers mois ou 50 dernières photos)
- **Lightbox** avec carte de localisation et navigation
- **Bilingue** français/anglais avec basculement facile

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

## Configuration

Tous les paramètres sont dans `config.yaml`:

```yaml
# Fichiers source
fichiers:
  donnees_ebird: "MyEBirdData.csv"
  taxonomie: "eBird_taxonomy_v2025.csv"

# Site web
site:
  index: "index.html"
  auteur: "Votre Nom"

# Options
generation:
  verifier_medias_en_ligne: false
  limite_photos_defaut: 300

# Voyages (avec image de couverture personnalisable)
voyages:
  - id: voyage_floride
    nom_fr: "Floride"
    nom_en: "Florida"
    pays: ["US-FL"]
    frontispice: "last"  # ou "first" ou numéro ML

# Icônes des familles (override optionnel)
familles_icones:
  Anatidae: "305223451"  # Numéro ML spécifique
```

## Utilisation

### Première utilisation

```bash
# 1. Vérifier les médias (crée le cache)
python generer_tout.py verifier

# 2. Générer toutes les galeries
python generer_tout.py
```

### Mises à jour

```bash
# Régénérer après mise à jour des données
python generer_tout.py
```

## Fichiers générés

- `species_list_fr.html` / `species_list_en.html` - Liste des espèces
- `gallery_recent_fr.html` / `gallery_recent_en.html` - Ajouts récents
- `voyages_index_fr.html` / `voyages_index_en.html` - Index des voyages
- `familles_index_fr.html` / `familles_index_en.html` - Index des familles
- `voyage_*_fr.html` / `voyage_*_en.html` - Galeries par voyage
- `gallery_*_fr.html` / `gallery_*_en.html` - Galeries par famille

## Structure des fichiers

```
├── config.yaml              # Configuration centralisée
├── generer_tout.py          # Script principal
├── generate_gallery.py      # Moteur de génération
├── gallery.css              # Styles
├── gallery_template.html    # Template galeries
├── species_list_template.html
├── voyages_index_template.html
├── familles_index_template.html
├── traductions_lieux.csv    # Traductions pays/régions
├── MyEBirdData.csv          # Vos données (à ajouter)
├── eBird_taxonomy_v2025.csv # Taxonomie (à ajouter)
└── media_cache.csv          # Cache médias (généré)
```

## Personnalisation

### Images de couverture (Voyages)

Dans `config.yaml`:
```yaml
voyages:
  - id: voyage_floride
    frontispice: "305223451"  # Numéro ML spécifique
```

### Icônes des familles

Dans `config.yaml`:
```yaml
familles_icones:
  Anatidae: "305223451"
  Accipitridae: "first"
  Trochilidae: "last"
```

## Licence

© Étienne Artigau
