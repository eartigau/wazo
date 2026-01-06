# Page Personnelle Bilingue

Page web personnelle avec toggle français/anglais, générée à partir d'un fichier YAML.
Supporte le Markdown dans le texte (liens automatiquement convertis en HTML).

## Structure

```
page_perso/
├── content.yaml      # Tout le contenu à modifier
├── template.html     # Template HTML
├── generer_page.py   # Génère index_fr.html + index_en.html
├── profile.jpg       # Photo profil (à ajouter)
├── painting.png      # Photo recherche (à ajouter)
├── cartoon.png       # Photo oiseaux (à ajouter)
├── index.html        # Redirection auto FR/EN
├── index_fr.html     # Page française (générée)
└── index_en.html     # Page anglaise (générée)
```

## Contenu de la page

La page contient 4 sections :

1. **Hero** : Photo profil, nom, titre, affiliation, intro
2. **Recherche** : Texte avec liens Markdown + photo
3. **Médias & Publications** : NASA ADS + Découvertes + vidéos YouTube
4. **Photographie d'oiseaux** : Texte + photo + lien vers galerie

## Utilisation

### 1. Modifier `content.yaml`

- Ajuster `css_path` selon votre structure de dossiers
- Écrire vos textes en FR et EN
- Ajouter vos découvertes et vidéos

### 2. Ajouter vos photos

- `profile.jpg` : Photo de profil (hero, affichée en rond)
- `painting.png` : Photo section Recherche
- `cartoon.png` : Photo section Oiseaux

### 3. Régénérer la page

```bash
python generer_page.py
```

## Fonctionnalités

### Support Markdown

Le contenu texte supporte les liens Markdown :
```
[texte du lien](https://url.com)
```
Automatiquement convertis en `<a href="..." target="_blank">texte</a>`

Listes avec puces :
```
• Premier élément
• Deuxième élément
```

### Section Découvertes

Grille de découvertes/distinctions dans la section Médias :
```yaml
decouvertes:
  - titre:
      fr: "Titre en français"
      en: "Title in English"
    annee: "2024"
    url: "https://source-originale.com"
```

### Vidéos YouTube

URLs parsées automatiquement :
- `youtube.com/watch?v=ID`
- `youtu.be/ID`
- `youtube.com/embed/ID`

## Structure recommandée

```
mon_site/
├── index.html           # Redirige vers FR/EN
├── index_fr.html        
├── index_en.html        
├── profile.jpg
├── painting.png
├── cartoon.png
└── gallery/             # Galerie d'oiseaux
    ├── gallery.css      # CSS partagé
    └── ...
```

## Palette de couleurs

Tons verts doux s'harmonisant avec la galerie :
- Fond hero/oiseaux : #e8f0e4 (vert très clair)
- Accents : #6b8f5c (vert moyen)
- Hover : #87a878 (vert doux)
