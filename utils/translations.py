# Traducciones simples para la aplicación
translations = {
    'es': {
        'Will it be rain on my parade?': '¿Lloverá en mi desfile?',
        'Will it be rain on my': '¿Lloverá en mi',
        'parade?': 'desfile?',
        '¿Quieres saber si lloverá en tu área?': '¿Quieres saber si lloverá en tu área?',
        'Continuar': 'Continuar',
        'Mapa Interactivo': 'Mapa Interactivo',
        'Buscar ubicación ...': 'Buscar ubicación ...',
        'Punto': 'Punto',
        'Polígono': 'Polígono',
        'Punto seleccionado': 'Punto seleccionado',
        'Polígono dibujado': 'Polígono dibujado '
    },
    'en': {
        'Will it be rain on my parade?': 'Will it be rain on my parade?',
        'Will it be rain on my': 'Will it be rain on my',
        'parade?': 'parade?',
        '¿Quieres saber si lloverá en tu área?': 'Do you want to know if it will rain in your area?',
        'Continuar': 'Continue',
        'Mapa Interactivo': 'Interactive Map',
        'Buscar ubicación ...': 'Search location ...',
        'Punto': 'Point',
        'Polígono': 'Polygon',
        'Punto seleccionado': 'Point selected',
        'Polígono dibujado': 'Polygon drawn'
    }
}

def get_translation(text, language='es'):
    """Obtiene la traducción de un texto según el idioma"""
    return translations.get(language, {}).get(text, text)