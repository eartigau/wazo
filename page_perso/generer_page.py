#!/usr/bin/env python3
"""
Générateur de page personnelle bilingue
Lit content.yaml et génère index_fr.html et index_en.html
"""

import yaml
import os
from pathlib import Path

def load_config(config_path: str = 'content.yaml') -> dict:
    """Charge la configuration YAML"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_template(template_path: str = 'template.html') -> str:
    """Charge le template HTML"""
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def render_template(template: str, context: dict) -> str:
    """
    Remplace les variables {{ variable }} dans le template
    Gère aussi les boucles {% for item in items %}...{% endfor %}
    """
    import re
    
    # Traiter les boucles for
    for_pattern = r'\{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%\}(.*?)\{%\s*endfor\s*%\}'
    
    def replace_for(match):
        item_name = match.group(1)
        list_name = match.group(2)
        block = match.group(3)
        
        items = context.get(list_name, [])
        result = []
        
        for item in items:
            block_rendered = block
            # Remplacer {{ item.attr }} par les valeurs
            for key, value in item.items():
                block_rendered = block_rendered.replace(f'{{{{ {item_name}.{key} }}}}', str(value))
            result.append(block_rendered)
        
        return ''.join(result)
    
    template = re.sub(for_pattern, replace_for, template, flags=re.DOTALL)
    
    # Traiter les conditions simples {{ 'active' if lang == 'fr' else '' }}
    cond_pattern = r"\{\{\s*'([^']*?)'\s*if\s+(\w+)\s*==\s*'([^']*?)'\s*else\s*'([^']*?)'\s*\}\}"
    
    def replace_cond(match):
        true_val = match.group(1)
        var_name = match.group(2)
        test_val = match.group(3)
        false_val = match.group(4)
        return true_val if context.get(var_name) == test_val else false_val
    
    template = re.sub(cond_pattern, replace_cond, template)
    
    # Remplacer les variables simples {{ variable }}
    for key, value in context.items():
        if not isinstance(value, (list, dict)):
            template = template.replace(f'{{{{ {key} }}}}', str(value))
    
    return template

def build_context(config: dict, lang: str) -> dict:
    """Construit le contexte pour le template selon la langue"""
    
    def get_text(obj, key=None):
        """Récupère le texte dans la bonne langue"""
        if key:
            obj = obj.get(key, {})
        if isinstance(obj, dict):
            return obj.get(lang, obj.get('fr', ''))
        return obj
    
    context = {
        'lang': lang,
        'nom': config['nom'],
        'titre': get_text(config, 'titre'),
        'photo': config.get('photo', 'profile.jpg'),
        
        # Affiliation
        'affiliation_inst': config['affiliation']['institution'],
        'affiliation_dept': get_text(config['affiliation'], 'departement'),
        'affiliation_role': get_text(config['affiliation'], 'role'),
        
        # Liens
        'email': config['liens']['email'],
        'orcid': config['liens']['orcid'],
        'publications_lien': config['liens']['publications'],
        'oiseaux_lien': config['liens']['galerie_oiseaux'],
        
        # Intro
        'intro': get_text(config, 'intro').strip(),
        
        # Navigation
        'nav_recherche': 'Recherche' if lang == 'fr' else 'Research',
        'nav_publications': 'Publications',
        'nav_projets': 'Projets' if lang == 'fr' else 'Projects',
        'nav_oiseaux': 'Oiseaux' if lang == 'fr' else 'Birds',
        'scroll_hint': 'Appuyez sur Espace pour défiler' if lang == 'fr' else 'Press Space to scroll',
        
        # Recherche
        'recherche_titre': get_text(config['recherche'], 'titre'),
        'recherche_contenu': get_text(config['recherche'], 'contenu').strip(),
        
        # Instrumentation
        'instrumentation_titre': get_text(config['instrumentation'], 'titre'),
        'instrumentation_contenu': get_text(config['instrumentation'], 'contenu').strip(),
        
        # Publications
        'publications_titre': get_text(config['publications'], 'titre'),
        'publications_description': get_text(config['publications'], 'description'),
        'publications_bouton': get_text(config['publications'], 'bouton'),
        
        # Oiseaux
        'oiseaux_titre': get_text(config['oiseaux'], 'titre'),
        'oiseaux_contenu': get_text(config['oiseaux'], 'contenu').strip(),
        'oiseaux_bouton': get_text(config['oiseaux'], 'bouton'),
        
        # Parcours
        'parcours_titre': get_text(config['parcours'], 'titre'),
        'parcours': [
            {
                'periode': item['periode'],
                'poste': get_text(item, 'poste')
            }
            for item in config['parcours']['items']
        ],
        
        # Projets
        'projets_titre': get_text(config['projets'], 'titre'),
        'projets': [
            {
                'nom': p['nom'],
                'description': get_text(p, 'description'),
                'lien': p['lien']
            }
            for p in config['projets']['liste']
        ],
        
        # Footer
        'footer_text': get_text(config, 'footer'),
    }
    
    return context

def generate_pages(config_path: str = 'content.yaml', 
                   template_path: str = 'template.html',
                   output_dir: str = '.'):
    """Génère les pages FR et EN"""
    
    print("=" * 50)
    print("GÉNÉRATION DE LA PAGE PERSONNELLE")
    print("=" * 50)
    
    # Charger config et template
    config = load_config(config_path)
    template = load_template(template_path)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Générer les deux versions
    for lang in ['fr', 'en']:
        print(f"\n📄 Génération index_{lang}.html...")
        
        context = build_context(config, lang)
        html = render_template(template, context)
        
        output_file = output_path / f'index_{lang}.html'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"   ✓ {output_file}")
    
    # Créer un index.html qui redirige vers FR par défaut
    redirect_html = '''<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0; url=index_fr.html">
    <script>window.location.href = 'index_fr.html';</script>
</head>
<body>
    <p>Redirection vers <a href="index_fr.html">la page française</a>...</p>
</body>
</html>'''
    
    with open(output_path / 'index.html', 'w', encoding='utf-8') as f:
        f.write(redirect_html)
    print(f"\n   ✓ index.html (redirection)")
    
    print("\n" + "=" * 50)
    print("✅ Génération terminée!")
    print(f"   Photo attendue: {config.get('photo', 'profile.jpg')}")
    print("=" * 50)

if __name__ == '__main__':
    import sys
    
    # Arguments optionnels
    config_path = sys.argv[1] if len(sys.argv) > 1 else 'content.yaml'
    output_dir = sys.argv[2] if len(sys.argv) > 2 else '.'
    
    generate_pages(config_path=config_path, output_dir=output_dir)
