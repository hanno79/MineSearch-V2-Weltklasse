"""
Author: rahn
Datum: 26.06.2025
Version: 1.0
Beschreibung: Ergebnis-Historie Seite für MineSearch
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from src.core.database import DatabaseManager, Search, Result, Mine


class ResultHistoryPage:
    """Seite zur Anzeige der Such-Historie"""
    
    def __init__(self, database: DatabaseManager):
        self.db = database
        
    def render(self):
        """Rendert die Historie-Seite"""
        st.header("📜 Such-Historie")
        
        # Filter-Optionen
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Zeitraum-Filter
            time_filter = st.selectbox(
                "Zeitraum",
                ["Letzte 24 Stunden", "Letzte 7 Tage", "Letzte 30 Tage", "Alle"],
                index=1
            )
            
        with col2:
            # Mine-Filter
            all_mines = self._get_all_mines()
            selected_mine = st.selectbox(
                "Mine filtern",
                ["Alle"] + all_mines,
                index=0
            )
            
        with col3:
            # Status-Filter
            status_filter = st.selectbox(
                "Status",
                ["Alle", "Erfolgreich", "Fehlgeschlagen", "Abgebrochen"],
                index=0
            )
            
        # Lade Suchverlauf
        searches = self._load_search_history(time_filter, selected_mine, status_filter)
        
        if not searches:
            st.info("Keine Suchergebnisse im gewählten Zeitraum gefunden.")
            return
            
        # Zeige Zusammenfassung
        self._render_summary(searches)
        
        # Zeige Suchverlauf
        st.subheader("🔍 Suchverlauf")
        
        # Erstelle DataFrame für bessere Darstellung
        df_data = []
        for search in searches:
            df_data.append({
                "Datum": search.created_at.strftime("%Y-%m-%d %H:%M"),
                "Minen": search.mine_count,
                "Agenten": len(search.agents_used) if search.agents_used else 0,
                "Ergebnisse": search.total_results,
                "Dauer": f"{(search.completed_at - search.started_at).total_seconds():.1f}s" if search.completed_at else "läuft",
                "Status": search.status,
                "ID": search.id
            })
            
        df = pd.DataFrame(df_data)
        
        # Zeige interaktive Tabelle
        selected_rows = st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        # Zeige Details für ausgewählte Suche
        if selected_rows and selected_rows.selection and selected_rows.selection.rows:
            selected_idx = selected_rows.selection.rows[0]
            selected_search = searches[selected_idx]
            self._render_search_details(selected_search)
            
    def _get_all_mines(self) -> List[str]:
        """Holt alle Minen aus der Datenbank"""
        with self.db.get_session() as session:
            mines = session.query(Mine.name).distinct().all()
            return [mine[0] for mine in mines]
            
    def _load_search_history(self, time_filter: str, mine_filter: str, status_filter: str) -> List[Search]:
        """Lädt Suchverlauf aus der Datenbank"""
        with self.db.get_session() as session:
            query = session.query(Search)
            
            # Zeit-Filter
            if time_filter == "Letzte 24 Stunden":
                since = datetime.now() - timedelta(days=1)
                query = query.filter(Search.created_at >= since)
            elif time_filter == "Letzte 7 Tage":
                since = datetime.now() - timedelta(days=7)
                query = query.filter(Search.created_at >= since)
            elif time_filter == "Letzte 30 Tage":
                since = datetime.now() - timedelta(days=30)
                query = query.filter(Search.created_at >= since)
                
            # Status-Filter
            if status_filter != "Alle":
                query = query.filter(Search.status == status_filter.lower())
                
            # Mine-Filter (komplexer, da Minen in Ergebnissen gespeichert sind)
            if mine_filter != "Alle":
                # JOIN mit Results und Mines
                query = query.join(Result).join(Mine).filter(Mine.name == mine_filter)
                
            # Sortiere nach Datum absteigend
            searches = query.order_by(Search.created_at.desc()).limit(100).all()
            
            return searches
            
    def _render_summary(self, searches: List[Search]):
        """Zeigt Zusammenfassung der Suchen"""
        col1, col2, col3, col4 = st.columns(4)
        
        total_searches = len(searches)
        successful = len([s for s in searches if s.status == "completed"])
        total_results = sum(s.total_results for s in searches if s.total_results)
        avg_duration = sum((s.completed_at - s.started_at).total_seconds() for s in searches if s.completed_at) / len([s for s in searches if s.completed_at]) if searches else 0
        
        with col1:
            st.metric("Gesamte Suchen", total_searches)
            
        with col2:
            success_rate = (successful / total_searches * 100) if total_searches > 0 else 0
            st.metric("Erfolgsrate", f"{success_rate:.0f}%")
            
        with col3:
            st.metric("Gefundene Daten", total_results)
            
        with col4:
            st.metric("⌀ Dauer", f"{avg_duration:.1f}s")
            
    def _render_search_details(self, search: Search):
        """Zeigt Details einer spezifischen Suche"""
        st.divider()
        st.subheader(f"📋 Such-Details (ID: {search.id})")
        
        # Basis-Informationen
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Gestartet:** {search.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            st.write(f"**Dauer:** {(search.completed_at - search.started_at).total_seconds():.1f} Sekunden" if search.completed_at else "läuft")
            st.write(f"**Status:** {search.status}")
            
        with col2:
            st.write(f"**Mine:** {search.mine.name if search.mine else 'Unbekannt'}")
            st.write(f"**Agenten:** {len(search.agents_used) if search.agents_used else 0}")
            st.write(f"**Ergebnisse:** {search.total_results}")
            
        # Lade Ergebnisse für diese Suche
        with self.db.get_session() as session:
            results = session.query(Result).filter(Result.search_id == search.id).all()
            
        if results:
            st.subheader("🔍 Gefundene Ergebnisse")
            
            # Gruppiere nach Mine
            mines_data = {}
            for result in results:
                mine_name = result.mine.name if result.mine else "Unknown"
                if mine_name not in mines_data:
                    mines_data[mine_name] = []
                mines_data[mine_name].append(result)
                
            # Zeige Ergebnisse pro Mine
            for mine_name, mine_results in mines_data.items():
                with st.expander(f"⛏️ {mine_name} ({len(mine_results)} Felder)", expanded=False):
                    for result in mine_results:
                        col1, col2, col3 = st.columns([2, 3, 1])
                        
                        with col1:
                            st.write(f"**{result.field_name}**")
                            
                        with col2:
                            st.write(result.value[:100] + "..." if len(result.value) > 100 else result.value)
                            
                        with col3:
                            # Farbkodierung basierend auf Konfidenz
                            confidence = result.confidence_score
                            if confidence >= 0.8:
                                st.success(f"{confidence:.0%}")
                            elif confidence >= 0.6:
                                st.warning(f"{confidence:.0%}")
                            else:
                                st.error(f"{confidence:.0%}")
                                
                    # Export-Option für diese Mine
                    if st.button(f"📥 Export {mine_name} Daten", key=f"export_{search.id}_{mine_name}"):
                        # Hier könnte Export-Funktionalität implementiert werden
                        st.info("Export-Funktion wird implementiert...")
        else:
            st.info("Keine Ergebnisse für diese Suche gefunden.")