"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Research-Verarbeitung für DeepSeek Agent
"""

import re
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from .models import ResearchStep, ExtractionResult, AdaptationStrategy, ResearchContext
from ..base_agent import MineQuery, SearchResult
from src.core.logger import get_logger


class ResearchProcessor:
    """Verarbeitet Research-Pläne und -Ergebnisse"""
    
    def __init__(self, logger=None):
        self.logger = logger or get_logger("research_processor")
        
    async def create_research_plan(self, query: MineQuery, model_response: str) -> List[ResearchStep]:
        """Erstellt strukturierten Research-Plan aus Modell-Antwort"""
        try:
            # Extrahiere JSON aus Response
            if isinstance(model_response, str):
                json_match = re.search(r'\[.*\]', model_response, re.DOTALL)
                if json_match:
                    plan_data = json.loads(json_match.group())
                else:
                    return self.create_fallback_plan(query)
            else:
                plan_data = model_response
            
            # Konvertiere zu ResearchStep Objekten
            research_steps = []
            for step_data in plan_data[:5]:  # Max 5 Schritte
                step = ResearchStep(
                    objective=step_data.get("objective", ""),
                    strategy=step_data.get("strategy", ""),
                    sources=step_data.get("sources", []),
                    keywords=step_data.get("keywords", []),
                    expected_data=step_data.get("expected_data", []),
                    priority=step_data.get("priority", "medium")
                )
                research_steps.append(step)
            
            return research_steps
            
        except Exception as e:
            self.logger.error(f"Fehler beim Parsen des Research-Plans: {e}")
            return self.create_fallback_plan(query)
    
    def create_fallback_plan(self, query: MineQuery) -> List[ResearchStep]:
        """Erstellt Fallback Research-Plan"""
        return [
            ResearchStep(
                objective="Find basic mine information and operator",
                strategy="Search government databases and company websites",
                sources=["government", "company"],
                keywords=[f'"{query.mine_name}" operator owner company'],
                expected_data=["betreiber", "operator", "status"],
                priority="high"
            ),
            ResearchStep(
                objective="Locate technical and production data",
                strategy="Search technical reports and industry publications",
                sources=["technical", "industry"],
                keywords=[f'"{query.mine_name}" production capacity technical report'],
                expected_data=["koordinaten", "produktion", "rohstofftyp"],
                priority="medium"
            ),
            ResearchStep(
                objective="Find environmental and financial information",
                strategy="Search environmental assessments and financial reports",
                sources=["environmental", "financial"],
                keywords=[f'"{query.mine_name}" environmental impact remediation costs'],
                expected_data=["sanierungskosten", "umweltauswirkungen"],
                priority="low"
            )
        ]
    
    def extract_structured_data(self, response: str, query: MineQuery, 
                              step: ResearchStep) -> List[SearchResult]:
        """Extrahiert strukturierte Daten aus Modell-Response"""
        results = []
        
        try:
            # Versuche verschiedene Extraktionsmethoden
            
            # 1. JSON-basierte Extraktion
            json_results = self._extract_json_data(response)
            if json_results:
                for item in json_results:
                    if self._is_relevant_to_step(item, step):
                        result = self._convert_to_search_result(item, query)
                        if result:
                            results.append(result)
            
            # 2. Pattern-basierte Extraktion
            pattern_results = self._extract_pattern_data(response, step.expected_data)
            results.extend(pattern_results)
            
            # 3. Keyword-basierte Extraktion
            keyword_results = self._extract_keyword_data(response, query, step)
            results.extend(keyword_results)
            
            # Dedupliziere Ergebnisse
            results = self._deduplicate_results(results)
            
        except Exception as e:
            self.logger.error(f"Fehler bei Datenextraktion: {e}")
        
        return results
    
    def adapt_research_plan(self, remaining_steps: List[ResearchStep],
                          recent_findings: List[SearchResult],
                          query: MineQuery) -> Tuple[List[ResearchStep], AdaptationStrategy]:
        """Passt Research-Plan basierend auf Ergebnissen an"""
        
        # Analysiere bisherige Ergebnisse
        found_fields = set(r.field_name for r in recent_findings)
        missing_fields = set(query.required_fields) - found_fields
        
        # Bestimme Anpassungsstrategie
        if not missing_fields:
            # Alle Felder gefunden - keine Anpassung nötig
            strategy = AdaptationStrategy(
                missing_fields=[],
                found_fields=list(found_fields),
                confidence_threshold=0.8,
                max_retries=1,
                adaptation_type="complete"
            )
            return remaining_steps, strategy
        
        # Analysiere Confidence der gefundenen Felder
        avg_confidence = sum(r.confidence_score for r in recent_findings) / len(recent_findings) if recent_findings else 0
        
        if avg_confidence < 0.5:
            # Niedrige Confidence - erweitere Suche
            adaptation_type = "expand"
        elif len(missing_fields) > len(found_fields):
            # Viele fehlende Felder - ändere Strategie
            adaptation_type = "pivot"
        else:
            # Wenige fehlende Felder - verfeinere Suche
            adaptation_type = "refine"
        
        strategy = AdaptationStrategy(
            missing_fields=list(missing_fields),
            found_fields=list(found_fields),
            confidence_threshold=0.7,
            max_retries=2,
            adaptation_type=adaptation_type
        )
        
        # Modifiziere verbleibende Schritte
        adapted_steps = self._modify_steps_based_on_strategy(
            remaining_steps, strategy, query
        )
        
        return adapted_steps, strategy
    
    def create_step_prompt(self, step: ResearchStep, context: ResearchContext) -> str:
        """Erstellt optimierten Prompt für einen Research-Schritt"""
        return f"""Research Task: {step.objective}

