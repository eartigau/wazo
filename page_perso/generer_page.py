#!/usr/bin/env python3
"""
Starlight whispers through
algorithms parse the dark—
worlds beyond revealed

Generator for bilingual personal page with Markdown support.
Converts YAML content to HTML pages (FR/EN).
"""

import re
import yaml
from pathlib import Path
from typing import Any

# =============================================================================
# MARKDOWN TO HTML CONVERSION
# =============================================================================

def markdown_to_html(text: str) -> str:
    """
    Convert Markdown-style text to HTML.
    Supports: links, paragraphs, bullet points (• or -).
    
    Optimized with compiled regex patterns for faster execution.
    """
    if not text:
        return ""
    
    # Pre-compiled patterns for performance
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    bullet_pattern = re.compile(r'^[•\-]\s+', re.MULTILINE)
    
    # Convert Markdown links [text](url) to <a> tags
    text = link_pattern.sub(r'<a href="\2" target="_blank">\1</a>', text)
    
    # Split into paragraphs
    paragraphs = text.strip().split('\n\n')
    html_parts = []
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # Check if paragraph contains bullet points
        lines = para.split('\n')
        bullet_lines = [l for l in lines if bullet_pattern.match(l.strip())]
        
        if bullet_lines and len(bullet_lines) == len(lines):
            # All lines are bullets -> create <ul>
            items = [bullet_pattern.sub('', l.strip()) for l in lines]
            html_parts.append('<ul>' + ''.join(f'<li>{item}</li>' for item in items) + '</ul>')
        elif bullet_lines:
            # Mixed content: process line by line
            result = []
            in_list = False
            list_items = []
            
            for line in lines:
                line = line.strip()
                if bullet_pattern.match(line):
                    if not in_list:
                        in_list = True
                    list_items.append(bullet_pattern.sub('', line))
                else:
                    if in_list:
                        result.append('<ul>' + ''.join(f'<li>{item}</li>' for item in list_items) + '</ul>')
                        list_items = []
                        in_list = False
                    if line:
                        result.append(f'<p>{line}</p>')
            
            if list_items:
                result.append('<ul>' + ''.join(f'<li>{item}</li>' for item in list_items) + '</ul>')
            
            html_parts.append(''.join(result))
        else:
            # Regular paragraph
            # Join lines with <br> for single newlines within paragraph
            joined = '<br>'.join(l.strip() for l in lines if l.strip())
            html_parts.append(f'<p>{joined}</p>')
    
    return '\n'.join(html_parts)


# =============================================================================
# YOUTUBE ID EXTRACTION
# =============================================================================

# Pre-compiled pattern for YouTube URL parsing
YOUTUBE_PATTERN = re.compile(
    r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})'
)

def extract_youtube_id(url: str) -> str:
    """
    Extract YouTube video ID from various URL formats.
    Returns empty string if no valid ID found.
    """
    match = YOUTUBE_PATTERN.search(url)
    return match.group(1) if match else ""


# =============================================================================
# TEMPLATE RENDERING
# =============================================================================

def render_template(template: str, context: dict[str, Any]) -> str:
    """
    Simple template rendering with Jinja2-like syntax.
    Supports: {{ variable }}, {% for %}, {% if %}, conditionals.
    """
    result = template
    
    # Process for loops first: {% for item in items %}...{% endfor %}
    for_pattern = re.compile(
        r'\{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%\}(.*?)\{%\s*endfor\s*%\}',
        re.DOTALL
    )
    
    def replace_for(match):
        var_name = match.group(1)
        list_name = match.group(2)
        body = match.group(3)
        
        items = context.get(list_name, [])
        if not items:
            return ""
        
        rendered_items = []
        for item in items:
            item_body = body
            # Replace {{ var.attr }} patterns
            for key, value in item.items():
                item_body = item_body.replace(f'{{{{ {var_name}.{key} }}}}', str(value))
            rendered_items.append(item_body)
        
        return ''.join(rendered_items)
    
    result = for_pattern.sub(replace_for, result)
    
    # Process conditionals: {{ 'value1' if condition else 'value2' }}
    cond_pattern = re.compile(r"\{\{\s*'([^']+)'\s+if\s+(\w+)\s*==\s*'([^']+)'\s+else\s*'([^']*)'\s*\}\}")
    
    def replace_cond(match):
        val_true, var, check_val, val_false = match.groups()
        return val_true if context.get(var) == check_val else val_false
    
    result = cond_pattern.sub(replace_cond, result)
    
    # Replace simple variables: {{ variable }}
    for key, value in context.items():
        if not isinstance(value, (list, dict)):
            result = result.replace(f'{{{{ {key} }}}}', str(value))
    
    return result


# =============================================================================
# CONTEXT BUILDER
# =============================================================================

def get_text(obj: dict, key: str, lang: str) -> str:
    """
    Extract text for given language from a bilingual dict.
    Falls back to 'fr' if lang not found.
    """
    value = obj.get(key, {})
    if isinstance(value, dict):
        return value.get(lang, value.get('fr', ''))
    return str(value)


