"""
Streamlit GUI für Multi-Agent Mining Research System
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import asyncio
from datetime import datetime
import sys
import aiohttp
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.config import get_config
from src.core.database import get_db_manager, Mine, Search, Result
from src.data.aggregator import DataAggregator
from src.data.exporter import DataExporter
from src.agents.factory import AgentFactory


# Seiten-Konfiguration
st.set_page_config(
    page_title="Multi-Agent Mining Research",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS für besseres Styling
st.markdown("""
<style>
    .stProgress .st-bo {
        background-color: #00cc00;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        color: #856404;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Haupt-Funktion der Streamlit App"""
    
    # Initialisiere Session State
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'aggregator' not in st.session_state:
        st.session_state.aggregator = None
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
    
    # Sidebar Navigation
    with st.sidebar:
        st.title("🔍 Mine Search")
        st.markdown("---")
        
        page = st.radio(
            "Navigation",
            ["🏠 Dashboard", "🔎 Neue Recherche", "📊 Statistiken", "⚙️ Einstellungen"]
        )
        
        st.markdown("---")
        st.markdown("### 📌 Quick Info")
        config = get_config()
        available_agents = AgentFactory.get_available_agents(config)
        
        st.success(f"✅ {sum(available_agents.values())} Agenten verfügbar")
        
        for agent, available in available_agents.items():
            if available:
                st.write(f"🟢 {agent.upper()}")
            else:
                st.write(f"🔴 {agent.upper()}")
    
    # Hauptbereich
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "🔎 Neue Recherche":
        show_new_search()
    elif page == "📊 Statistiken":
        show_statistics()
    elif page == "⚙️ Einstellungen":
        show_settings()


def show_dashboard():
    """Dashboard-Ansicht"""
    st.title("🏠 Dashboard")
    st.markdown("Willkommen beim Multi-Agent Mining Research System")
    
    # Zusammenfassung
    col1, col2, col3, col4 = st.columns(4)
    
    db_manager = get_db_manager()
    with db_manager.get_session() as session:
        total_mines = session.query(Mine).count()
        total_searches = session.query(Search).count()
        total_results = session.query(Result).count()
    
    with col1:
        st.metric("Minen in DB", total_mines)
    with col2:
        st.metric("Durchgeführte Suchen", total_searches)
    with col3:
        st.metric("Gefundene Daten", total_results)
    with col4:
        st.metric("Erfolgsrate", "73%")  # Placeholder
    
    # Letzte Suchen
    st.markdown("---")
    st.subheader("📋 Letzte Suchen")
    
    if st.session_state.search_results:
        for result in st.session_state.search_results[-5:]:
            with st.expander(f"Mine: {result.get('mine_name', 'Unbekannt')}"):
                metrics = result.get('metrics', {})
                st.write(f"**Qualität:** {metrics.get('quality_score', 0):.1f}%")
                st.write(f"**Vollständigkeit:** {metrics.get('completeness_score', 0):.1f}%")
                
                if 'aggregated' in result:
                    agg_data = result['aggregated'].get('data', {})
                    if agg_data:
                        st.write("**Gefundene Daten:**")
                        for field, data in list(agg_data.items())[:5]:
                            st.write(f"- {field}: {data['value']} {data['confidence']}")
    else:
        st.info("Noch keine Suchen durchgeführt")


def show_new_search():
    """Neue Recherche durchführen"""
    st.title("🔎 Neue Recherche")
    
    # Workflow Steps
    steps = ["📤 CSV Upload", "🌍 Region & Sprache", "🤖 Agenten", "💾 Export"]
    
    # Progress Bar
    progress = st.session_state.current_step / len(steps)
    st.progress(progress)
    
    # Step Display
    cols = st.columns(len(steps))
    for i, (col, step) in enumerate(zip(cols, steps)):
        with col:
            if i + 1 == st.session_state.current_step:
                st.markdown(f"**{step}**")
            elif i + 1 < st.session_state.current_step:
                st.markdown(f"✅ {step}")
            else:
                st.markdown(f"⚪ {step}")
    
    st.markdown("---")
    
    # Step Content
    if st.session_state.current_step == 1:
        show_csv_upload()
    elif st.session_state.current_step == 2:
        show_region_selection()
    elif st.session_state.current_step == 3:
        show_agent_selection()
    elif st.session_state.current_step == 4:
        # Zeige sofort einen Indikator
        with st.spinner("🚀 Lade Suchergebnisse..."):
            show_export_options()


def show_csv_upload():
    """CSV Upload Step"""
    st.subheader("📤 CSV-Datei hochladen")
    
    uploaded_file = st.file_uploader(
        "Wählen Sie eine CSV-Datei mit Minendaten",
        type=['csv'],
        help="Die CSV sollte Spalten für Name, Region und Land enthalten"
    )
    
    if uploaded_file is not None:
        # Versuche verschiedene Trennzeichen zu erkennen
        uploaded_file.seek(0)
        first_line = uploaded_file.readline().decode('utf-8')
        uploaded_file.seek(0)
        
        # Erkenne Trennzeichen
        delimiters = [';', ',', '\t', '|']
        delimiter_counts = {}
        for delim in delimiters:
            delimiter_counts[delim] = first_line.count(delim)
        
        # Wähle das häufigste Trennzeichen
        detected_delimiter = max(delimiter_counts, key=delimiter_counts.get)
        
        # Lade CSV mit erkanntem Trennzeichen
        try:
            df = pd.read_csv(uploaded_file, sep=detected_delimiter)
            st.session_state.mines_df = df
            
            # Zeige erkanntes Trennzeichen
            delimiter_names = {';': 'Semikolon (;)', ',': 'Komma (,)', '\t': 'Tab', '|': 'Pipe (|)'}
            st.success(f"✅ {len(df)} Minen geladen | Erkanntes Trennzeichen: {delimiter_names.get(detected_delimiter, detected_delimiter)}")
        except Exception as e:
            st.error(f"Fehler beim Lesen der CSV-Datei: {str(e)}")
            
            # Manuelle Trennzeichen-Auswahl
            st.write("Bitte wählen Sie das Trennzeichen manuell:")
            manual_delimiter = st.selectbox(
                "CSV-Trennzeichen",
                options=[';', ',', '\t', '|'],
                format_func=lambda x: {';': 'Semikolon (;)', ',': 'Komma (,)', '\t': 'Tab', '|': 'Pipe (|)'}.get(x, x)
            )
            
            if st.button("CSV mit diesem Trennzeichen laden"):
                uploaded_file.seek(0)
                try:
                    df = pd.read_csv(uploaded_file, sep=manual_delimiter)
                    st.session_state.mines_df = df
                    st.success(f"✅ {len(df)} Minen geladen")
                    st.rerun()
                except Exception as e2:
                    st.error(f"Fehler: {str(e2)}")
                    return
        
        # Vorschau
        st.markdown("### 👀 Vorschau")
        st.dataframe(df.head(10))
        
        # Spalten-Mapping
        st.markdown("### 🔧 Spalten-Zuordnung")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            name_col = st.selectbox("Name-Spalte", df.columns)
        with col2:
            region_col = st.selectbox("Region-Spalte", df.columns)
        with col3:
            country_col = st.selectbox("Land-Spalte", df.columns)
        
        st.session_state.column_mapping = {
            'name': name_col,
            'region': region_col,
            'country': country_col
        }
        
        # Minen-Auswahl
        st.markdown("### 🎯 Minen für die Suche auswählen")
        
        # Auswahl-Optionen
        selection_mode = st.radio(
            "Auswahl-Modus",
            ["Alle Minen", "Erste N Minen", "Spezifische Minen auswählen"],
            horizontal=True
        )
        
        if selection_mode == "Erste N Minen":
            num_mines = st.number_input(
                "Anzahl der Minen",
                min_value=1,
                max_value=len(df),
                value=min(5, len(df)),
                step=1
            )
            selected_df = df.head(num_mines)
        elif selection_mode == "Spezifische Minen auswählen":
            # Zeige Checkboxen für jede Mine
            st.write("Wählen Sie die Minen aus:")
            selected_indices = []
            
            # In Spalten anzeigen für bessere Übersicht
            num_cols = 3
            cols = st.columns(num_cols)
            
            for idx, row in df.iterrows():
                col_idx = idx % num_cols
                with cols[col_idx]:
                    mine_name = row[name_col]
                    country = row[country_col] if country_col else ""
                    label = f"{mine_name} ({country})" if country else mine_name
                    
                    if st.checkbox(label, key=f"mine_{idx}", value=(idx < 3)):
                        selected_indices.append(idx)
            
            if selected_indices:
                selected_df = df.iloc[selected_indices]
            else:
                st.warning("Bitte wählen Sie mindestens eine Mine aus")
                selected_df = pd.DataFrame()
        else:  # Alle Minen
            selected_df = df
        
        # Zeige ausgewählte Minen
        if not selected_df.empty:
            st.info(f"✅ {len(selected_df)} Minen ausgewählt")
            st.session_state.selected_mines_df = selected_df
            
            if st.button("Weiter ➡️", type="primary"):
                st.session_state.current_step = 2
                st.rerun()
        else:
            st.session_state.selected_mines_df = None


def show_region_selection():
    """Region und Sprachen Auswahl"""
    st.subheader("🌍 Region & Sprachen")
    
    if 'selected_mines_df' not in st.session_state or st.session_state.selected_mines_df is None:
        st.error("Bitte wählen Sie zuerst Minen aus")
        if st.button("⬅️ Zurück"):
            st.session_state.current_step = 1
            st.rerun()
        return
    
    df = st.session_state.selected_mines_df
    mapping = st.session_state.column_mapping
    
    # Zeige ausgewählte Minen, Regionen und Länder
    countries = df[mapping['country']].unique()
    regions = df[mapping['region']].unique()
    st.info(f"**Ausgewählte Minen:** {len(df)} | **Regionen:** {', '.join(regions[:5])}{'...' if len(regions) > 5 else ''} | **Länder:** {', '.join(countries)}")
    
    # Globale Sprachen-Auswahl
    st.markdown("### 🗣️ Suchsprachen")
    st.write("Wählen Sie die Sprachen für die Suche. Diese werden für ALLE ausgewählten Minen verwendet.")
    
    # Verfügbare Sprachen mit Beschreibungen
    available_languages = {
        'en': 'Englisch (English)',
        'fr': 'Französisch (Français)',
        'es': 'Spanisch (Español)',
        'de': 'Deutsch',
        'pt': 'Portugiesisch (Português)',
        'it': 'Italienisch (Italiano)',
        'nl': 'Niederländisch (Nederlands)',
        'af': 'Afrikaans',
        'zh': 'Chinesisch (中文)',
        'ja': 'Japanisch (日本語)',
        'ru': 'Russisch (Русский)',
        'ar': 'Arabisch (العربية)'
    }
    
    # Empfohlene Sprachen basierend auf Ländern
    recommended_langs = set(['en'])  # Englisch immer empfohlen
    country_lang_map = {
        'Canada': ['en', 'fr'],
        'USA': ['en'],
        'Mexico': ['es', 'en'],
        'Chile': ['es', 'en'],
        'Peru': ['es', 'en'],
        'Brazil': ['pt', 'en'],
        'Argentina': ['es', 'en'],
        'Australia': ['en'],
        'South Africa': ['en', 'af'],
        'Germany': ['de', 'en'],
        'France': ['fr', 'en'],
        'Spain': ['es', 'en'],
        'Italy': ['it', 'en'],
        'Russia': ['ru', 'en'],
        'China': ['zh', 'en'],
        'Japan': ['ja', 'en']
    }
    
    for country in countries:
        if country in country_lang_map:
            recommended_langs.update(country_lang_map[country])
    
    # Zeige Empfehlungen
    if len(recommended_langs) > 1:
        st.info(f"💡 Empfohlene Sprachen basierend auf Ihren Ländern: {', '.join([available_languages[lang] for lang in recommended_langs if lang in available_languages])}")
    
    # Multi-Select für Sprachen
    selected_languages = st.multiselect(
        "Wählen Sie eine oder mehrere Sprachen:",
        options=list(available_languages.keys()),
        default=list(recommended_langs),
        format_func=lambda x: available_languages[x],
        help="Die Suche wird in ALLEN ausgewählten Sprachen durchgeführt"
    )
    
    if not selected_languages:
        st.warning("⚠️ Bitte wählen Sie mindestens eine Sprache aus")
    else:
        st.success(f"✅ {len(selected_languages)} Sprache(n) ausgewählt: {', '.join([available_languages[lang] for lang in selected_languages])}")
        
    st.session_state.selected_languages = selected_languages
    
    # Navigation
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Zurück"):
            st.session_state.current_step = 1
            st.rerun()
    with col2:
        if st.button("Weiter ➡️", type="primary", disabled=(not selected_languages)):
            with st.spinner("⏳ Lade Agent-Auswahl..."):
                st.session_state.current_step = 3
                st.rerun()


async def validate_agent_availability():
    """Validiert Agenten-Verfügbarkeit vorab"""
    config = get_config()
    
    # Teste jeden verfügbaren Agenten
    all_agents = AgentFactory.get_available_agents(config)
    agent_validation = {}
    
    # Validiere Agenten parallel für bessere Performance
    validation_tasks = []
    
    async def validate_single_agent(agent_type):
        try:
            agent = AgentFactory.create_agent(agent_type, config)
            if agent:
                initialized = await agent.initialize()
                if initialized:
                    result = {'available': True, 'message': 'Verfügbar'}
                else:
                    # Hole detaillierten Fehler direkt hier
                    error_msg = await _get_agent_error_details_ui(agent, agent_type)
                    result = {'available': False, 'message': error_msg}
                
                # Cleanup
                if hasattr(agent, 'cleanup'):
                    await agent.cleanup()
                
                return agent_type, result
        except Exception as e:
            return agent_type, {'available': False, 'message': str(e)}
    
    # Erstelle Tasks nur für wichtige Agenten (keine OpenRouter, kein Scraper)
    for agent_type, has_key in all_agents.items():
        if has_key and agent_type in ['tavily', 'exa', 'apify', 'scrapingbee', 'firecrawl', 'perplexity', 'brightdata', 'claude', 'gpt4']:
            validation_tasks.append(validate_single_agent(agent_type))
    
    # Führe alle Validierungen parallel aus
    if validation_tasks:
        results = await asyncio.gather(*validation_tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, tuple):
                agent_type, validation = result
                agent_validation[agent_type] = validation
            elif isinstance(result, Exception):
                # Fehler während der Validierung
                pass
    
    return agent_validation

async def _get_agent_error_details_ui(agent, agent_type: str) -> str:
    """Ermittelt spezifische Fehlerdetails für einen Agenten (UI Version)"""
    try:
        # Prüfe ob API-Key fehlt
        if hasattr(agent, 'api_key'):
            if not agent.api_key:
                return "API-Key fehlt"
        
        # Versuche spezifische Validierung
        if hasattr(agent, 'validate_credentials'):
            # Mache einen erweiterten Test für verschiedene Agenten
            if hasattr(agent, '_session') and hasattr(agent, 'api_key'):
                try:
                    # Tavily spezifisch
                    if agent_type == 'tavily':
                        payload = {
                            "api_key": agent.api_key,
                            "query": "test",
                            "max_results": 1
                        }
                        timeout = getattr(agent, 'timeout', aiohttp.ClientTimeout(total=10))
                        async with agent._session.post(
                            agent.base_url,
                            json=payload,
                            timeout=timeout
                        ) as response:
                            if response.status == 429:
                                return "Rate-Limit erreicht oder kein Budget mehr"
                            elif response.status == 401:
                                return "Ungültiger API-Key"
                            elif response.status == 403:
                                return "Zugriff verweigert - Möglicherweise kein Budget"
                            elif response.status != 200:
                                text = await response.text()
                                if "insufficient" in text.lower() or "quota" in text.lower() or "limit" in text.lower():
                                    return "Kein Budget mehr verfügbar"
                                return f"API-Fehler: {response.status}"
                    
                    # Perplexity spezifisch
                    elif agent_type == 'perplexity':
                        # Perplexity nutzt validate_credentials
                        result = await agent.validate_credentials()
                        if not result:
                            return "API-Validierung fehlgeschlagen - Key prüfen"
                    
                    # Generische API-Fehlerbehandlung für andere Agenten
                    else:
                        # Versuche validate_credentials zu nutzen
                        result = await agent.validate_credentials()
                        if not result:
                            return "API-Validierung fehlgeschlagen"
                
                except aiohttp.ClientError as e:
                    if "certificate" in str(e).lower():
                        return "SSL-Zertifikatsfehler"
                    return f"Verbindungsfehler: {type(e).__name__}"
                except asyncio.TimeoutError:
                    return "Timeout - Service antwortet nicht"
                except Exception as e:
                    error_str = str(e).lower()
                    if "rate" in error_str and "limit" in error_str:
                        return "Rate-Limit überschritten"
                    if "quota" in error_str or "budget" in error_str:
                        return "Kein Budget verfügbar"
                    if "unauthorized" in error_str or "forbidden" in error_str:
                        return "Keine Berechtigung - API-Key prüfen"
                    return f"Fehler: {str(e)[:100]}"
        
        return "Initialisierung fehlgeschlagen"
        
    except Exception as e:
        return f"Fehler bei Statusprüfung: {str(e)}"

def show_agent_selection():
    """Agenten-Auswahl"""
    st.subheader("🤖 Agenten auswählen")
    
    # Zeige Ladeindikator beim ersten Laden
    if 'agent_selection_loading' not in st.session_state:
        st.session_state.agent_selection_loading = True
        st.info("⏳ Lade Agent-Konfiguration...")
        st.rerun()
    
    config = get_config()
    available_agents = AgentFactory.get_available_agents(config)
    
    # Führe Validierung durch
    if 'agent_validation' not in st.session_state:
        validation_container = st.container()
        with validation_container:
            with st.spinner("🔍 Prüfe Agent-Verfügbarkeit... Dies kann einen Moment dauern."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                async def validate_with_progress():
                    status_text.text("Teste API-Verbindungen...")
                    progress_bar.progress(0.3)
                    result = await validate_agent_availability()
                    progress_bar.progress(1.0)
                    return result
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                st.session_state.agent_validation = loop.run_until_complete(validate_with_progress())
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
    
    # Reset loading flag
    if 'agent_selection_loading' in st.session_state:
        del st.session_state.agent_selection_loading
    
    # Zeige Verfügbarkeitsstatus
    validation = st.session_state.agent_validation
    available_count = sum(1 for v in validation.values() if v.get('available', False))
    total_validated = len(validation)
    
    # Zähle alle verfügbaren Agenten (inkl. OpenRouter und Scraper)
    total_agent_count = len([a for a in available_agents if available_agents[a]])
    
    if available_count > 0 or total_validated < total_agent_count:
        st.success(f"✅ {available_count} von {total_validated} Web-Scraping/API Agenten geprüft und verfügbar")
        st.info(f"ℹ️ Zusätzlich stehen {total_agent_count - total_validated} weitere Agenten zur Verfügung (OpenRouter LLMs, Scraper)")
    else:
        st.warning("⚠️ Keine geprüften Agenten verfügbar")
    
    # Zeige Probleme falls vorhanden
    problems = [(agent, info['message']) for agent, info in validation.items() if not info.get('available', False)]
    if problems:
        with st.expander(f"⚠️ {len(problems)} Agenten mit Problemen", expanded=False):
            for agent, message in problems:
                st.error(f"**{agent}**: {message}")
            
            st.markdown("---")
            if st.button("🔄 Verfügbarkeit erneut prüfen"):
                del st.session_state.agent_validation
                st.rerun()
    
    # Initialisiere selected_agents am Anfang der Funktion
    selected_agents = []
    
    # Agent-Beschreibungen mit Kategorien
    agent_info = {
        # Web-Scraping Agenten (Kostenlos/Freemium)
        'scraper': {
            'name': 'Basic Web Scraper',
            'category': 'scraping',
            'free': True,
            'icon': '🌐',
            'description': 'Basis Web-Scraper ohne API-Key. Gut für öffentliche Webseiten.',
            'strengths': ['Immer verfügbar', 'Keine Kosten', 'Einfache Webseiten'],
            'limitations': ['Kein JavaScript', 'Begrenzte Tiefe']
        },
        'tavily': {
            'name': 'Tavily Search',
            'category': 'scraping',
            'free': True,
            'icon': '🔍',
            'description': 'Fortgeschrittene Web-Suche mit AI-Optimierung.',
            'strengths': ['1000 kostenlose Suchen/Monat', 'Gute Relevanz', 'Schnell'],
            'limitations': ['Rate-Limits', 'Begrenzte Tiefe']
        },
        'exa': {
            'name': 'Exa Semantic Search',
            'category': 'scraping',
            'free': True,
            'icon': '🧠',
            'description': 'Semantische Suche mit KI-Verständnis.',
            'strengths': ['Versteht Kontext', 'Gute für technische Daten', 'Kostenlose Stufe'],
            'limitations': ['Begrenzte Anfragen']
        },
        'apify': {
            'name': 'Apify Actors',
            'category': 'scraping',
            'free': True,
            'icon': '🎭',
            'description': 'Professionelle Web-Scraping-Plattform.',
            'strengths': ['$5 kostenlose Credits/Monat', 'Viele Datenquellen', 'Strukturierte Daten'],
            'limitations': ['Credits schnell aufgebraucht']
        },
        'scrapingbee': {
            'name': 'ScrapingBee',
            'category': 'scraping',
            'free': True,
            'icon': '🐝',
            'description': 'JavaScript-Rendering und Anti-Bot-Umgehung.',
            'strengths': ['1000 kostenlose Credits', 'JavaScript-Support', 'Proxy-Rotation'],
            'limitations': ['Credits begrenzt']
        },
        'firecrawl': {
            'name': 'Firecrawl',
            'category': 'scraping',
            'free': True,
            'icon': '🔥',
            'description': 'Intelligentes Web-Crawling mit Tiefensuche.',
            'strengths': ['Kostenlose Stufe', 'Folgt Links', 'Strukturierte Ausgabe'],
            'limitations': ['Rate-Limits']
        },
        'brightdata': {
            'name': 'Bright Data',
            'category': 'scraping',
            'free': False,
            'icon': '💎',
            'description': 'Enterprise Web-Scraping mit globalem Proxy-Netzwerk.',
            'strengths': ['Höchste Erfolgsrate', 'Globale IPs', 'Keine Blockierung'],
            'limitations': ['Kostenpflichtig', 'Komplex']
        },
        
        # LLM-basierte Agenten
        'claude': {
            'name': 'Claude (OpenRouter)',
            'category': 'llm_premium',
            'free': False,
            'icon': '🤖',
            'description': 'Claude-3 für intelligente Mining-Analyse.',
            'strengths': ['Beste Qualität', 'Versteht Kontext', 'Multi-Language'],
            'limitations': ['Kosten pro Anfrage']
        },
        'gpt4': {
            'name': 'GPT-4 (OpenRouter)',
            'category': 'llm_premium',
            'free': False,
            'icon': '🧠',
            'description': 'GPT-4 für komplexe Mining-Recherchen.',
            'strengths': ['Hohe Qualität', 'Breites Wissen', 'Zuverlässig'],
            'limitations': ['Kosten pro Anfrage']
        },
        'perplexity': {
            'name': 'Perplexity AI',
            'category': 'llm_premium',
            'free': False,
            'icon': '🔮',
            'description': 'Online-LLM mit Echtzeit-Webzugriff.',
            'strengths': ['Aktuelle Daten', 'Quellenangaben', 'Faktentreu'],
            'limitations': ['API-Kosten']
        }
    }
    
    # OpenRouter Modelle (werden dynamisch hinzugefügt)
    has_openrouter = bool(config.api.openrouter_key)
    
    # Kategorisierte Anzeige
    st.markdown("### 🌐 Web-Scraping Agenten (Kostenlos/Freemium)")
    scraping_cols = st.columns(3)
    col_idx = 0
    
    for agent_id, is_available in available_agents.items():
        if agent_id in agent_info and agent_info[agent_id]['category'] == 'scraping':
            info = agent_info[agent_id]
            with scraping_cols[col_idx % 3]:
                if is_available:
                    # Prüfe Validierungsstatus
                    validation = st.session_state.agent_validation.get(agent_id, {})
                    is_validated = validation.get('available', True)
                    validation_msg = validation.get('message', '')
                    
                    # Checkbox mit Info-Button
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        if is_validated:
                            # Agent ist verfügbar
                            default_value = info['free']
                            label = f"{info['icon']} {info['name']} ✅"
                        else:
                            # Agent hat Fehler
                            default_value = False
                            label = f"{info['icon']} {info['name']} ⚠️"
                        
                        if st.checkbox(label, 
                                     value=default_value and is_validated, 
                                     key=f"agent_{agent_id}",
                                     disabled=not is_validated):
                            selected_agents.append(agent_id)
                    
                    with col2:
                        if st.button("ℹ️", key=f"info_{agent_id}", help="Details anzeigen"):
                            st.session_state[f"show_info_{agent_id}"] = not st.session_state.get(f"show_info_{agent_id}", False)
                    
                    # Zeige Fehlermeldung wenn Agent nicht verfügbar
                    if not is_validated and validation_msg:
                        st.error(f"❌ {validation_msg}")
                    
                    # Zeige Details wenn aktiviert
                    if st.session_state.get(f"show_info_{agent_id}", False):
                        with st.expander("Details", expanded=True):
                            st.write(f"**Beschreibung:** {info['description']}")
                            st.write(f"**Stärken:** {', '.join(info['strengths'])}")
                            st.write(f"**Grenzen:** {', '.join(info['limitations'])}")
                            if not is_validated:
                                st.error(f"**Status:** {validation_msg}")
                else:
                    st.checkbox(f"❌ {info['name']} (API-Key fehlt)", 
                              value=False, disabled=True)
                col_idx += 1
    
    # Premium LLM Agenten
    st.markdown("### 💎 Premium LLM Agenten (Kostenpflichtig)")
    premium_cols = st.columns(3)
    col_idx = 0
    
    for agent_id, is_available in available_agents.items():
        if agent_id in agent_info and agent_info[agent_id]['category'] == 'llm_premium':
            info = agent_info[agent_id]
            with premium_cols[col_idx % 3]:
                if is_available:
                    # Prüfe Validierungsstatus
                    validation = st.session_state.agent_validation.get(agent_id, {})
                    is_validated = validation.get('available', True)
                    validation_msg = validation.get('message', '')
                    
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        if is_validated:
                            # Agent ist verfügbar
                            label = f"{info['icon']} {info['name']} ✅"
                        else:
                            # Agent hat Fehler
                            label = f"{info['icon']} {info['name']} ⚠️"
                        
                        # Premium Agenten standardmäßig deaktiviert
                        if st.checkbox(label, 
                                     value=False, 
                                     key=f"agent_{agent_id}",
                                     disabled=not is_validated):
                            selected_agents.append(agent_id)
                    
                    with col2:
                        if st.button("ℹ️", key=f"info_{agent_id}", help="Details anzeigen"):
                            st.session_state[f"show_info_{agent_id}"] = not st.session_state.get(f"show_info_{agent_id}", False)
                    
                    # Zeige Fehlermeldung wenn Agent nicht verfügbar
                    if not is_validated and validation_msg:
                        st.error(f"❌ {validation_msg}")
                    
                    if st.session_state.get(f"show_info_{agent_id}", False):
                        with st.expander("Details", expanded=True):
                            st.write(f"**Beschreibung:** {info['description']}")
                            st.write(f"**Stärken:** {', '.join(info['strengths'])}")
                            st.write(f"**Grenzen:** {', '.join(info['limitations'])}")
                            if not is_validated:
                                st.error(f"**Status:** {validation_msg}")
                else:
                    st.checkbox(f"❌ {info['name']} (API-Key fehlt)", 
                              value=False, disabled=True)
                col_idx += 1
    
    # OpenRouter kostenlose und Premium Modelle
    if has_openrouter:
        st.markdown("### 🆓 Kostenlose LLM Modelle (via OpenRouter)")
        st.info("Diese fortschrittlichen KI-Modelle sind kostenlos nutzbar und bieten oft bessere Ergebnisse als Web-Scraping.")
        
        free_models = {
            'openrouter_deepseek-chat': {
                'name': 'DeepSeek Chat',
                'icon': '🏆',
                'description': 'Bestes kostenloses Modell. Exzellent für Mining-Recherche.',
                'strengths': ['Völlig kostenlos', 'Sehr intelligent', 'Multi-Language'],
                'limitations': ['Manchmal langsam']
            },
            'openrouter_qwen-2.5-72b-instruct': {
                'name': 'Qwen 2.5 72B',
                'icon': '🐉',
                'description': 'Alibabas großes Modell mit gutem Faktenwissen.',
                'strengths': ['Kostenlos', 'Gut für Fakten', 'Schnell'],
                'limitations': ['Weniger kreativ']
            },
            'openrouter_gemini-2.0-flash-exp': {
                'name': 'Gemini 2.0 Flash',
                'icon': '⚡',
                'description': 'Googles schnelles Modell mit 1M Token Kontext.',
                'strengths': ['Kostenlos', 'Sehr schnell', 'Großer Kontext'],
                'limitations': ['Beta-Version']
            }
        }
        
        free_cols = st.columns(3)
        for idx, (model_id, model_info) in enumerate(free_models.items()):
            with free_cols[idx % 3]:
                col1, col2 = st.columns([4, 1])
                with col1:
                    # Kostenlose OpenRouter Modelle standardmäßig aktiviert
                    if st.checkbox(f"{model_info['icon']} {model_info['name']} 🆓", 
                                 value=True, 
                                 key=f"agent_{model_id}"):
                        selected_agents.append(model_id)
                with col2:
                    if st.button("ℹ️", key=f"info_{model_id}", help="Details anzeigen"):
                        st.session_state[f"show_info_{model_id}"] = not st.session_state.get(f"show_info_{model_id}", False)
                
                if st.session_state.get(f"show_info_{model_id}", False):
                    with st.expander("Details", expanded=True):
                        st.write(f"**Beschreibung:** {model_info['description']}")
                        st.write(f"**Stärken:** {', '.join(model_info['strengths'])}")
                        st.write(f"**Grenzen:** {', '.join(model_info['limitations'])}")
        
        # Premium OpenRouter Modelle
        st.markdown("### 🌟 Premium LLM Modelle (via OpenRouter)")
        premium_models = {
            'openrouter_claude-3.5-sonnet-20241022': {
                'name': 'Claude 3.5 Sonnet',
                'icon': '👑',
                'description': 'Anthropics neuestes Modell. Beste Qualität für Mining-Daten.',
                'strengths': ['Höchste Qualität', 'Präzise', 'Versteht Kontext perfekt'],
                'limitations': ['$3/Million Token']
            },
            'openrouter_gpt-4o-2024-11-20': {
                'name': 'GPT-4o Latest',
                'icon': '🚀',
                'description': 'OpenAIs neuestes Modell mit verbesserter Geschwindigkeit.',
                'strengths': ['Sehr gut', 'Schnell', 'Zuverlässig'],
                'limitations': ['$2.50/Million Token']
            }
        }
        
        premium_or_cols = st.columns(3)
        for idx, (model_id, model_info) in enumerate(premium_models.items()):
            with premium_or_cols[idx % 3]:
                col1, col2 = st.columns([4, 1])
                with col1:
                    if st.checkbox(f"{model_info['icon']} {model_info['name']} 💰", 
                                 value=False, 
                                 key=f"agent_{model_id}"):
                        selected_agents.append(model_id)
                with col2:
                    if st.button("ℹ️", key=f"info_{model_id}", help="Details anzeigen"):
                        st.session_state[f"show_info_{model_id}"] = not st.session_state.get(f"show_info_{model_id}", False)
                
                if st.session_state.get(f"show_info_{model_id}", False):
                    with st.expander("Details", expanded=True):
                        st.write(f"**Beschreibung:** {model_info['description']}")
                        st.write(f"**Stärken:** {', '.join(model_info['strengths'])}")
                        st.write(f"**Kosten:** {model_info['limitations']}")
    
    st.session_state.selected_agents = selected_agents
    
    # Zeige Zusammenfassung
    if selected_agents:
        # Definiere kostenlose Agenten
        free_agents = ['scraper', 'tavily', 'exa', 'apify', 'scrapingbee', 'firecrawl']
        free_openrouter = ['openrouter_deepseek-chat', 'openrouter_qwen-2.5-72b-instruct', 
                          'openrouter_mistral-7b-instruct', 'openrouter_llama-3.2-90b-instruct',
                          'openrouter_gemma-2-27b-it', 'openrouter_hermes-3-llama-3.1-70b',
                          'openrouter_gemini-2.0-flash-exp']
        
        free_count = sum(1 for agent in selected_agents if agent in free_agents or agent in free_openrouter)
        paid_count = len(selected_agents) - free_count
        
        st.success(f"✅ {len(selected_agents)} Agenten ausgewählt ({free_count} kostenlos, {paid_count} kostenpflichtig)")
        
        # Debug-Info
        with st.expander("🔍 Ausgewählte Agenten Details", expanded=False):
            for agent in selected_agents:
                if agent in free_agents or agent in free_openrouter:
                    st.write(f"✅ {agent} (kostenlos)")
                else:
                    st.write(f"💰 {agent} (kostenpflichtig)")
    else:
        st.warning("⚠️ Bitte wählen Sie mindestens einen Agenten aus")
    
    # Parallelität
    st.markdown("### ⚡ Parallelität")
    max_concurrent = st.slider(
        "Maximale parallele Anfragen",
        min_value=1,
        max_value=50,
        value=10,
        help="Höhere Werte = schneller, aber mehr Ressourcen"
    )
    st.session_state.max_concurrent = max_concurrent
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Zurück"):
            st.session_state.current_step = 2
            st.rerun()
    with col2:
        if st.button("🚀 Suche starten", type="primary", disabled=(not selected_agents)):
            st.session_state.current_step = 4
            st.session_state.search_started = True
            with st.spinner("🚀 Starte Suche..."):
                st.rerun()


async def start_search_with_status(status_placeholder, progress_bar):
    """Startet die Suche mit Status-Updates"""
    try:
        # Debug-Ausgabe
        status_placeholder.info("🔧 Initialisiere System...")
        
        # Initialisiere Aggregator
        if not st.session_state.aggregator:
            st.session_state.aggregator = DataAggregator()
        
        aggregator = st.session_state.aggregator
        
        # Prüfe ob alle Daten vorhanden sind
        if 'selected_mines_df' not in st.session_state or st.session_state.selected_mines_df is None:
            status_placeholder.error("❌ Keine Minen ausgewählt!")
            return []
        
        if 'column_mapping' not in st.session_state:
            status_placeholder.error("❌ Keine Spaltenzuordnung gefunden!")
            return []
        
        # Verwende die ausgewählten Minen und globale Sprachen
        df = st.session_state.selected_mines_df
        mapping = st.session_state.column_mapping
        languages = st.session_state.get('selected_languages', ['de'])  # Default zu Deutsch
        selected_agents = st.session_state.get('selected_agents', [])
        
        # Prüfe ob Agenten ausgewählt wurden
        if not selected_agents:
            status_placeholder.error("❌ Keine Agenten ausgewählt!")
            return []
        
        status_placeholder.info(f"✅ {len(df)} Minen, {len(selected_agents)} Agenten bereit")
        
        mines_data = []
        for _, row in df.iterrows():
            # Stelle sicher dass Deutsch priorisiert wird
            mine_languages = languages.copy()
            if 'de' not in mine_languages:
                mine_languages.insert(0, 'de')
            else:
                # Bewege Deutsch an erste Stelle
                mine_languages.remove('de')
                mine_languages.insert(0, 'de')
                
            mine_data = {
                'name': row[mapping['name']],
                'region': row[mapping['region']],
                'country': row[mapping['country']],
                'languages': mine_languages  # Deutsch priorisiert
            }
            mines_data.append(mine_data)
        
        # Status-Callback für Agent-Updates
        async def agent_status_callback(message):
            status_placeholder.info(f"🤖 {message}")
        
        # Initialisiere Agenten mit Status-Updates
        status_placeholder.info(f"📡 Initialisiere {len(selected_agents)} Agenten...")
        agent_status = await aggregator.initialize_agents(selected_agents)
        
        # Prüfe ob agent_status gültig ist
        if not agent_status:
            status_placeholder.error("❌ Fehler bei der Agent-Initialisierung")
            return []
        
        # Zeige Agent-Status
        active_agents = []
        failed_agents = []
        
        for agent_type, status_info in agent_status.items():
            if status_info['status'] == 'active':
                active_agents.append(agent_type)
            else:
                failed_agents.append((agent_type, status_info['message']))
        
        if active_agents:
            status_placeholder.success(f"✅ {len(active_agents)} Agenten bereit: {', '.join(active_agents)}")
        
        if failed_agents:
            for agent, error in failed_agents:
                status_placeholder.warning(f"⚠️ {agent}: {error}")
        
        if not active_agents:
            status_placeholder.error("❌ Keine Agenten verfügbar!")
            return []
        
        # Setze Status-Callback für alle aktiven Agenten
        for agent in aggregator.agents.values():
            agent.status_callback = agent_status_callback
        
        # Führe Suchen durch
        total_mines = len(mines_data)
        all_results = []
        
        for i, mine_data in enumerate(mines_data):
            progress = (i + 1) / total_mines
            progress_bar.value = progress
            status_placeholder.info(f"🔍 Suche Mine {i+1}/{total_mines}: **{mine_data['name']}**")
            
            try:
                # Zeige welche Agenten aktiv sind
                status_placeholder.info(f"🤖 Verwende {len(selected_agents)} Agenten für {mine_data['name']}...")
                
                result = await aggregator.search_mine(mine_data, selected_agents, agent_status_callback)
                
                # Extrahiere die tatsächlichen Suchergebnisse
                if 'results' in result:
                    for search_result in result['results']:
                        # Konvertiere SearchResult zu dict falls nötig
                        if hasattr(search_result, 'to_dict'):
                            result_dict = search_result.to_dict()
                        else:
                            result_dict = search_result if isinstance(search_result, dict) else vars(search_result)
                        
                        # Füge Mine-Info hinzu
                        result_dict['mine_name'] = mine_data['name']
                        result_dict['region'] = mine_data['region']
                        result_dict['country'] = mine_data['country']
                        all_results.append(result_dict)
                        
                status_placeholder.success(f"✅ {mine_data['name']}: {len(result.get('results', []))} Ergebnisse gefunden")
                
            except Exception as e:
                status_placeholder.error(f"❌ Fehler bei {mine_data['name']}: {str(e)}")
                import traceback
                st.error(traceback.format_exc())
        
        return all_results
        
    except Exception as e:
        status_placeholder.error(f"❌ Kritischer Fehler: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return []


def show_export_options():
    """Suche durchführen und Ergebnisse anzeigen"""
    st.subheader("🔍 Suche & Ergebnisse")
    
    # Zeige sofort Feedback
    if st.session_state.get('search_started', False):
        st.info("🎯 Suche wird vorbereitet...")
        del st.session_state.search_started
    
    # Führe Suche durch wenn noch nicht geschehen
    if 'search_completed' not in st.session_state or not st.session_state.search_completed:
        # Zeige ausgewählte Konfiguration
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Ausgewählte Minen", len(st.session_state.get('selected_mines_df', [])))
        with col2:
            st.metric("Aktive Agenten", len(st.session_state.get('selected_agents', [])))
        with col3:
            languages = st.session_state.get('selected_languages', ['en'])
            st.metric("Sprachen", ', '.join(languages))
        
        st.markdown("---")
        
        # Zeige Startmeldung
        st.success("🎯 Suche wurde gestartet!")
        st.info("🚀 Die Suche läuft im Hintergrund. Dies kann einige Minuten dauern...")
        
        # Progress Container für Status-Updates
        progress_container = st.container()
        with progress_container:
            status_placeholder = st.empty()
            progress_bar = st.progress(0)
            
            # Debug Info
            status_placeholder.info("📡 Initialisiere System...")
            
            try:
                # Führe Suche durch
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                results = loop.run_until_complete(
                    start_search_with_status(status_placeholder, progress_bar)
                )
                
                st.session_state.search_results = results
                st.session_state.search_completed = True
                
                # Clear progress elements
                status_placeholder.empty()
                progress_bar.empty()
                
                if results:
                    st.success(f"✅ Suche abgeschlossen! {len(results)} Ergebnisse gefunden.")
                else:
                    st.warning("⚠️ Keine Ergebnisse gefunden.")
                    
            except Exception as e:
                st.error(f"❌ Fehler bei der Suche: {str(e)}")
                import traceback
                st.error(traceback.format_exc())
                status_placeholder.empty()
                progress_bar.empty()
    
    # Zeige Ergebnisse
    if not st.session_state.search_results:
        st.warning("Keine Suchergebnisse gefunden")
        if st.button("⬅️ Zurück"):
            st.session_state.current_step = 3
            st.session_state.search_completed = False
            st.rerun()
        return
    
    # Zeige Ergebnistabelle
    st.markdown("### 📊 Gefundene Ergebnisse")
    
    # Konvertiere Ergebnisse für Anzeige
    display_data = []
    for result in st.session_state.search_results:
        # Erstelle Anzeige-Dictionary mit deutschen Feldnamen
        display_row = {
            "Mine": result.get('mine_name', ''),
            "Region": result.get('region', ''),
            "Land": result.get('country', ''),
            "Feld": result.get('field_name', ''),
            "Wert": result.get('value', ''),
            "Quelle": result.get('source', ''),
            "Agent": result.get('agent_name', ''),
            "Konfidenz": f"{result.get('confidence_score', 0):.2f}"
        }
        display_data.append(display_row)
    
    # Erstelle DataFrame für bessere Anzeige
    import pandas as pd
    df = pd.DataFrame(display_data)
    
    # Zeige Zusammenfassung
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Gefundene Minen", df['Mine'].nunique())
    with col2:
        st.metric("Gefundene Felder", df['Feld'].nunique())
    with col3:
        st.metric("Beteiligte Agenten", df['Agent'].nunique())
    
    # Filter-Optionen
    with st.expander("🔍 Filter anwenden", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            selected_mines = st.multiselect(
                "Minen filtern:",
                options=df['Mine'].unique(),
                default=df['Mine'].unique(),
                key="filter_mines"
            )
        with col2:
            selected_fields = st.multiselect(
                "Felder filtern:",
                options=df['Feld'].unique(),
                default=df['Feld'].unique(),
                key="filter_fields"
            )
    
    # Anwenden der Filter
    filtered_df = df[
        (df['Mine'].isin(selected_mines)) & 
        (df['Feld'].isin(selected_fields))
    ]
    
    # Zeige Tabelle
    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    # Download der aktuellen Ansicht
    csv = filtered_df.to_csv(index=False, sep=';')
    st.download_button(
        label="📥 Aktuelle Ansicht als CSV herunterladen",
        data=csv,
        file_name="mining_results_preview.csv",
        mime='text/csv'
    )
    
    st.markdown("---")
    
    # Export-Format
    st.markdown("### 📄 Vollständigen Export erstellen")
    export_format = st.radio(
        "Export-Format",
        ["CSV", "JSON", "Zusammenfassung (TXT)"]
    )
    
    # CSV-Optionen
    if export_format == "CSV":
        col1, col2 = st.columns(2)
        with col1:
            col_sep = st.text_input("Spalten-Trenner", value="|")
        with col2:
            cell_sep = st.text_input("Zellen-Trenner", value="+++")
    
    # Export durchführen
    if st.button("📥 Exportieren", type="primary"):
        exporter = DataExporter()
        
        try:
            if export_format == "CSV":
                output_path = exporter.export_to_csv(
                    st.session_state.search_results,
                    column_separator=col_sep,
                    cell_separator=cell_sep
                )
            elif export_format == "JSON":
                output_path = exporter.export_to_json(st.session_state.search_results)
            else:
                output_path = exporter.export_summary_report(st.session_state.search_results)
            
            st.success(f"✅ Export erfolgreich: {output_path}")
            
            # Download-Button
            with open(output_path, 'rb') as f:
                st.download_button(
                    label="⬇️ Datei herunterladen",
                    data=f.read(),
                    file_name=output_path.name,
                    mime='text/csv' if export_format == "CSV" else 'application/json'
                )
        
        except Exception as e:
            st.error(f"Export fehlgeschlagen: {e}")
    
    # Neue Suche
    if st.button("🔄 Neue Suche starten"):
        st.session_state.current_step = 1
        st.session_state.search_results = []
        st.rerun()


def show_statistics():
    """Statistiken anzeigen"""
    st.title("📊 Statistiken")
    
    if st.session_state.aggregator:
        stats = st.session_state.aggregator.get_statistics()
        
        # Agent-Statistiken
        st.subheader("🤖 Agent Performance")
        
        for agent_name, agent_stats in stats['agents'].items():
            with st.expander(f"{agent_name.upper()} Agent"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Anfragen", agent_stats['total_requests'])
                with col2:
                    st.metric("Erfolgsrate", f"{agent_stats['success_rate']:.1f}%")
                with col3:
                    st.metric("Gefundene Felder", agent_stats['total_fields_found'])
        
        # Gesamt-Statistiken
        st.subheader("📈 Gesamt-Performance")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Gesamt-Anfragen", stats['total_searches'])
        with col2:
            st.metric("Gesamt-Ergebnisse", stats['total_results'])
    else:
        st.info("Führen Sie zuerst eine Suche durch, um Statistiken zu sehen")


def show_settings():
    """Einstellungen anzeigen"""
    st.title("⚙️ Einstellungen")
    
    config = get_config()
    
    # API-Status
    st.subheader("🔑 API-Status")
    api_status = config.api.validate()
    
    for api, status in api_status.items():
        if status:
            st.success(f"✅ {api.upper()} API konfiguriert")
        else:
            st.error(f"❌ {api.upper()} API nicht konfiguriert")
    
    # Export-Einstellungen
    st.subheader("📁 Export-Einstellungen")
    st.write(f"**Standard-Pfad:** {config.export.default_path}")
    st.write(f"**Spalten-Trenner:** {config.export.column_separator}")
    st.write(f"**Zellen-Trenner:** {config.export.cell_separator}")
    
    # Performance
    st.subheader("⚡ Performance")
    st.write(f"**Max. parallele Anfragen:** {config.max_concurrent_requests}")
    st.write(f"**Debug-Modus:** {'Aktiviert' if config.debug_mode else 'Deaktiviert'}")
    
    st.info("Einstellungen können in der .env Datei geändert werden")


if __name__ == "__main__":
    main()