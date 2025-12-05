#!/usr/bin/env python3
"""
Configuration des galeries eBird v2.0
Modifiez ce fichier pour personnaliser vos galeries
"""

# ============================================================================
# VOYAGES
# Utilisez les codes pays/régions eBird (ex: CA-QC, US-FL, CL, CH)
# ============================================================================

VOYAGES = [
    {
        'id': 'voyage_chili',
        'nom_fr': 'Chili',
        'nom_en': 'Chile',
        'pays': ['CL'],
        'limite': 500
    },
    {
        'id': 'voyage_geneve',
        'nom_fr': 'Genève',
        'nom_en': 'Geneva',
        'pays': ['CH'],
        'limite': 300
    },
    {
        'id': 'voyage_hawaii',
        'nom_fr': 'Hawaï',
        'nom_en': 'Hawaii',
        'pays': ['US-HI'],
        'limite': 300
    },
    {
        'id': 'voyage_floride',
        'nom_fr': 'Floride',
        'nom_en': 'Florida',
        'pays': ['US-FL'],
        'limite': 300
    },
    {
        'id': 'voyage_arizona',
        'nom_fr': 'Arizona',
        'nom_en': 'Arizona',
        'pays': ['US-AZ'],
        'limite': 200
    },
]


# ============================================================================
# FAMILLES D'OISEAUX (OBSOLÈTE - CONSERVÉ POUR RÉFÉRENCE)
# Les galeries par famille sont maintenant générées AUTOMATIQUEMENT
# pour toutes les familles observées. Cette section n'est plus utilisée.
# ============================================================================

# Cette variable n'est plus utilisée - les galeries par famille sont
# générées automatiquement à partir des observations.
FAMILLES_OBSOLETE = [
    {
        'id': 'gallery_anatidae',
        'nom_fr': 'Anatidés',
        'nom_en': 'Waterfowl',
        'familles': ['Anatidae'],  # Canards, oies, cygnes
        'limite': 400
    },
    {
        'id': 'gallery_raptors',
        'nom_fr': 'Rapaces',
        'nom_en': 'Raptors',
        'familles': ['Accipitridae', 'Falconidae', 'Pandionidae', 'Cathartidae'],
        'limite': 300
    },
    {
        'id': 'gallery_owls',
        'nom_fr': 'Hiboux et chouettes',
        'nom_en': 'Owls',
        'familles': ['Strigidae', 'Tytonidae'],
        'limite': 200
    },
    {
        'id': 'gallery_herons',
        'nom_fr': 'Hérons et aigrettes',
        'nom_en': 'Herons & Egrets',
        'familles': ['Ardeidae'],
        'limite': 200
    },
    {
        'id': 'gallery_woodpeckers',
        'nom_fr': 'Pics',
        'nom_en': 'Woodpeckers',
        'familles': ['Picidae'],
        'limite': 200
    },
    {
        'id': 'gallery_hummingbirds',
        'nom_fr': 'Colibris',
        'nom_en': 'Hummingbirds',
        'familles': ['Trochilidae'],
        'limite': 150
    },
    {
        'id': 'gallery_warblers',
        'nom_fr': 'Parulines',
        'nom_en': 'Warblers',
        'familles': ['Parulidae'],
        'limite': 300
    },
    {
        'id': 'gallery_shorebirds',
        'nom_fr': 'Limicoles',
        'nom_en': 'Shorebirds',
        'familles': ['Scolopacidae', 'Charadriidae', 'Recurvirostridae', 'Haematopodidae'],
        'limite': 300
    },
    {
        'id': 'gallery_gulls',
        'nom_fr': 'Goélands et sternes',
        'nom_en': 'Gulls & Terns',
        'familles': ['Laridae'],
        'limite': 200
    },
    {
        'id': 'gallery_sparrows',
        'nom_fr': 'Bruants',
        'nom_en': 'Sparrows',
        'familles': ['Passerellidae'],
        'limite': 200
    },
    {
        'id': 'gallery_flycatchers',
        'nom_fr': 'Moucherolles',
        'nom_en': 'Flycatchers',
        'familles': ['Tyrannidae'],
        'limite': 200
    },
    {
        'id': 'gallery_thrushes',
        'nom_fr': 'Grives',
        'nom_en': 'Thrushes',
        'familles': ['Turdidae'],
        'limite': 150
    },
]


# ============================================================================
# GALERIES GÉNÉRALES
# ============================================================================

GALERIES_GENERALES = [
    {
        'id': 'gallery_all',
        'nom_fr': 'Toutes les photos',
        'nom_en': 'All Photos',
        'limite': 1000
    },
    {
        'id': 'gallery_quebec',
        'nom_fr': 'Québec',
        'nom_en': 'Quebec',
        'pays': ['CA-QC'],
        'limite': 500
    },
    {
        'id': 'gallery_recent',
        'nom_fr': 'Photos récentes',
        'nom_en': 'Recent Photos',
        'date_debut': '2024-01-01',
        'limite': 300
    },
]


# ============================================================================
# AIDE - CODES FAMILLES COURANTS
# ============================================================================
"""
Anatidae - Canards, oies, cygnes
Accipitridae - Éperviers, buses, aigles
Falconidae - Faucons
Strigidae - Hiboux
Tytonidae - Effraies
Ardeidae - Hérons, aigrettes
Picidae - Pics
Trochilidae - Colibris
Parulidae - Parulines
Scolopacidae - Bécasseaux, chevaliers
Charadriidae - Pluviers
Laridae - Goélands, sternes
Passerellidae - Bruants
Tyrannidae - Moucherolles
Turdidae - Grives
Fringillidae - Pinsons
Icteridae - Carouges, orioles
Corvidae - Corneilles, geais
Hirundinidae - Hirondelles
Alcidae - Guillemots, macareux
Phalacrocoracidae - Cormorans
Podicipedidae - Grèbes
Gaviidae - Huards
Procellariidae - Pétrels, puffins
Sulidae - Fous
Pelecanidae - Pélicans
Threskiornithidae - Ibis, spatules
Gruidae - Grues
Rallidae - Râles
Columbidae - Pigeons, tourterelles
Cuculidae - Coulicous
Caprimulgidae - Engoulevents
Apodidae - Martinets
Alcedinidae - Martins-pêcheurs
"""