{context.to_prompt_context()}
Strategy: {step.strategy}

Search using these keywords: {', '.join(step.keywords)}
Focus on these sources: {', '.join(step.sources)}
Extract data for: {', '.join(step.expected_data)}

Provide detailed findings with:
1. Specific data values found
2. Source of information
3. Confidence level (0-1)
4. Date/year of information
5. Any contradictions or uncertainties

Format findings as structured JSON data."""
    
    def create_adaptation_prompt(self, strategy: AdaptationStrategy, 
                               context: ResearchContext) -> str:
        """Erstellt Prompt für Plan-Anpassung"""
        return f"""Adapt research strategy for: {context.mine_name}

Current situation:
- Found fields: {', '.join(strategy.found_fields)}
- Missing fields: {', '.join(strategy.missing_fields)}
- Adaptation type: {strategy.adaptation_type}

Create {3 - len(strategy.found_fields)} new research steps focusing on missing fields.
Prioritize: {', '.join(strategy.missing_fields[:3])}

Consider alternative sources and search strategies.
Return as JSON array of research steps."""
    
    # Private Hilfsmethoden
    def _extract_json_data(self, response: str) -> List[Dict[str, Any]]:
        """Extrahiert JSON-Daten aus Response"""
        results = []
        
        # Suche nach JSON-Strukturen
        json_patterns = [
            r'\{[^{}]*\}',  # Einfache JSON-Objekte
            r'\[[^\[\]]*\]'  # JSON-Arrays
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, response)
            for match in matches:
                try:
                    data = json.loads(match)
                    if isinstance(data, dict):
                        results.append(data)
                    elif isinstance(data, list):
                        results.extend([d for d in data if isinstance(d, dict)])
                except:
                    continue
        
        return results
    
    def _extract_pattern_data(self, response: str, expected_fields: List[str]) -> List[SearchResult]:
        """Extrahiert Daten basierend auf Patterns"""
        results = []
        
        # Field-spezifische Patterns
        patterns = {
            "koordinaten": r"(?:coordinates?|GPS|lat.*?lon).*?(\d+\.?\d*)[°\s,]+(\d+\.?\d*)",
            "coordinates": r"(?:coordinates?|GPS|lat.*?lon).*?(\d+\.?\d*)[°\s,]+(\d+\.?\d*)",
            "sanierungskosten": r"(?:remediation|closure|restoration).*?costs?.*?(\d+[\d,]*\.?\d*)\s*(?:million|USD|EUR|CAD)",
            "remediation_costs": r"(?:remediation|closure|restoration).*?costs?.*?(\d+[\d,]*\.?\d*)\s*(?:million|USD|EUR|CAD)",
            "produktion": r"(?:production|capacity).*?(\d+[\d,]*\.?\d*)\s*(?:tons?|tonnes?|t\/year|tpa)",
            "production": r"(?:production|capacity).*?(\d+[\d,]*\.?\d*)\s*(?:tons?|tonnes?|t\/year|tpa)"
        }
        
        for field in expected_fields:
            if field in patterns:
                matches = re.finditer(patterns[field], response, re.IGNORECASE)
                for match in matches:
                    value = match.group(0)
                    results.append(SearchResult(
                        field_name=field,
                        value=value,
                        source="DeepSeek pattern extraction",
                        confidence_score=0.7,
                        metadata={"extraction_method": "pattern"}
                    ))
        
        return results
    
    def _extract_keyword_data(self, response: str, query: MineQuery, 
                            step: ResearchStep) -> List[SearchResult]:
        """Extrahiert Daten basierend auf Keywords"""
        results = []
        
        # Suche nach Feld-Wert Paaren
        for field in step.expected_data:
            # Verschiedene Schreibweisen des Feldes
            field_variations = [field, field.replace("_", " "), field.title()]
            
            for variation in field_variations:
                # Suche nach "Field: Value" Mustern
                pattern = rf"{variation}:?\s*([^\n,;]+)"
                matches = re.finditer(pattern, response, re.IGNORECASE)
                
                for match in matches:
                    value = match.group(1).strip()
                    if value and len(value) > 2:
                        results.append(SearchResult(
                            field_name=field,
                            value=value,
                            source=f"DeepSeek - {step.objective}",
                            confidence_score=0.6,
                            metadata={
                                "extraction_method": "keyword",
                                "step": step.objective
                            }
                        ))
        
        return results
    
    def _is_relevant_to_step(self, data: Dict[str, Any], step: ResearchStep) -> bool:
        """Prüft ob Daten zu Research-Schritt passen"""
        # Prüfe ob eines der erwarteten Felder vorhanden ist
        data_keys = set(k.lower() for k in data.keys())
        expected_keys = set(f.lower() for f in step.expected_data)
        
        return bool(data_keys & expected_keys)
    
    def _convert_to_search_result(self, data: Dict[str, Any], query: MineQuery) -> Optional[SearchResult]:
        """Konvertiert extrahierte Daten zu SearchResult"""
        # Finde passendes Feld
        field_mapping = {
            "operator": "betreiber",
            "owner": "betreiber",
            "coordinates": "koordinaten",
            "gps": "koordinaten",
            "production": "produktion",
            "capacity": "produktion",
            "commodity": "rohstofftyp",
            "mineral": "rohstofftyp",
            "status": "aktivitaetsstatus",
            "remediation": "sanierungskosten",
            "closure_costs": "sanierungskosten"
        }
        
        for key, value in data.items():
            field = field_mapping.get(key.lower(), key.lower())
            
            if field in query.required_fields:
                return SearchResult(
                    field_name=field,
                    value=value,
                    source=data.get("source", "DeepSeek Research"),
                    confidence_score=float(data.get("confidence", 0.7)),
                    metadata=data
                )
        
        return None
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Entfernt Duplikate und behält beste Version"""
        unique_results = {}
        
        for result in results:
            key = (result.field_name, str(result.value).lower().strip())
            
            if key not in unique_results:
                unique_results[key] = result
            else:
                # Behalte Version mit höherer Confidence
                if result.confidence_score > unique_results[key].confidence_score:
                    unique_results[key] = result
        
        return list(unique_results.values())
    
    def _modify_steps_based_on_strategy(self, steps: List[ResearchStep],
                                       strategy: AdaptationStrategy,
                                       query: MineQuery) -> List[ResearchStep]:
        """Modifiziert Schritte basierend auf Anpassungsstrategie"""
        if strategy.adaptation_type == "expand":
            # Erweitere Keywords und Quellen
            for step in steps:
                step.keywords.extend([
                    f'"{query.mine_name}" {field}' 
                    for field in strategy.missing_fields[:2]
                ])
                step.sources.extend(["academic", "news", "social"])
        
        elif strategy.adaptation_type == "pivot":
            # Füge neue Schritte für fehlende Felder hinzu
            for field in strategy.missing_fields[:2]:
                new_step = ResearchStep(
                    objective=f"Find specific information about {field}",
                    strategy="Focused search on specialized sources",
                    sources=["government", "technical", "academic"],
                    keywords=[f'"{query.mine_name}" {field} {query.country}'],
                    expected_data=[field],
                    priority="high"
                )
                steps.insert(0, new_step)
        
        elif strategy.adaptation_type == "refine":
            # Verfeinere bestehende Schritte
            for step in steps:
                step.expected_data = [
                    f for f in step.expected_data 
                    if f in strategy.missing_fields
                ]
                step.priority = "high"
        
        return steps