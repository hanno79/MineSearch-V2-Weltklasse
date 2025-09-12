"""
Author: rahn
Datum: 24.08.2025
Version: 1.0
Beschreibung: Provider Status und API-Key Validierung
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter
import aiohttp
import time

from minesearch.config.base import config
from minesearch.providers.registry import provider_registry

logger = logging.getLogger(__name__)
router = APIRouter()

class ProviderStatusChecker:
    """Umfassende Provider-Status und API-Key Validierung"""

    def __init__(self):
        """__init__ - TODO: Dokumentation hinzufügen"""
        self.test_results = {}

    async def check_provider_health(self, provider_name: str, api_key: str) -> Dict[str, Any]:
        """Führe einen echten API-Health-Check für einen Provider durch"""

        # Basis-Status
        status = {
            'provider': provider_name,
            'api_key_present': bool(api_key and len(api_key) > 10),
            'api_key_format_valid': False,
            'api_accessible': False,
            'budget_available': False,
            'response_time_ms': None,
            'error_message': None,
            'last_checked': time.time(),
            'status': 'unknown'
        }

        # Format-Validierung
        if api_key:
            status['api_key_format_valid'] = self._validate_api_key_format(provider_name, api_key)

        if not status['api_key_format_valid']:
            status['status'] = 'invalid_key'
            return status

        # Echte API-Tests
        try:
            start_time = time.time()
            test_result = await self._test_provider_api(provider_name, api_key)
            response_time = (time.time() - start_time) * 1000

            status['response_time_ms'] = round(response_time, 2)
            status['api_accessible'] = test_result['accessible']
            status['budget_available'] = test_result['budget_ok']
            status['error_message'] = test_result.get('error')

            if status['api_accessible'] and status['budget_available']:
                status['status'] = 'healthy'
            elif status['api_accessible']:
                status['status'] = 'budget_exceeded'
            else:
                status['status'] = 'api_error'

        except Exception as e:
            status['error_message'] = str(e)
            status['status'] = 'connection_error'

        return status

    def _validate_api_key_format(self, provider_name: str, api_key: str) -> bool:
        """Validiere API-Key Format für verschiedene Provider"""

        format_rules = {
            'openrouter': api_key.startswith('sk-or-'),
            'openai': api_key.startswith('sk-'),
            'anthropic': api_key.startswith('sk-ant-'),
            'perplexity': api_key.startswith('pplx-'),
            'grok': api_key.startswith('xai-'),
            'gemini': api_key.startswith('AIza'),
            'deepseek': api_key.startswith('sk-'),
            # Andere Provider haben meist weniger strenge Format-Regeln
            'tavily': len(api_key) > 15,
            'exa': len(api_key) > 15,
            # 'abacus': len(api_key) > 10,  # ENTFERNT 02.09.2025: Abacus Provider entfernt
            'scrapingbee': len(api_key) > 20,
            'firecrawl': api_key.startswith('fc-'),
            'brightdata': len(api_key) > 30
        }

        return format_rules.get(provider_name, len(api_key) > 10)

    async def _test_provider_api(self, provider_name: str, api_key: str) -> Dict[str, Any]:
        """Führe einen echten API-Test durch"""

        test_configs = {
            'openrouter': {
                'url': 'https://openrouter.ai/api/v1/models',
                'headers': {'Authorization': f'Bearer {api_key}'},
                'method': 'GET',
                'budget_check': lambda r: True  # OpenRouter hat selten Budget-Limits
            },
            'openai': {
                'url': 'https://api.openai.com/v1/models',
                'headers': {'Authorization': f'Bearer {api_key}'},
                'method': 'GET',
                'budget_check': lambda r: 'insufficient_quota' not in str(r)
            },
            'anthropic': {
                'url': 'https://api.anthropic.com/v1/messages',
                'headers': {
                    'x-api-key': api_key,
                    'Content-Type': 'application/json',
                    'anthropic-version': '2023-06-01'
                },
                'method': 'POST',
                'data': {
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "hi"}]
                },
                'budget_check': lambda r: 'insufficient_quota' not in str(r) and 'rate_limit' not in str(r)
            },
            'perplexity': {
                'url': 'https://api.perplexity.ai/chat/completions',
                'headers': {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
                'method': 'POST',
                'data': {
                    "model": "llama-3.1-sonar-small-128k-online",
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 1
                },
                'budget_check': lambda r: 'rate_limit' not in str(r)
            },
            'gemini': {
                'url': f'https://generativelanguage.googleapis.com/v1/models?key={api_key}',
                'headers': {},
                'method': 'GET',
                'budget_check': lambda r: 'quotaExceeded' not in str(r)
            },
            'grok': {
                'url': 'https://api.x.ai/v1/chat/completions',
                'headers': {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
                'method': 'POST',
                'data': {
                    "model": "grok-beta",
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 1
                },
                'budget_check': lambda r: 'insufficient_quota' not in str(r)
            },
            # API-TEST-FIX 29.08.2025: Füge Tavily, Abacus und Exa Test-Konfigurationen hinzu
            'tavily': {
                'url': 'https://api.tavily.com/search',
                'headers': {'Content-Type': 'application/json'},
                'method': 'POST',
                'data': {
                    'api_key': api_key,
                    'query': 'test mining',
                    'max_results': 1,
                    'search_depth': 'basic'
                },
                'budget_check': lambda r: 'pay-as-you-go limit' not in str(r) and 'quota' not in str(r)
            },
            # 'abacus': {  # ENTFERNT 02.09.2025: Abacus Provider entfernt
            #     'url': 'https://api.abacus.ai/api/v0/listProjects',
            #     'headers': {'apiKey': api_key, 'Content-Type': 'application/json'},
            #     'method': 'GET',
            #     'budget_check': lambda r: 'insufficient_quota' not in str(r) and 'rate_limit' not in str(r) and 'authentication' not in str(r).lower()
            # },
            'exa': {
                'url': 'https://api.exa.ai/search',  # EXA-TEST-FIX 29.08.2025: Exa Neural Search API
                'headers': {'x-api-key': api_key, 'Content-Type': 'application/json'},
                'method': 'POST',
                'data': {
                    'query': 'test mining data',
                    'num_results': 1,
                    'type': 'neural'
                },
                'budget_check': lambda r: 'quota' not in str(r).lower() and 'limit' not in str(r).lower()
            }
        }

        # Standard-Test für Provider ohne spezielle Konfiguration
        if provider_name not in test_configs:
            return {'accessible': True, 'budget_ok': True, 'error': 'No specific test available'}

        provider_config = test_configs[provider_name]

        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:

                if provider_config['method'] == 'GET':
                    async with session.get(
                        provider_config['url'],
                        headers=provider_config['headers']
                    ) as response:
                        text = await response.text()

                        if response.status == 200:
                            budget_ok = provider_config['budget_check'](text)
                            return {'accessible': True, 'budget_ok': budget_ok}
                        elif response.status == 401:
                            return {'accessible': False, 'budget_ok': False, 'error': 'Invalid API key'}
                        elif response.status == 429:
                            return {'accessible': True, 'budget_ok': False, 'error': 'Rate limit exceeded'}
                        elif response.status in [402, 433]:  # BUDGET-FIX 29.08.2025: Erkenne Budget-Limits auch bei GET
                            budget_ok = provider_config['budget_check'](text)
                            if not budget_ok:
                                return {'accessible': True, 'budget_ok': False, 'error': f'Budget exceeded (HTTP {response.status})'}
                            return {'accessible': False, 'budget_ok': False, 'error': f'HTTP {response.status}'}
                        else:
                            return {'accessible': False, 'budget_ok': False, 'error': f'HTTP {response.status}'}

                elif provider_config['method'] == 'POST':
                    async with session.post(
                        provider_config['url'],
                        headers=provider_config['headers'],
                        json=provider_config.get("data", {})
                    ) as response:
                        text = await response.text()

                        if response.status in [200, 201]:
                            budget_ok = provider_config['budget_check'](text)
                            return {'accessible': True, 'budget_ok': budget_ok}
                        elif response.status == 401:
                            return {'accessible': False, 'budget_ok': False, 'error': 'Invalid API key'}
                        elif response.status == 429:
                            return {'accessible': True, 'budget_ok': False, 'error': 'Rate limit exceeded'}
                        elif response.status in [402, 433]:  # BUDGET-FIX 29.08.2025: Erkenne Budget-Limits
                            budget_ok = provider_config['budget_check'](text)
                            if not budget_ok:
                                return {'accessible': True, 'budget_ok': False, 'error': f'Budget exceeded (HTTP {response.status})'}
                            return {'accessible': False, 'budget_ok': False, 'error': f'HTTP {response.status}: {text[:200]}'}
                        else:
                            return {'accessible': False, 'budget_ok': False, 'error': f'HTTP {response.status}: {text[:200]}'}

        except asyncio.TimeoutError:
            return {'accessible': False, 'budget_ok': False, 'error': 'Connection timeout'}
        except Exception as e:
            return {'accessible': False, 'budget_ok': False, 'error': str(e)}

    async def check_all_providers(self) -> Dict[str, Any]:
        """Prüfe alle konfigurierten Provider"""

        logger.info("[PROVIDER-STATUS] 🔍 Starte umfassende Provider-Validierung...")

        # API-Keys nur für aktive Provider (OpenRouter-geroutete Provider ausgeschlossen)
        # PROVIDER-FIX-V3 29.08.2025: Entferne deaktivierte Provider die über OpenRouter laufen
        api_keys = {
            'openrouter': config.OPENROUTER_API_KEY,  # Hauptprovider für alle Premium-Modelle
            'tavily': config.TAVILY_API_KEY,          # Web-Search Provider
            'exa': config.EXA_API_KEY,                # Neural Search Provider
            'scrapingbee': config.SCRAPINGBEE_API_KEY,  # Scraping Provider
            'firecrawl': config.FIRECRAWL_API_KEY,      # Crawling Provider
            'brightdata': config.BRIGHTDATA_API_KEY,    # Data Provider
            # Die folgenden Provider sind DEAKTIVIERT und laufen über OpenRouter:
            # 'perplexity': über OpenRouter geroutet
            # 'openai': über OpenRouter geroutet
            # 'anthropic': über OpenRouter geroutet
            # 'gemini': über OpenRouter geroutet
            # 'grok': über OpenRouter geroutet
            # 'deepseek': über OpenRouter geroutet
        }

        # Parallel-Tests für alle Provider
        tasks = []
        for provider_name, api_key in api_keys.items():
            if api_key:  # Nur wenn API-Key gesetzt
                task = self.check_provider_health(provider_name, api_key)
                tasks.append(task)
            else:
                # Sofortige Kennzeichnung als fehlend
                self.test_results[provider_name] = {
                    'provider': provider_name,
                    'api_key_present': False,
                    'api_key_format_valid': False,
                    'api_accessible': False,
                    'budget_available': False,
                    'response_time_ms': None,
                    'error_message': 'API key not configured',
                    'status': 'no_api_key',
                    'last_checked': time.time()
                }

        # Ausführen aller Tests
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"[PROVIDER-STATUS] Test fehlgeschlagen: {result}")
                else:
                    self.test_results[result['provider']] = result

        # Statistiken
        total_providers = len(api_keys)
        healthy_providers = len([r for r in self.test_results.values() if r['status'] == 'healthy'])
        providers_with_keys = len([r for r in self.test_results.values() if r['api_key_present']])

        summary = {
            'total_providers': total_providers,
            'providers_with_api_keys': providers_with_keys,
            'healthy_providers': healthy_providers,
            'provider_details': self.test_results,
            'check_timestamp': time.time()
        }

        # API-KEY-LOGGING FIX 29.08.2025: Detaillierteres Logging für fehlende API-Keys
        missing_keys = len([r for r in self.test_results.values() if r['status'] == 'no_api_key'])
        api_errors = len([r for r in self.test_results.values() if r['status'] in ['api_error',
'invalid_key', 'connection_error']])

        logger.info(f"[PROVIDER-STATUS] ✅ Validierung abgeschlossen: {healthy_providers}/{total_providers} Provider funktionsfähig")
        if missing_keys > 0:
            logger.warning(f"[PROVIDER-STATUS] ⚠️ {missing_keys} Provider ohne API-Key: {[k for k, v in self.test_results.items() if v['status'] == 'no_api_key']}")
        if api_errors > 0:
            logger.warning(f"[PROVIDER-STATUS] ❌ {api_errors} Provider mit API-Fehlern: {[k for k, v in self.test_results.items() if v['status'] in ['api_error', 'invalid_key', 'connection_error']]}" )

        return summary

# Globale Instanz
provider_checker = ProviderStatusChecker()

@router.get("/provider-status")
async def get_provider_status():
    """API-Endpoint für Provider-Status-Übersicht"""

    try:
        status_report = await provider_checker.check_all_providers()

        # PROVIDER-DISPLAY-FIX-V3 29.08.2025: Verbesserte Status-Anzeige mit OpenRouter-Info
        missing_keys_count = len([r for r in status_report['provider_details'].values() if r['status'] == 'no_api_key'])
        api_error_count = len([r for r in status_report['provider_details'].values() if r['status']
in ['api_error', 'invalid_key', 'connection_error']])
        budget_issues_count = len([r for r in status_report['provider_details'].values() if
r['status'] == 'budget_exceeded'])

        # Berechne OpenRouter-geroutete Provider
        openrouter_routed_models = ['perplexity', 'openai', 'anthropic', 'gemini', 'grok', 'deepseek']
        openrouter_status = status_report['provider_details'].get('openrouter', {}).get('status', 'unknown')
        openrouter_models_available = len(openrouter_routed_models) if openrouter_status == 'healthy' else 0

        status_message = f"{status_report['healthy_providers']}/{status_report['total_providers']} Provider verfügbar"

        # Füge OpenRouter-Info hinzu
        if openrouter_models_available > 0:
            status_message += f" (inkl. {openrouter_models_available} über OpenRouter)"

        # Füge Problem-Info hinzu
        problems = []
        if budget_issues_count > 0:
            problems.append(f"{budget_issues_count} Budget-Limit")
        if api_error_count > 0:
            problems.append(f"{api_error_count} API-Fehler")
        if missing_keys_count > 0:
            problems.append(f"{missing_keys_count} ohne API-Key")

        if problems:
            status_message += f" | Probleme: {', '.join(problems)}"

        return {
            "success": True,
            "data": status_report,
            "message": status_message
        }

    except Exception as e:
        logger.error(f"[PROVIDER-STATUS] Fehler bei Status-Check: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Provider-Status-Check fehlgeschlagen"
        }

@router.get("/available-models")
async def get_available_models():
    """API-Endpoint für verfügbare Modelle basierend auf Provider-Status"""

    try:
        # Hole aktuellen Provider-Status
        status_report = await provider_checker.check_all_providers()

        # Sammle verfügbare Modelle von gesunden Providern
        available_models = {}
        unavailable_models = {}

        for provider_name, provider_status in status_report['provider_details'].items():

            # Hole Modelle für diesen Provider aus der Registry
            provider_instance = provider_registry.get_provider(provider_name)
            if not provider_instance:
                continue

            provider_models = provider_instance.get_models()

            for model_key, model_config in provider_models.items():
                full_model_id = f"{provider_name}:{model_key}"

                if provider_status['status'] == 'healthy':
                    available_models[full_model_id] = {
                        'name': model_config.name,
                        'description': model_config.description,
                        'provider': provider_name,
                        'provider_status': 'healthy',
                        # ÄNDERUNG 24.08.2025: Provider-Kategorie für Premium-Model UI-Gruppierung
                        'provider_category': getattr(model_config, 'provider_category', None)
                    }
                else:
                    unavailable_models[full_model_id] = {
                        'name': model_config.name,
                        'description': model_config.description,
                        'provider': provider_name,
                        'provider_status': provider_status['status'],
                        'error': provider_status.get("error_message", 'Provider nicht verfügbar'),
                        # ÄNDERUNG 24.08.2025: Provider-Kategorie für Premium-Model UI-Gruppierung
                        'provider_category': getattr(model_config, 'provider_category', None)
                    }

        return {
            "success": True,
            "data": {
                "available_models": available_models,
                "unavailable_models": unavailable_models,
                "summary": {
                    "total_available": len(available_models),
                    "total_unavailable": len(unavailable_models),
                    "healthy_providers": status_report['healthy_providers'],
                    "total_providers": status_report['total_providers']
                }
            }
        }

    except Exception as e:
        logger.error(f"[AVAILABLE-MODELS] Fehler beim Laden verfügbarer Modelle: {e}")
        return {
            "success": False,
            "error": str(e)
        }
