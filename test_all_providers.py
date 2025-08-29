#!/usr/bin/env python3
"""
Test script for all providers
"""

import requests
import json

import sys
import time
from typing import Optional

# Basis-URL und Endpunkte
SERVER_BASE_URL = "http://localhost:8000"
AVAILABLE_MODELS_ENDPOINT = "/api/available-models"
AVAILABLE_MODELS_URL = f"{SERVER_BASE_URL}{AVAILABLE_MODELS_ENDPOINT}"


def is_server_reachable(base_url: str, check_url: str, timeout: float = 1.5, retries: int = 3, backoff_factor: float = 0.5) -> bool:
    """
    Führt einen leichten Reachability-Check durch: HEAD auf Basis-URL, dann GET auf /health,
    GET auf Basis-URL und als letzte Eskalation ein GET auf check_url. Erwartet 2xx.
    Mit kleinem Retry/Backoff bei transienten Fehlern.
    """
    for attempt in range(retries):
        # 1) HEAD auf Basis-URL
        try:
            r = requests.head(base_url, timeout=timeout)
            if 200 <= r.status_code < 300:
                return True
        except requests.exceptions.RequestException:
            pass

        # 2) GET /health (falls vorhanden)
        try:
            r = requests.get(f"{base_url}/health", timeout=timeout)
            if 200 <= r.status_code < 300:
                return True
        except requests.exceptions.RequestException:
            pass

        # 3) GET Basis-URL
        try:
            r = requests.get(base_url, timeout=timeout)
            if 200 <= r.status_code < 300:
                return True
        except requests.exceptions.RequestException:
            pass

        # 4) GET auf die konkrete Check-URL
        try:
            r = requests.get(check_url, timeout=timeout)
            if 200 <= r.status_code < 300:
                return True
        except requests.exceptions.RequestException:
            pass

        if attempt < retries - 1:
            time.sleep(backoff_factor * (2 ** attempt))

    return False


def request_with_retries(method: str, url: str, timeout: float = 3.0, retries: int = 2, backoff_factor: float = 0.5) -> Optional[requests.Response]:
    """
    Führt eine HTTP-Anfrage mit kleinem Retry/Backoff aus. Retried bei 429/5xx und Netzwerkfehlern.
    Gibt die Response zurück (ggf. Non-2xx), oder None bei totalem Fehlschlag.
    """
    for attempt in range(retries + 1):
        try:
            resp = requests.request(method=method, url=url, timeout=timeout)

            # Retrybare Statuscodes
            if resp.status_code in (429, 500, 502, 503, 504):
                if attempt < retries:
                    time.sleep(backoff_factor * (2 ** attempt))
                    continue
            return resp
        except requests.exceptions.RequestException as exc:
            if attempt < retries:
                time.sleep(backoff_factor * (2 ** attempt))
                continue
            print(f"HTTP-Fehler bei {method} {url}: {exc}")
            return None

def test_all_providers():
    # Vorab: Server-Reachability-Check mit kurzem Timeout und Backoff
    if not is_server_reachable(SERVER_BASE_URL, AVAILABLE_MODELS_URL, timeout=1.5, retries=3, backoff_factor=0.5):
        print("Server nicht erreichbar (Health-Check fehlgeschlagen). Test wird übersprungen.")
        return

    try:
        response = request_with_retries("GET", AVAILABLE_MODELS_URL, timeout=3.0, retries=2, backoff_factor=0.5)
        if response is None:
            print("Fehler: Keine Antwort vom Server erhalten.")
            return

        if not (200 <= response.status_code < 300):
            print(f"Fehler: Unerwarteter Status-Code {response.status_code} für {AVAILABLE_MODELS_URL}")
            try:
                snippet = response.text[:200]
                if snippet:
                    print(f"Antwortauszug: {snippet}...")
            except Exception:
                pass
            return

        try:
            data = response.json()
        except ValueError as e:
            print(f"Fehler beim Parsen der JSON-Antwort: {e}")
            return

        models = data.get('data', {}).get('available_models', {})
        unavailable = data.get('data', {}).get('unavailable_models', {})

        print(f"=== ALLE PROVIDER-TEST ===")
        print(f"Verfügbare Modelle: {len(models)}")
        print(f"Nicht verfügbare Modelle: {len(unavailable)}")

        # Zähle nach echten Provider (nicht Kategorie)
        providers = {}
        for model_id, model_data in models.items():
            provider = model_data['provider']
            if provider not in providers:
                providers[provider] = []
            providers[provider].append(model_id)

        print(f"\n=== VERFÜGBARE PROVIDER ===")
        for provider, model_list in providers.items():
            print(f"🔹 {provider.upper()}: {len(model_list)} Modelle")

        # Zeige nicht verfügbare Provider
        if unavailable:
            print(f"\n=== NICHT VERFÜGBARE MODELLE ===")
            unavail_providers = {}
            for model_id, model_data in unavailable.items():
                provider = model_data['provider']
                if provider not in unavail_providers:
                    unavail_providers[provider] = []
                unavail_providers[provider].append({
                    'model_id': model_id,
                    'status': model_data.get('provider_status', 'unknown'),
                    'error': model_data.get('error', 'No error info')
                })

            for provider, model_list in unavail_providers.items():
                print(f"❌ {provider.upper()}: {len(model_list)} Modelle nicht verfügbar")
                for model_info in model_list[:2]:  # Zeige erste 2
                    print(f"   • {model_info['model_id']} - {model_info['status']}")
                    print(f"     Fehler: {model_info['error'][:50]}...")

        # Erwartete Provider-Liste
        expected_providers = [
            'openrouter', 'abacus', 'tavily', 'exa', 'scrapingbee',
            'firecrawl', 'brightdata'
        ]

        print(f"\n=== PROVIDER-STATUS CHECK ===")
        for exp_provider in expected_providers:
            if exp_provider in providers:
                print(f"✅ {exp_provider.upper()}: Verfügbar ({len(providers[exp_provider])} Modelle)")
            else:
                # Check if it's in unavailable
                found_unavail = any(model_data['provider'] == exp_provider for model_data in unavailable.values())
                if found_unavail:
                    print(f"⚠️  {exp_provider.upper()}: Nicht verfügbar (Provider-Problem)")
                else:
                    print(f"❌ {exp_provider.upper()}: Komplett fehlend")

    except Exception as e:
        print(f"Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_all_providers()