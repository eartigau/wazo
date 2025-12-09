# Page Personnelle Bilingue

Page web personnelle avec toggle français/anglais, générée à partir d'un fichier YAML.
Partage le CSS de la galerie d'oiseaux pour une cohérence visuelle.

## Structure

```
page_perso/
├── content.yaml      # Tout le contenu à modifier
├── template.html     # Template HTML
├── generer_page.py   # Génère index_fr.html + index_en.html
├── profile.jpg       # Votre photo (à ajouter)
├── index.html        # Redirection auto vers FR
├── index_fr.html     # Page française (générée)
└── index_en.html     # Page anglaise (générée)
```

## Utilisation

### 1. Modifier le contenu

Éditer `content.yaml` pour personnaliser :

```yaml
# Chemin vers le CSS partagé avec la galerie
css_path: "gallery/gallery.css"

# Photo de profil
photo: "profile.jpg"

# Photo d'oiseau (identifiant Macaulay Library) pour la section ornithologie
oiseaux:
  photo_ml: "12345678"  # Votre identifiant ML
```

### 2. Ajouter vos photos

- **Photo profil** : Placer dans le même dossier avec le nom défini dans le yaml
- **Photo oiseau** : Spécifier l'identifiant Macaulay Library dans `oiseaux.photo_ml`

### 3. Régénérer la page

```bash
python generer_page.py
```

## Configuration CSS

Le template utilise le CSS de la galerie d'oiseaux. Configurer le chemin relatif :

```yaml
css_path: "gallery/gallery.css"
```

Si votre structure est :
```
mon_site/
├── index_fr.html
├── index_en.html
└── gallery/
    ├── gallery.css
    └── ...
```

## Photo d'oiseau (section Ornithologie)

La section "Oiseaux" affiche une photo dans un cercle, tirée de Macaulay Library.

```yaml
oiseaux:
  photo_ml: "634559741"  # Identifiant ML de votre meilleure photo
```

L'image sera chargée depuis :
`https://cdn.download.ams.birds.cornell.edu/api/v2/asset/{photo_ml}/1200`

## Fonctionnalités

- **CSS partagé** : Utilise le même CSS que la galerie d'oiseaux
- **Bilingue** : Toggle FR/EN dans la navigation
- **Scroll avec Espace** : Appuyer sur la barre d'espace fait défiler vers la section suivante
- **Responsive** : S'adapte aux mobiles
- **Sections** : Hero, Recherche, Instrumentation, Projets, Parcours, Publications, Ornithologie

## Personnalisation

Les couleurs utilisent les variables CSS de la galerie :
- `--forest-green` : Couleur principale verte
- `--forest-green-light` / `--forest-green-dark` : Variations

Les styles spécifiques à la page perso sont préfixés `perso-` pour éviter les conflits.
