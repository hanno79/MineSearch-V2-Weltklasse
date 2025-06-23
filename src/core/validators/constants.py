"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Konstanten für Validatoren
"""


class ValidatorConstants:
    """Zentrale Konstanten für alle Validatoren"""
    
    # Währungscodes
    VALID_CURRENCIES = [
        'CAD', 'USD', 'EUR', 'GBP', 'AUD', 'CHF', 'JPY', 'CNY',
        'ZAR', 'BRL', 'MXN', 'CLP', 'PEN', 'COP', 'ARS', 'RUB'
    ]
    
    # Gültige Rohstoffe (mehrsprachig)
    VALID_COMMODITIES = [
        # Edelmetalle
        'gold', 'or', 'oro', 'золото',
        'silver', 'argent', 'plata', 'silber', 'серебро',
        'platinum', 'platin', 'platino', 'платина',
        'palladium', 'palladio', 'палладий',
        
        # Basismetalle
        'copper', 'cuivre', 'cobre', 'kupfer', 'медь',
        'zinc', 'zink', 'цинк',
        'lead', 'plomb', 'plomo', 'blei', 'свинец',
        'nickel', 'níquel', 'никель',
        'tin', 'étain', 'estaño', 'zinn', 'олово',
        'aluminum', 'aluminium', 'aluminio', 'алюминий',
        
        # Eisenmetalle
        'iron', 'fer', 'hierro', 'eisen', 'железо',
        'steel', 'acier', 'acero', 'stahl', 'сталь',
        'manganese', 'manganèse', 'mangan', 'марганец',
        'chromium', 'chrome', 'cromo', 'chrom', 'хром',
        
        # Energierohstoffe
        'coal', 'charbon', 'carbón', 'kohle', 'уголь',
        'uranium', 'uran', 'uranio', 'уран',
        'oil', 'pétrole', 'petróleo', 'öl', 'нефть',
        'gas', 'gaz', 'erdgas', 'газ',
        
        # Industrieminerale
        'lithium', 'litio', 'литий',
        'cobalt', 'kobalt', 'cobalto', 'кобальт',
        'graphite', 'graphit', 'grafito', 'графит',
        'diamond', 'diamant', 'diamante', 'алмаз',
        'phosphate', 'phosphat', 'fosfato', 'фосфат',
        'potash', 'potasse', 'potasa', 'kali', 'калий',
        
        # Seltene Erden
        'rare earth', 'terres rares', 'tierras raras', 'seltene erden',
        
        # Andere
        'salt', 'sel', 'sal', 'salz', 'соль',
        'limestone', 'calcaire', 'caliza', 'kalkstein', 'известняк',
        'sand', 'sable', 'arena', 'песок',
        'gravel', 'gravier', 'grava', 'kies', 'гравий'
    ]
    
    # Gültige Minenstatus
    VALID_MINE_STATUS = [
        # Aktiv
        'active', 'aktiv', 'actif', 'activo', 'активный',
        'operating', 'in betrieb', 'en operation', 'operando',
        'producing', 'produzierend', 'produisant', 'produciendo',
        'operational', 'betriebsbereit', 'opérationnel', 'operacional',
        
        # Inaktiv
        'inactive', 'inaktiv', 'inactif', 'inactivo', 'неактивный',
        'closed', 'geschlossen', 'fermé', 'cerrado', 'закрыт',
        'abandoned', 'aufgegeben', 'abandonné', 'abandonado',
        'depleted', 'erschöpft', 'épuisé', 'agotado',
        
        # Pausiert
        'suspended', 'suspendiert', 'suspendu', 'suspendido',
        'on hold', 'pausiert', 'en pause', 'en espera',
        'care and maintenance', 'wartung', 'entretien',
        
        # Entwicklung
        'development', 'entwicklung', 'développement', 'desarrollo',
        'construction', 'bau', 'строительство',
        'exploration', 'erkundung', 'exploración',
        'feasibility', 'machbarkeit', 'faisabilité'
    ]
    
    # Status-Normalisierung
    STATUS_NORMALIZATION = {
        # Zu 'aktiv'
        'active': 'aktiv',
        'operating': 'aktiv',
        'in betrieb': 'aktiv',
        'producing': 'aktiv',
        'operational': 'aktiv',
        'production': 'aktiv',
        
        # Zu 'inaktiv'
        'inactive': 'inaktiv',
        'closed': 'inaktiv',
        'geschlossen': 'inaktiv',
        'shut down': 'inaktiv',
        'abandoned': 'inaktiv',
        'depleted': 'inaktiv',
        
        # Zu 'pausiert'
        'suspended': 'pausiert',
        'on hold': 'pausiert',
        'care and maintenance': 'pausiert',
        'temporary closure': 'pausiert',
        
        # Zu 'entwicklung'
        'development': 'entwicklung',
        'construction': 'entwicklung',
        'pre-production': 'entwicklung',
        'commissioning': 'entwicklung',
        
        # Zu 'exploration'
        'exploration': 'exploration',
        'feasibility': 'exploration',
        'evaluation': 'exploration'
    }
    
    # Gültige Minentypen
    VALID_MINE_TYPES = [
        # Tagebau
        'open pit', 'tagebau', 'mine à ciel ouvert', 'mina a cielo abierto',
        'surface', 'oberflächlich', 'surface mine',
        'strip mine', 'streifenbergbau',
        'quarry', 'steinbruch', 'carrière', 'cantera',
        
        # Untertagebau
        'underground', 'untertagebau', 'souterrain', 'subterráneo',
        'subsurface', 'unterirdisch',
        'shaft mine', 'schachtbergbau',
        'drift mine', 'stollenbergbau',
        
        # Spezialtypen
        'placer', 'alluvial', 'seifenbergbau',
        'dredging', 'baggerung', 'dragage',
        'solution', 'lösung', 'lixiviation',
        'in-situ', 'in situ leaching', 'isl',
        
        # Kombiniert
        'combined', 'kombiniert', 'combiné', 'combinado',
        'hybrid', 'hybride', 'híbrido',
        'mixed', 'gemischt', 'mixte', 'mixto'
    ]
    
    # Rohstoff-Normalisierung
    COMMODITY_NORMALIZATION = {
        # Gold
        'gold': 'Gold', 'or': 'Gold', 'oro': 'Gold', 'золото': 'Gold',
        
        # Silber
        'silver': 'Silber', 'argent': 'Silber', 'plata': 'Silber',
        'ag': 'Silber', 'серебро': 'Silber',
        
        # Kupfer
        'copper': 'Kupfer', 'cuivre': 'Kupfer', 'cobre': 'Kupfer',
        'cu': 'Kupfer', 'медь': 'Kupfer',
        
        # Weitere Metalle
        'iron': 'Eisen', 'fer': 'Eisen', 'hierro': 'Eisen', 'fe': 'Eisen',
        'zinc': 'Zink', 'zn': 'Zink', 'цинк': 'Zink',
        'lead': 'Blei', 'plomb': 'Blei', 'plomo': 'Blei', 'pb': 'Blei',
        'nickel': 'Nickel', 'ni': 'Nickel', 'níquel': 'Nickel',
        'tin': 'Zinn', 'étain': 'Zinn', 'estaño': 'Zinn', 'sn': 'Zinn',
        
        # Energierohstoffe
        'coal': 'Kohle', 'charbon': 'Kohle', 'carbón': 'Kohle',
        'uranium': 'Uran', 'u': 'Uran', 'uranio': 'Uran',
        
        # Industrieminerale
        'lithium': 'Lithium', 'li': 'Lithium', 'litio': 'Lithium',
        'cobalt': 'Kobalt', 'co': 'Kobalt', 'cobalto': 'Kobalt',
        
        # Edelsteine
        'diamond': 'Diamant', 'diamonds': 'Diamant', 'diamante': 'Diamant',
        
        # Seltene Erden
        'rare earth': 'Seltene Erden', 'terres rares': 'Seltene Erden',
        'ree': 'Seltene Erden', 'tierras raras': 'Seltene Erden'
    }
    
    # Einheiten für Validierung
    PRODUCTION_UNITS = {
        'weight': ['tonnes', 'tons', 't', 'mt', 'kg', 'g', 'oz', 'pounds', 'lbs'],
        'volume': ['m3', 'cubic meters', 'liters', 'l', 'barrels', 'bbl'],
        'energy': ['mwh', 'gwh', 'twh', 'btu', 'mcf', 'bcf'],
        'concentration': ['g/t', 'oz/t', 'ppm', '%', 'percent']
    }
    
    # Länder (ISO-3166)
    VALID_COUNTRIES = [
        'Canada', 'USA', 'United States', 'Mexico', 'Brazil', 'Chile', 'Peru',
        'Argentina', 'Colombia', 'Australia', 'China', 'Russia', 'India',
        'South Africa', 'Ghana', 'Mali', 'Burkina Faso', 'Tanzania',
        'DRC', 'Democratic Republic of Congo', 'Zambia', 'Zimbabwe',
        'Germany', 'France', 'UK', 'United Kingdom', 'Spain', 'Sweden',
        'Finland', 'Norway', 'Poland', 'Turkey', 'Kazakhstan', 'Mongolia',
        'Indonesia', 'Philippines', 'Papua New Guinea', 'New Zealand'
    ]