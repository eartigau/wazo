# Page Personnelle Bilingue

Page web personnelle avec toggle français/anglais, générée à partir d'un fichier YAML.

## Structure

```
page_perso/
├── content.yaml      # Tout le contenu à modifier
├── template.html     # Template HTML (ne pas modifier sauf CSS)
├── generer_page.py   # Script de génération
├── profile.jpg       # Votre photo (à ajouter)
├── index.html        # Redirection auto vers FR
├── index_fr.html     # Page française (générée)
└── index_en.html     # Page anglaise (générée)
```

## Utilisation

### 1. Modifier le contenu

Éditer `content.yaml` pour personnaliser :
- Informations de base (nom, titre, affiliation)
- Photo de profil (chemin du fichier)
- Textes des sections (recherche, instrumentation, etc.)
- Liens (email, ORCID, publications NASA ADS, galerie oiseaux)
- Parcours/timeline
- Projets

### 2. Ajouter votre photo

Placer votre photo dans le même dossier avec le nom défini dans `content.yaml` (par défaut: `profile.jpg`).

### 3. Régénérer la page

```bash
python generer_page.py
```

Options :
```bash
python generer_page.py content.yaml output_folder
```

## Fonctionnalités

- **Bilingue** : Toggle FR/EN dans la navigation
- **Scroll avec Espace** : Appuyer sur la barre d'espace fait défiler vers la section suivante
- **Responsive** : S'adapte aux mobiles
- **Sections** :
  - Hero avec photo et intro
  - Recherche
  - Instrumentation
  - Projets (grille avec liens)
  - Parcours (timeline)
  - Publications (lien vers NASA ADS)
  - Ornithologie (lien vers galerie)

## Lien avec la galerie d'oiseaux

Dans `content.yaml`, configurer le lien relatif :

```yaml
liens:
  galerie_oiseaux: "gallery/index_fr.html"
```

Si la galerie est dans un sous-dossier `gallery/`, le lien fonctionnera automatiquement.

## Déploiement

Les fichiers générés sont statiques et peuvent être hébergés sur :
- GitHub Pages
- Netlify
- Tout serveur web statique

## Personnalisation CSS

Le CSS est intégré dans `template.html`. Les variables principales sont :

```css
:root {
    --primary: #1a365d;       /* Couleur principale (bleu foncé) */
    --accent: #38a169;        /* Couleur d'accent (vert) */
    --bg: #f7fafc;            /* Fond gris clair */
}
```
