# Galerie eBird v2.0

Générateur de galeries photo bilingues (français/anglais) à partir des données eBird.

## Fonctionnalités

- **Bilingue** : Galeries en français et anglais avec switch de langue (drapeaux 🇫🇷 🇬🇧)
- **Taxonomie** : Filtrage par famille taxonomique (Anatidae, Accipitridae, etc.)
- **Thème clair** : Style inspiré d'eBird avec fond blanc/gris pâle
- **Liste des espèces** : Ordre phylogénétique, groupé par famille
  - Une photo par espèce dans la grille
  - Toutes les photos de l'espèce dans la lightbox (navigation ←→)
  - Fusion des sous-espèces avec l'espèce principale
- **Galeries par famille** : Générées automatiquement pour toutes les familles observées
  - Tri taxonomique (pas chronologique)
  - Titre "Famille des Anatidaes" avec description
  - Affiche le nombre de photos et d'espèces
- **Galeries voyages** : Tri chronologique
- **Menu dynamique** : 
  - Toutes les familles avec photos
  - Format "Latin (descriptions au pluriel)"
  - 2-6 colonnes selon le nombre de familles (max 20/colonne)
- **Lightbox claire** : Fond gris pâle, compteur de photos, carte et lieu
- **Letterboxing** : Images affichées en entier sans recadrage
- **Dates formatées** : "13 janvier 2025" (FR) / "January 13, 2025" (EN)
- **Lieux traduits** : Pays et régions selon la langue
- **Descriptions au pluriel** : 
  - FR: Générées automatiquement (Canards, Oies, Hiboux, Merlebleus, etc.)
  - EN: Depuis la taxonomie eBird

## Installation

```bash
pip install jinja2
```

## Fichiers requis

1. `MyEBirdData.csv` - Vos données eBird
   → Télécharger depuis https://ebird.org/downloadMyData

2. `eBird_taxonomy_v2025.csv` - Taxonomie eBird
   → Télécharger depuis https://ebird.org/science/use-ebird-data/the-ebird-taxonomy

## Utilisation

### Première exécution (vérifier les médias)

```bash
python generer_tout.py verifier
```

Ceci vérifie chaque média pour distinguer les images des sons. Le résultat est sauvegardé dans `media_cache.csv`.

### Générer les galeries

```bash
python generer_tout.py
```

### Aide

```bash
python generer_tout.py help
```

## Configuration

### config_galeries.py

Définissez vos voyages et galeries générales :

```python
VOYAGES = [
    {
        'id': 'voyage_chili',
        'nom_fr': 'Chili',
        'nom_en': 'Chile',
        'pays': ['CL'],
        'limite': 500
    },
]

# Note: Les galeries par famille sont générées automatiquement
# pour toutes les familles observées (plus besoin de les définir)
```

### traductions_lieux.csv

Ajoutez vos traductions de pays/régions :

```csv
code,fr,en
CA-QC,Québec,Quebec
CH-GE,Genève,Geneva
```

## Fichiers générés

- `species_list_fr.html` / `species_list_en.html` - Liste des espèces
- `gallery_all_fr.html` / `gallery_all_en.html` - Toutes les photos
- `gallery_[famille]_fr.html` / `gallery_[famille]_en.html` - Par famille (auto)
- `voyage_[lieu]_fr.html` / `voyage_[lieu]_en.html` - Par voyage

## Structure des fichiers

```
ebird_gallery/
├── generate_gallery.py      # Classe principale
├── generer_tout.py          # Script de génération
├── config_galeries.py       # Configuration
├── verifier_medias.py       # Outil vérification médias
├── gallery_template.html    # Template galerie
├── species_list_template.html  # Template liste espèces
├── gallery.css              # Styles
├── traductions_lieux.csv    # Traductions
├── media_cache.csv          # Cache médias (généré)
├── MyEBirdData.csv          # Vos données
└── eBird_taxonomy_v2025.csv # Taxonomie
```

## Noms de familles courantes

| Code | Français | English |
|------|----------|---------|
| Anatidae | Anatidés | Ducks, Geese, Swans |
| Accipitridae | Accipitridés | Hawks, Eagles |
| Falconidae | Falconidés | Falcons |
| Strigidae | Strigidés | Typical Owls |
| Ardeidae | Ardéidés | Herons, Egrets |
| Picidae | Picidés | Woodpeckers |
| Trochilidae | Trochilidés | Hummingbirds |
| Parulidae | Parulidés | New World Warblers |
| Laridae | Laridés | Gulls, Terns |
| Scolopacidae | Scolopacidés | Sandpipers |

## Notes

- La page d'accueil (`index.html`) n'est pas générée automatiquement
- Le menu est centré, sans titre de site
- Les images gardent leurs proportions (letterboxing)
- Les drapeaux permettent de basculer entre FR et EN
- Les galeries par famille sont triées par ordre taxonomique
- Les galeries de voyage sont triées par date (plus récent d'abord)
