"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Länderspezifische Konfigurationen für Mining-Suchen
"""

# Länderspezifische Konfigurationen
COUNTRY_CONFIG = {
    'kanada': {
        'languages': ['en', 'fr'],
        'currency': 'CAD',
        'regions': ['Quebec', 'Ontario', 'British Columbia', 'Alberta', 
                   'Manitoba', 'Saskatchewan', 'Nova Scotia', 'New Brunswick', 
                   'Newfoundland and Labrador', 'Prince Edward Island',
                   'Northwest Territories', 'Yukon', 'Nunavut'],
        'mining_terms': {
            'mine': ['mine', 'site minier', 'project', 'projet', 'property', 'propriété'],
            'operator': ['operator', 'opérateur', 'exploitant', 'betreiber', 'operador'],
            'owner': ['owner', 'propriétaire', 'eigentümer', 'propietario', 'belongs to', 'gehört', 'property of'],
            'commodity': ['commodity', 'produit', 'minerai', 'mineral', 'minéral'],
            'restoration_costs': [
                'restoration costs', 'closure costs', 'reclamation costs', 
                'coûts de restauration', 'coûts de fermeture', 'coûts de réhabilitation',
                'asset retirement obligation', 'ARO', 'obligation de mise hors service',
                'environmental liability', 'passif environnemental', 
                'closure bond', 'garantie financière', 'financial assurance',
                'provision for closure', 'provision pour fermeture',
                'decommissioning costs', 'site rehabilitation', 'mine closure provision',
                'environmental bond', 'reclamation bond', 'security deposit',
                'restoration provision', 'closure liability', 'post-closure costs',
                'remediation costs', 'environmental obligations', 'closure reserve',
                'rehabilitation provision', 'closure financial guarantee',
                'coûts de déclassement', 'provision pour restauration',
                'garantie de fermeture', 'obligations environnementales'
            ]
        },
        'priority_domains': ['mern.gouv.qc.ca', 'nrcan.gc.ca', 'gestim.quebec',
                           'mining.ca', 'sedar.com', 'tse.ca', 'gov.bc.ca']
    },
    'canada': {  # Englische Variante
        'languages': ['en', 'fr'],
        'currency': 'CAD',
        'regions': ['Quebec', 'Ontario', 'British Columbia', 'Alberta', 
                   'Manitoba', 'Saskatchewan', 'Nova Scotia', 'New Brunswick', 
                   'Newfoundland and Labrador', 'Prince Edward Island',
                   'Northwest Territories', 'Yukon', 'Nunavut'],
        'mining_terms': {
            'mine': ['mine', 'site minier', 'project', 'projet', 'property', 'propriété'],
            'operator': ['operator', 'opérateur', 'exploitant', 'betreiber', 'operador'],
            'owner': ['owner', 'propriétaire', 'eigentümer', 'propietario', 'belongs to', 'gehört', 'property of'],
            'commodity': ['commodity', 'produit', 'minerai', 'mineral', 'minéral'],
            'restoration_costs': [
                'restoration costs', 'closure costs', 'reclamation costs', 
                'coûts de restauration', 'coûts de fermeture', 'coûts de réhabilitation',
                'asset retirement obligation', 'ARO', 'obligation de mise hors service',
                'environmental liability', 'passif environnemental', 
                'closure bond', 'garantie financière', 'financial assurance',
                'provision for closure', 'provision pour fermeture',
                'decommissioning costs', 'site rehabilitation', 'mine closure provision',
                'environmental bond', 'reclamation bond', 'security deposit',
                'restoration provision', 'closure liability', 'post-closure costs',
                'remediation costs', 'environmental obligations', 'closure reserve',
                'rehabilitation provision', 'closure financial guarantee',
                'coûts de déclassement', 'provision pour restauration',
                'garantie de fermeture', 'obligations environnementales'
            ]
        },
        'priority_domains': ['mern.gouv.qc.ca', 'nrcan.gc.ca', 'gestim.quebec',
                           'mining.ca', 'sedar.com', 'tse.ca', 'gov.bc.ca']
    },
    'australien': {
        'languages': ['en'],
        'currency': 'AUD',
        'regions': ['Western Australia', 'Queensland', 'New South Wales', 
                   'Victoria', 'South Australia', 'Tasmania', 
                   'Northern Territory'],
        'mining_terms': {
            'mine': ['mine', 'mining operation', 'project', 'property', 'deposit'],
            'operator': ['operator', 'company', 'joint venture', 'JV', 'operates', 'operating company'],
            'owner': ['owner', 'owns', 'ownership', 'property of', 'belongs to', 'held by'],
            'commodity': ['commodity', 'mineral', 'ore', 'resource'],
            'restoration_costs': [
                'restoration costs', 'closure costs', 'reclamation costs',
                'rehabilitation costs', 'asset retirement obligation', 'ARO',
                'environmental liability', 'closure bond', 'financial assurance',
                'provision for closure', 'mine closure provision',
                'rehabilitation bond', 'environmental security deposit',
                'mine rehabilitation fund', 'closure assurance', 'decommissioning provision',
                'rehabilitation liability', 'environmental rehabilitation obligation',
                'closure cost estimate', 'post-mining land use', 'rehabilitation guarantee',
                'environmental performance bond', 'mine closure liability',
                'progressive rehabilitation', 'final rehabilitation costs',
                'care and maintenance costs', 'ongoing monitoring costs'
            ]
        },
        'priority_domains': ['ga.gov.au', 'dmp.wa.gov.au', 'sarig.sa.gov.au', 
                           'minedex.dmirs.wa.gov.au', 'asx.com.au']
    },
    'australia': {  # Englische Variante
        'languages': ['en'],
        'currency': 'AUD',
        'regions': ['Western Australia', 'Queensland', 'New South Wales', 
                   'Victoria', 'South Australia', 'Tasmania', 
                   'Northern Territory'],
        'mining_terms': {
            'mine': ['mine', 'mining operation', 'project', 'property', 'deposit'],
            'operator': ['operator', 'company', 'joint venture', 'JV', 'operates', 'operating company'],
            'owner': ['owner', 'owns', 'ownership', 'property of', 'belongs to', 'held by'],
            'commodity': ['commodity', 'mineral', 'ore', 'resource'],
            'restoration_costs': [
                'restoration costs', 'closure costs', 'reclamation costs',
                'rehabilitation costs', 'asset retirement obligation', 'ARO',
                'environmental liability', 'closure bond', 'financial assurance',
                'provision for closure', 'mine closure provision',
                'rehabilitation bond', 'environmental security deposit',
                'mine rehabilitation fund', 'closure assurance', 'decommissioning provision',
                'rehabilitation liability', 'environmental rehabilitation obligation',
                'closure cost estimate', 'post-mining land use', 'rehabilitation guarantee',
                'environmental performance bond', 'mine closure liability',
                'progressive rehabilitation', 'final rehabilitation costs',
                'care and maintenance costs', 'ongoing monitoring costs'
            ]
        },
        'priority_domains': ['ga.gov.au', 'dmp.wa.gov.au', 'sarig.sa.gov.au', 
                           'minedex.dmirs.wa.gov.au', 'asx.com.au']
    },
    'indonesien': {
        'languages': ['id', 'en'],
        'currency': 'IDR',
        'regions': ['Kalimantan', 'Sulawesi', 'Papua', 'Sumatra', 
                   'Java', 'Nusa Tenggara', 'Maluku'],
        'mining_terms': {
            'mine': ['tambang', 'mine', 'proyek', 'project', 'lokasi penambangan'],
            'operator': ['PT', 'operator', 'perusahaan', 'kontraktor', 'pemegang IUP', 'dioperasikan oleh'],
            'owner': ['pemilik', 'owner', 'dimiliki oleh', 'milik', 'kepemilikan'],
            'commodity': ['komoditas', 'mineral', 'bahan galian', 'sumber daya'],
            'restoration_costs': [
                'biaya reklamasi', 'biaya penutupan tambang', 'restoration costs',
                'jaminan reklamasi', 'dana jaminan', 'closure costs',
                'kewajiban lingkungan', 'environmental liability',
                'provisi penutupan tambang', 'closure provision',
                'biaya rehabilitasi', 'dana cadangan reklamasi',
                'jaminan pasca tambang', 'biaya pemulihan lingkungan',
                'kewajiban reklamasi', 'dana jaminan lingkungan',
                'biaya pengelolaan pasca tambang', 'jaminan kinerja lingkungan',
                'cadangan biaya penutupan', 'kewajiban rehabilitasi',
                'biaya revegetasi', 'dana pemulihan lahan',
                'post-mining obligation', 'environmental bond',
                'rehabilitation fund', 'closure financial guarantee'
            ]
        },
        'priority_domains': ['esdm.go.id', 'minerba.esdm.go.id', 'modi.esdm.go.id',
                           'idx.co.id', 'ptba.co.id', 'antam.com']
    },
    'indonesia': {  # Englische Variante
        'languages': ['id', 'en'],
        'currency': 'IDR',
        'regions': ['Kalimantan', 'Sulawesi', 'Papua', 'Sumatra', 
                   'Java', 'Nusa Tenggara', 'Maluku'],
        'mining_terms': {
            'mine': ['tambang', 'mine', 'proyek', 'project', 'lokasi penambangan'],
            'operator': ['PT', 'operator', 'perusahaan', 'kontraktor', 'pemegang IUP', 'dioperasikan oleh'],
            'owner': ['pemilik', 'owner', 'dimiliki oleh', 'milik', 'kepemilikan'],
            'commodity': ['komoditas', 'mineral', 'bahan galian', 'sumber daya'],
            'restoration_costs': [
                'biaya reklamasi', 'biaya penutupan tambang', 'restoration costs',
                'jaminan reklamasi', 'dana jaminan', 'closure costs',
                'kewajiban lingkungan', 'environmental liability',
                'provisi penutupan tambang', 'closure provision',
                'biaya rehabilitasi', 'dana cadangan reklamasi',
                'jaminan pasca tambang', 'biaya pemulihan lingkungan',
                'kewajiban reklamasi', 'dana jaminan lingkungan',
                'biaya pengelolaan pasca tambang', 'jaminan kinerja lingkungan',
                'cadangan biaya penutupan', 'kewajiban rehabilitasi',
                'biaya revegetasi', 'dana pemulihan lahan',
                'post-mining obligation', 'environmental bond',
                'rehabilitation fund', 'closure financial guarantee'
            ]
        },
        'priority_domains': ['esdm.go.id', 'minerba.esdm.go.id', 'modi.esdm.go.id',
                           'idx.co.id', 'ptba.co.id', 'antam.com']
    }
}