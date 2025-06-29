"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Mining-spezifische Pattern und Extraktionsfunktionen
"""

import re
from typing import Dict, List, Any, Optional


class MiningPatternExtractor:
    """Extrahiert Mining-spezifische Daten aus Text"""
    
    # Mining-Daten Patterns
    PATTERNS = {
        'betreiber': [
            r'operated\s+by\s+([A-Z][^,.]+(?:\s+[A-Z][^,.]+)*)',
            r'operator\s*[:=]\s*([A-Z][^,.]+(?:\s+[A-Z][^,.]+)*)',
            r'company\s*[:=]\s*([A-Z][^,.]+(?:\s+[A-Z][^,.]+)*)'
        ],
        'koordinaten': [
            r'([\d.]+°[\d.]+\'[\d.]*"?[NS])\s*,?\s*([\d.]+°[\d.]+\'[\d.]*"?[EW])',
            r'latitude\s*[:=]\s*([-]?[\d.]+)\s*,?\s*longitude\s*[:=]\s*([-]?[\d.]+)',
            r'coordinates\s*[:=]\s*([-]?[\d.]+)\s*,\s*([-]?[\d.]+)'
        ],
        'jahresproduktion': [
            r'([\d,]+)\s*(?:tonnes?|tons?|ounces?|oz)\s*(?:per\s+year|annually|/year|p\.a\.)',
            r'annual\s+production\s*[:=]\s*([\d,]+)\s*(?:tonnes?|tons?|ounces?|oz)',
            r'production\s+capacity\s*[:=]\s*([\d,]+)\s*(?:tonnes?|tons?|ounces?|oz)'
        ],
        'rohstofftyp': [
            r'commodity\s*[:=]\s*([A-Za-z]+(?:\s+[A-Za-z]+)*)',
            r'mineral\s*[:=]\s*([A-Za-z]+(?:\s+[A-Za-z]+)*)',
            r'producing\s+([A-Za-z]+(?:\s+[A-Za-z]+)*)\s+(?:mine|deposit)'
        ],
        'aktivitaetsstatus': [
            r'status\s*[:=]\s*(active|operating|suspended|closed|care\s+and\s+maintenance)',
            r'mine\s+is\s+(active|operating|suspended|closed|on\s+care\s+and\s+maintenance)',
            r'currently\s+(active|operating|suspended|closed|on\s+care\s+and\s+maintenance)'
        ]
    }
    
    @staticmethod
    def extract_key_data(text: str) -> Dict[str, Any]:
        """Extrahiert wichtige Mining-Daten aus Text"""
        key_data = {}
        
        for field, field_patterns in MiningPatternExtractor.PATTERNS.items():
            for pattern in field_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    if isinstance(matches[0], tuple):
                        key_data[field] = ' '.join(matches[0])
                    else:
                        key_data[field] = matches[0]
                    break
        
        return key_data
    
    @staticmethod
    def extract_coordinates(text: str) -> Optional[str]:
        """Extrahiert Koordinaten aus Text"""
        coord_patterns = [
            r'([\d.]+°[\d.]+\'[\d.]*"?[NS])\s*,?\s*([\d.]+°[\d.]+\'[\d.]*"?[EW])',
            r'latitude\s*[:=]\s*([-]?[\d.]+)\s*,?\s*longitude\s*[:=]\s*([-]?[\d.]+)',
            r'(\d{1,2}°\s*\d{1,2}\'\s*\d{1,2}(?:\.\d+)?"?\s*[NS])\s*,?\s*(\d{1,3}°\s*\d{1,2}\'\s*\d{1,2}(?:\.\d+)?"?\s*[EW])'
        ]
        
        for pattern in coord_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return f"{match.group(1)}, {match.group(2)}"
        
        return None
    
    @staticmethod
    def extract_resource_data(text: str) -> Dict[str, Any]:
        """Extrahiert Ressourcendaten aus Text"""
        resources = {}
        
        resource_types = {
            'measured': r'measured\s+resources?\s*[:=]\s*([\d,]+)\s*(?:tonnes?|tons?|ounces?|oz)',
            'indicated': r'indicated\s+resources?\s*[:=]\s*([\d,]+)\s*(?:tonnes?|tons?|ounces?|oz)',
            'inferred': r'inferred\s+resources?\s*[:=]\s*([\d,]+)\s*(?:tonnes?|tons?|ounces?|oz)'
        }
        
        for resource_type, pattern in resource_types.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                resources[resource_type] = match.group(1)
        
        return resources
    
    @staticmethod
    def extract_cost_data(text: str) -> Dict[str, Any]:
        """Extrahiert Kostendaten aus Text"""
        costs = {}
        
        cost_patterns = {
            'capex': r'capital\s+cost\s*[:=]\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|M)?',
            'opex': r'operating\s+cost\s*[:=]\s*\$?([\d,]+(?:\.\d+)?)\s*(?:per\s+(?:tonne|ton|ounce|oz))?',
            'aisc': r'AISC\s*[:=]\s*\$?([\d,]+(?:\.\d+)?)\s*(?:per\s+(?:ounce|oz))?'
        }
        
        for cost_type, pattern in cost_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                costs[cost_type] = match.group(1)
        
        return costs
    
    @staticmethod
    def extract_environmental_data(text: str) -> Dict[str, Any]:
        """Extrahiert Umweltdaten aus Text"""
        env_data = {}
        
        env_patterns = {
            'sanierungskosten': [
                r'closure\s+cost[s]?\s*[:=]\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|M)?',
                r'rehabilitation\s+cost[s]?\s*[:=]\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|M)?',
                r'environmental\s+bond\s*[:=]\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|M)?'
            ],
            'water_usage': [
                r'water\s+consumption\s*[:=]\s*([\d,]+)\s*(?:m3|cubic\s+meters|litres)',
                r'water\s+usage\s*[:=]\s*([\d,]+)\s*(?:m3|cubic\s+meters|litres)'
            ],
            'land_disturbance': [
                r'disturbed\s+area\s*[:=]\s*([\d,]+(?:\.\d+)?)\s*(?:hectares|ha|km2)',
                r'footprint\s*[:=]\s*([\d,]+(?:\.\d+)?)\s*(?:hectares|ha|km2)'
            ]
        }
        
        for key, patterns in env_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    env_data[key] = matches[0]
                    break
        
        return env_data
    
    @staticmethod
    def extract_technical_data(text: str) -> Dict[str, Any]:
        """Extrahiert technische Daten aus Text"""
        tech_data = {}
        
        tech_patterns = {
            'jahresproduktion': [
                r'annual\s+production\s*[:=]\s*([\d,]+)\s*(?:tonnes|tons|ounces|oz)',
                r'production\s+capacity\s*[:=]\s*([\d,]+)\s*(?:tonnes|tons|ounces|oz)\s*(?:per\s+year|/year|p\.a\.)'
            ],
            'reserve_life': [
                r'mine\s+life\s*[:=]\s*([\d.]+)\s*years',
                r'reserve\s+life\s*[:=]\s*([\d.]+)\s*years'
            ],
            'grade': [
                r'average\s+grade\s*[:=]\s*([\d.]+)\s*(?:%|g/t|ppm)',
                r'head\s+grade\s*[:=]\s*([\d.]+)\s*(?:%|g/t|ppm)'
            ],
            'recovery': [
                r'recovery\s+rate\s*[:=]\s*([\d.]+)\s*%',
                r'metallurgical\s+recovery\s*[:=]\s*([\d.]+)\s*%'
            ]
        }
        
        for key, patterns in tech_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    tech_data[key] = matches[0]
                    break
        
        return tech_data
    
    @staticmethod
    def is_environmental_table(table: Dict) -> bool:
        """Prüft ob eine Tabelle Umweltdaten enthält"""
        env_keywords = [
            'environmental', 'closure', 'rehabilitation', 'water', 
            'emission', 'waste', 'contamination', 'restoration'
        ]
        
        headers = table.get('headers', [])
        headers_text = ' '.join(str(h).lower() for h in headers)
        
        return any(keyword in headers_text for keyword in env_keywords)
    
    @staticmethod
    def is_technical_table(table: Dict) -> bool:
        """Prüft ob eine Tabelle technische Daten enthält"""
        tech_keywords = [
            'production', 'grade', 'recovery', 'tonnage', 'resource',
            'reserve', 'ore', 'mineral', 'capacity', 'throughput'
        ]
        
        headers = table.get('headers', [])
        headers_text = ' '.join(str(h).lower() for h in headers)
        
        return any(keyword in headers_text for keyword in tech_keywords)
    
    @staticmethod
    def find_financial_value(table_data: List[List], keywords: List[str]) -> Optional[str]:
        """Findet Finanzwerte in Tabellendaten"""
        for row in table_data:
            row_text = ' '.join(str(cell).lower() for cell in row)
            
            for keyword in keywords:
                if keyword in row_text:
                    # Suche nach Zahlen in der Zeile
                    for cell in row:
                        cell_str = str(cell)
                        # Muster für Finanzwerte
                        if re.match(r'^\$?[\d,]+(?:\.\d+)?(?:M|million|B|billion)?$', cell_str):
                            return cell_str
        
        return None