def build_context(config: dict, lang: str) -> dict[str, Any]:
    """
    Build template context from YAML config for specified language.
    """
    # Helper for bilingual fields
    def t(obj: dict, key: str) -> str:
        return get_text(obj, key, lang)
    
    # Navigation labels
    nav_labels = {
        'fr': {'recherche': 'Recherche', 'medias': 'Médias', 'oiseaux': 'Photos', 
               'scroll': 'Défiler', 'gallery': 'Voir la galerie'},
        'en': {'recherche': 'Research', 'medias': 'Media', 'oiseaux': 'Photos',
               'scroll': 'Scroll', 'gallery': 'View gallery'}
    }
    labels = nav_labels.get(lang, nav_labels['fr'])
    
    # Process videos
    videos = []
    for v in config.get('medias', {}).get('videos', []):
        video_id = extract_youtube_id(v.get('url', ''))
        if video_id:
            videos.append({
                'video_id': video_id,
                'titre': t(v, 'titre')
            })
    
    # Process discoveries
    decouvertes = []
    for d in config.get('medias', {}).get('decouvertes', []):
        decouvertes.append({
            'titre': t(d, 'titre'),
            'annee': d.get('annee', ''),
            'url': d.get('url', '')
        })
    
    # Build context dict
    context = {
        'lang': lang,
        'nom': config.get('nom', ''),
        'titre': t(config, 'titre'),
        'photo': config.get('photo', ''),
        'css_path': config.get('css_path', ''),
        
        # Affiliation
        'affiliation_inst': config.get('affiliation', {}).get('institution', ''),
        'affiliation_dept': t(config.get('affiliation', {}), 'departement'),
        
        # Liens
        'email': config.get('liens', {}).get('email', ''),
        'orcid': config.get('liens', {}).get('orcid', ''),
        
        # Navigation
        'nav_recherche': labels['recherche'],
        'nav_medias': labels['medias'],
        'nav_oiseaux': labels['oiseaux'],
        'scroll_hint': labels['scroll'],
        'oiseaux_bouton': labels['gallery'],
        
        # Intro
        'intro': t(config, 'intro').strip(),
        
        # Recherche - convert Markdown to HTML
        'recherche_titre': t(config.get('recherche', {}), 'titre'),
        'recherche_photo': config.get('recherche', {}).get('photo', ''),
        'recherche_contenu': markdown_to_html(t(config.get('recherche', {}), 'contenu')),
        
        # Médias
        'medias_titre': t(config.get('medias', {}), 'titre'),
        'ads_url': config.get('medias', {}).get('ads_url', ''),
        'ads_texte': t(config.get('medias', {}), 'ads_texte'),
        'decouvertes_titre': t(config.get('medias', {}), 'decouvertes_titre'),
        'videos': videos,
        'decouvertes': decouvertes,
        
        # Oiseaux - convert Markdown to HTML
        'oiseaux_titre': t(config.get('oiseaux', {}), 'titre'),
        'oiseaux_photo': config.get('oiseaux', {}).get('photo', ''),
        'oiseaux_contenu': markdown_to_html(t(config.get('oiseaux', {}), 'contenu')),
        'oiseaux_lien': config.get('liens', {}).get('galerie_oiseaux', '').replace('_fr', f'_{lang}'),
        
        # Footer
        'footer_text': t(config.get('footer', {'fr': '', 'en': ''}), 'fr' if lang == 'fr' else 'en')
            if isinstance(config.get('footer'), dict) 
            else config.get('footer', {}).get(lang, '')
    }
    
    # Fix footer for simple dict structure
    footer = config.get('footer', {})
    if isinstance(footer, dict):
        context['footer_text'] = footer.get(lang, footer.get('fr', ''))
    
    return context


# =============================================================================
# MAIN GENERATOR
# =============================================================================

def generate_pages(config_path: str = 'content.yaml', 
                   template_path: str = 'template.html',
                   output_dir: str = '.') -> None:
    """
    Generate bilingual HTML pages from YAML config.
    Creates: index_fr.html, index_en.html, index.html (redirect)
    """
    # Load config
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Load template
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    output_path = Path(output_dir)
    
    # Generate for each language
    for lang in ['fr', 'en']:
        context = build_context(config, lang)
        html = render_template(template, context)
        
        out_file = output_path / f'index_{lang}.html'
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✓ Generated: {out_file}")
    
    # Create redirect index.html
    redirect_html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0; url=index_fr.html">
    <script>
        const userLang = navigator.language || navigator.userLanguage;
        const targetLang = userLang.startsWith('fr') ? 'fr' : 'en';
        window.location.href = 'index_' + targetLang + '.html';
    </script>
</head>
<body>
    <p>Redirecting... <a href="index_fr.html">Français</a> | <a href="index_en.html">English</a></p>
</body>
</html>'''
    
    with open(output_path / 'index.html', 'w', encoding='utf-8') as f:
        f.write(redirect_html)
    print("✓ Generated: index.html (redirect)")


if __name__ == '__main__':
    generate_pages()
