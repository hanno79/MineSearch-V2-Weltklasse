"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Utility-Funktionen für Firecrawl Provider
"""

import re
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, urljoin

logger = logging.getLogger(__name__)


class FirecrawlExtractor:
    """Extractor für strukturierte Daten aus gecrawlten Inhalten"""
    
    @staticmethod
    def extract_mining_data(content: str, mine_name: str) -> Dict[str, Any]:
        """Extrahiert Mining-spezifische Daten aus dem Content"""
        
        extracted_data = {}
        
        # Suche nach Koordinaten
        coord_patterns = [
            r'(?:latitude|lat)[:\s]+(-?\d+\.?\d*)',
            r'(?:longitude|lon|lng)[:\s]+(-?\d+\.?\d*)',
            r'(\d+°\s*\d+\'?\s*\d*"?\s*[NS])\s*,?\s*(\d+°\s*\d+\'?\s*\d*"?\s*[EW])',
            r'(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)'  # Decimal degrees
        ]
        
        for pattern in coord_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                if isinstance(matches[0], tuple):
                    extracted_data['coordinates'] = f"{matches[0][0]}, {matches[0][1]}"
                else:
                    extracted_data['coordinates'] = matches[0]
                break
        
        # FIELD-MAPPING-FIX 20.08.2025: Separate Eigentümer and Betreiber extraction
        # Suche nach Eigentümern (Owner)
        owner_patterns = [
            rf'{mine_name}.*?(?:owned|held)\s+by\s+([A-Z][^.]+?)(?:\.|,|\s+and)',
            r'(?:owner|ownership)[:\s]+([A-Z][^.\n]+)',
            rf'([A-Z][^.]+?)\s+(?:owns|holds)\s+{mine_name}',
            r'(?:propriétaire|eigentümer)[:\s]+([A-Z][^.\n]+)',
            r'(?:property|eigentum)\s+of\s+([A-Z][^.\n]+)'
        ]
        
        for pattern in owner_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                extracted_data['owner'] = match.group(1).strip()
                break
        
        # Suche nach Betreibern (Operator) - SEPARATE extraction
        operator_patterns = [
            rf'{mine_name}.*?(?:operated|managed)\s+by\s+([A-Z][^.]+?)(?:\.|,|\s+and)',
            r'(?:operator|operating|management)[:\s]+([A-Z][^.\n]+)',
            rf'([A-Z][^.]+?)\s+(?:operates|manages)\s+{mine_name}',
            r'(?:exploitant|betreiber)[:\s]+([A-Z][^.\n]+)',
            r'(?:operated|managed)\s+by\s+([A-Z][^.\n]+)'
        ]
        
        for pattern in operator_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                extracted_data['operator'] = match.group(1).strip()
                break
        
        # Suche nach Restoration/Closure Costs
        cost_patterns = [
            r'(?:closure|restoration|remediation|reclamation)\s+(?:cost|liability|bond)[s]?[:\s]+\$?([\d,]+(?:\.\d+)?)\s*(?:million|billion|M|B)?',
            r'\$?([\d,]+(?:\.\d+)?)\s*(?:million|billion|M|B)?\s+(?:for|in)\s+(?:closure|restoration|remediation)',
            r'ARO[:\s]+\$?([\d,]+(?:\.\d+)?)\s*(?:million|billion|M|B)?'
        ]
        
        for pattern in cost_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                cost_str = match.group(1).replace(',', '')
                # FIX 02.09.2025: Robust type checking für match.group(0).lower()
                unit = match.group(0).lower() if match.group(0) is not None else ""
                if 'billion' in unit or ' b' in unit:
                    cost = float(cost_str) * 1000  # Convert to millions
                else:
                    cost = float(cost_str)
                extracted_data['restoration_cost'] = f"${cost:.1f}M"
                break
        
        # Suche nach Rohstoffen
        commodity_patterns = [
            r'(?:produces?|mining|extracts?|commodity|commodities)[:\s]+([^.\n]+(?:gold|silver|copper|coal|iron|zinc|lead|nickel|uranium|lithium)[^.\n]*)',
            r'(gold|silver|copper|coal|iron|zinc|lead|nickel|uranium|lithium)\s+(?:mine|mining|production)',
        ]
        
        for pattern in commodity_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                commodities = []
                for match in matches:
                    # FIX 02.09.2025: Robust type checking vor .lower() call
                    match_str = str(match) if match is not None else ""
                    for commodity in ['gold', 'silver', 'copper', 'coal', 'iron', 'zinc', 'lead', 'nickel', 'uranium', 'lithium']:
                        if commodity in match_str.lower():
                            commodities.append(commodity.capitalize())
                if commodities:
                    extracted_data['commodities'] = list(set(commodities))
                break
        
        # Suche nach Status
        status_patterns = [
            r'(?:status|operation)[:\s]+(\w+)',
            r'(operational|operating|active|closed|suspended|abandoned|care\s+and\s+maintenance)',
            r'(?:mine|project)\s+is\s+(?:currently\s+)?(\w+)'
        ]
        
        for pattern in status_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                status = match.group(1).strip()
                extracted_data['status'] = status.capitalize()
                break
        
        return extracted_data
    
    @staticmethod
    def convert_dms_to_decimal(dms_string: str) -> Optional[float]:
        """Konvertiert DMS (Degrees Minutes Seconds) zu Dezimalgrad"""
        try:
            # Pattern für DMS: 49°30'45"N oder 49° 30' 45" N
            pattern = r'(\d+)°\s*(\d+)\'?\s*(\d+(?:\.\d+)?)\"?\s*([NSEW])'
            match = re.match(pattern, dms_string.strip())
            
            if match:
                degrees = float(match.group(1))
                minutes = float(match.group(2))
                seconds = float(match.group(3))
                direction = match.group(4)
                
                decimal = degrees + minutes/60 + seconds/3600
                
                if direction in ['S', 'W']:
                    decimal = -decimal
                    
                return decimal
        except (ValueError, AttributeError) as e:
            logger.debug(f"[FIRECRAWL] DMS-Parsing-Fehler für '{dms_string}': {e}")
        except Exception as e:
            logger.warning(f"[FIRECRAWL] Unerwarteter Fehler bei DMS-Konvertierung: {e}")
        return None


class FirecrawlDataProcessor:
    """Prozessor für Firecrawl-Daten"""
    
    @staticmethod
    def process_crawled_data(crawled_data: List[Dict], mine_name: str) -> Dict[str, Any]:
        """Verarbeitet gecrawlte Daten und extrahiert strukturierte Informationen"""
        
        aggregated_content = '\n\n'.join([item['markdown'] for item in crawled_data])
        
        # Verwende Extractor
        extractor = FirecrawlExtractor()
        extracted_data = extractor.extract_mining_data(aggregated_content, mine_name)
        
        # FIELD-MAPPING-FIX 20.08.2025: Corrected field mapping
        # Strukturiere Daten für MineSearch Format
        structured_data = {
            'Name': mine_name,
            'Eigentümer': extracted_data.get('owner', ''),          # Owner -> Eigentümer (correct)
            'Betreiber': extracted_data.get('operator', ''),        # FIXED: Operator -> Betreiber
            'Restaurationskosten': extracted_data.get('restoration_cost', ''),
            'Rohstoffabbau': ', '.join(extracted_data.get('commodities', [])),
            'Aktivitätsstatus': extracted_data.get('status', '')
        }
        
        # Verarbeite Koordinaten
        if 'coordinates' in extracted_data:
            coords = extracted_data['coordinates']
            if ',' in coords:
                parts = coords.split(',')
                if len(parts) == 2:
                    structured_data['x-Koordinate'] = parts[1].strip()
                    structured_data['y-Koordinate'] = parts[0].strip()
            else:
                # Möglicherweise DMS Format
                decimal = extractor.convert_dms_to_decimal(coords)
                if decimal:
                    structured_data['y-Koordinate'] = str(decimal)
        
        # Entferne leere Felder
        structured_data = {k: v for k, v in structured_data.items() if v}
        
        return structured_data
    
    @staticmethod
    def build_crawl_params(url: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Erstellt Crawl-Parameter basierend auf URL und Optionen"""
        
        mine_name = options.get('mine_name', '')
        
        # Basis-Parameter
        params = {
            'url': url,
            'limit': 10,
            'scrapeOptions': {
                'formats': ['markdown', 'html'],
                'onlyMainContent': True,
                'includeHtml': False
            }
        }
        
        # Füge includePaths hinzu wenn mine_name vorhanden
        if mine_name:
            # Erstelle URL-Patterns die den Minennamen enthalten könnten
            mine_slug = mine_name.lower().replace(' ', '-')
            mine_underscore = mine_name.lower().replace(' ', '_')
            
            params['includePaths'] = [
                f"*{mine_slug}*",
                f"*{mine_underscore}*",
                f"*{mine_name.lower()}*",
                "*mining*",
                "*operations*",
                "*projects*"
            ]
        
        # Spezielle Behandlung für bekannte Mining-Websites
        domain = urlparse(url).netloc.lower()
        if 'mining.com' in domain:
            params['includePaths'].extend(["*/companies/*", "*/mines/*"])
        elif 'infomine.com' in domain:
            params['includePaths'].extend(["*/properties/*", "*/mines/*"])
            
        return params