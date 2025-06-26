"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Database Viewer für MineSearch - Zeigt wichtige Datenbanktabellen
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
from src.core.database import DatabaseManager, Mine, Search, Result, AggregatedData
from sqlalchemy import func


class DatabaseViewerPage:
    """Seite zur Anzeige der Datenbanktabellen"""
    
    def __init__(self, database: DatabaseManager):
        self.db = database
        
    def render(self):
        """Rendert die Database Viewer Seite"""
        st.header("🗄️ Datenbank-Übersicht")
        
        # Tab-Auswahl für verschiedene Tabellen
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "⛏️ Minen", 
            "🔍 Suchen", 
            "📊 Ergebnisse", 
            "📈 Aggregierte Daten",
            "📊 Statistiken"
        ])
        
        with tab1:
            self._render_mines_table()
            
        with tab2:
            self._render_searches_table()
            
        with tab3:
            self._render_results_table()
            
        with tab4:
            self._render_aggregated_data()
            
        with tab5:
            self._render_statistics()
            
    def _render_mines_table(self):
        """Zeigt die Mines Tabelle"""
        st.subheader("⛏️ Registrierte Minen")
        
        with self.db.get_session() as session:
            mines = session.query(Mine).all()
            
        if not mines:
            st.info("Keine Minen in der Datenbank gefunden.")
            return
            
        # Konvertiere zu DataFrame
        df_data = []
        for mine in mines:
            df_data.append({
                "ID": mine.id,
                "Name": mine.name,
                "Region": mine.region,
                "Land": mine.country,
                "Sprachen": ", ".join(mine.languages) if mine.languages else "",
                "Erstellt": mine.created_at.strftime("%Y-%m-%d %H:%M") if mine.created_at else "",
                "Aktualisiert": mine.updated_at.strftime("%Y-%m-%d %H:%M") if mine.updated_at else ""
            })
            
        df = pd.DataFrame(df_data)
        
        # Filter-Optionen
        col1, col2 = st.columns(2)
        with col1:
            country_filter = st.selectbox(
                "Nach Land filtern",
                ["Alle"] + sorted(df["Land"].unique().tolist()),
                key="mine_country_filter"
            )
            
        if country_filter != "Alle":
            df = df[df["Land"] == country_filter]
            
        # Zeige Tabelle
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
        
        st.metric("Gesamt", len(df))
        
    def _render_searches_table(self):
        """Zeigt die Searches Tabelle"""
        st.subheader("🔍 Suchläufe")
        
        # Zeitfilter
        time_filter = st.selectbox(
            "Zeitraum",
            ["Letzte 24 Stunden", "Letzte 7 Tage", "Letzte 30 Tage", "Alle"],
            key="search_time_filter"
        )
        
        with self.db.get_session() as session:
            query = session.query(Search).join(Mine)
            
            # Zeit-Filter anwenden
            if time_filter == "Letzte 24 Stunden":
                since = datetime.now() - timedelta(days=1)
                query = query.filter(Search.started_at >= since)
            elif time_filter == "Letzte 7 Tage":
                since = datetime.now() - timedelta(days=7)
                query = query.filter(Search.started_at >= since)
            elif time_filter == "Letzte 30 Tage":
                since = datetime.now() - timedelta(days=30)
                query = query.filter(Search.started_at >= since)
                
            searches = query.order_by(Search.started_at.desc()).all()
            
        if not searches:
            st.info("Keine Suchläufe im gewählten Zeitraum gefunden.")
            return
            
        # Konvertiere zu DataFrame
        df_data = []
        for search in searches:
            duration = None
            if search.started_at and search.completed_at:
                duration = (search.completed_at - search.started_at).total_seconds()
                
            df_data.append({
                "ID": search.id,
                "Mine": search.mine.name if search.mine else "Unknown",
                "Gestartet": search.started_at.strftime("%Y-%m-%d %H:%M") if search.started_at else "",
                "Status": search.status,
                "Agenten": len(search.agents_used) if search.agents_used else 0,
                "Ergebnisse": search.total_results or 0,
                "Dauer (s)": f"{duration:.1f}" if duration else "läuft",
                "Erfolgsrate": f"{search.success_rate:.0%}" if search.success_rate else "-"
            })
            
        df = pd.DataFrame(df_data)
        
        # Status-Filter
        status_filter = st.selectbox(
            "Status filtern",
            ["Alle"] + sorted(df["Status"].unique().tolist()),
            key="search_status_filter"
        )
        
        if status_filter != "Alle":
            df = df[df["Status"] == status_filter]
            
        # Zeige Tabelle
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
        
        # Metriken
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Gesamt", len(df))
        with col2:
            completed = len(df[df["Status"] == "completed"])
            st.metric("Erfolgreich", completed)
        with col3:
            if len(df) > 0:
                success_rate = completed / len(df) * 100
                st.metric("Erfolgsrate", f"{success_rate:.0f}%")
                
    def _render_results_table(self):
        """Zeigt die Results Tabelle"""
        st.subheader("📊 Suchergebnisse")
        
        # Filter-Optionen
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Mine-Filter
            with self.db.get_session() as session:
                mine_names = session.query(Mine.name).distinct().all()
                mine_names = [m[0] for m in mine_names]
                
            selected_mine = st.selectbox(
                "Mine",
                ["Alle"] + sorted(mine_names),
                key="result_mine_filter"
            )
            
        with col2:
            # Feld-Filter
            field_filter = st.text_input(
                "Feld filtern",
                placeholder="z.B. betreiber",
                key="result_field_filter"
            )
            
        with col3:
            # Konfidenz-Filter
            min_confidence = st.slider(
                "Min. Konfidenz",
                0.0, 1.0, 0.0,
                key="result_confidence_filter"
            )
            
        # Lade Ergebnisse
        with self.db.get_session() as session:
            query = session.query(Result).join(Mine)
            
            if selected_mine != "Alle":
                query = query.filter(Mine.name == selected_mine)
                
            if field_filter:
                query = query.filter(Result.field_name.contains(field_filter))
                
            if min_confidence > 0:
                query = query.filter(Result.confidence_score >= min_confidence)
                
            results = query.order_by(Result.created_at.desc()).limit(500).all()
            
        if not results:
            st.info("Keine Ergebnisse mit den gewählten Filtern gefunden.")
            return
            
        # Konvertiere zu DataFrame
        df_data = []
        for result in results:
            df_data.append({
                "Mine": result.mine.name if result.mine else "Unknown",
                "Feld": result.field_name,
                "Wert": result.value[:100] + "..." if len(result.value) > 100 else result.value,
                "Quelle": result.source or "-",
                "Agent": result.agent_name or "-",
                "Konfidenz": result.confidence_score or 0,
                "Jahr": result.source_date or "-",
                "Erstellt": result.created_at.strftime("%Y-%m-%d") if result.created_at else ""
            })
            
        df = pd.DataFrame(df_data)
        
        # Zeige Tabelle mit Farbkodierung
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Konfidenz": st.column_config.ProgressColumn(
                    "Konfidenz",
                    format="%.0%%",
                    min_value=0,
                    max_value=1
                )
            }
        )
        
        # Metriken
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Gesamt", len(df))
        with col2:
            avg_confidence = df["Konfidenz"].mean()
            st.metric("⌀ Konfidenz", f"{avg_confidence:.0%}")
        with col3:
            unique_fields = df["Feld"].nunique()
            st.metric("Unique Felder", unique_fields)
            
    def _render_aggregated_data(self):
        """Zeigt aggregierte Daten"""
        st.subheader("📈 Aggregierte Daten pro Mine")
        
        with self.db.get_session() as session:
            agg_data = session.query(AggregatedData).join(Mine).all()
            
        if not agg_data:
            st.info("Keine aggregierten Daten vorhanden.")
            return
            
        # Zeige Daten pro Mine
        for agg in agg_data:
            with st.expander(f"⛏️ {agg.mine.name}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Qualitäts-Score", f"{agg.quality_score:.0%}" if agg.quality_score else "-")
                    st.metric("Vollständigkeits-Score", f"{agg.completeness_score:.0%}" if agg.completeness_score else "-")
                    
                with col2:
                    st.metric("Letzte Aktualisierung", 
                             agg.last_updated.strftime("%Y-%m-%d %H:%M") if agg.last_updated else "-")
                    
                # Zeige aggregierte Daten
                if agg.data:
                    st.json(agg.data)
                    
    def _render_statistics(self):
        """Zeigt Gesamtstatistiken"""
        st.subheader("📊 Gesamtstatistiken")
        
        with self.db.get_session() as session:
            # Basis-Statistiken
            total_mines = session.query(func.count(Mine.id)).scalar()
            total_searches = session.query(func.count(Search.id)).scalar()
            total_results = session.query(func.count(Result.id)).scalar()
            
            # Erfolgsrate
            completed_searches = session.query(func.count(Search.id)).filter(
                Search.status == "completed"
            ).scalar()
            
            # Top Agenten
            agent_stats = session.query(
                Result.agent_name,
                func.count(Result.id).label('count'),
                func.avg(Result.confidence_score).label('avg_confidence')
            ).group_by(Result.agent_name).all()
            
        # Zeige Metriken
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🏔️ Minen", total_mines)
            
        with col2:
            st.metric("🔍 Suchläufe", total_searches)
            
        with col3:
            st.metric("📊 Ergebnisse", total_results)
            
        with col4:
            if total_searches > 0:
                success_rate = completed_searches / total_searches * 100
                st.metric("✅ Erfolgsrate", f"{success_rate:.0f}%")
                
        # Agent Performance
        st.divider()
        st.subheader("🤖 Agent Performance")
        
        if agent_stats:
            df_agents = pd.DataFrame([
                {
                    "Agent": stat.agent_name or "Unknown",
                    "Ergebnisse": stat.count,
                    "⌀ Konfidenz": stat.avg_confidence or 0
                }
                for stat in agent_stats
            ])
            
            # Sortiere nach Anzahl Ergebnisse
            df_agents = df_agents.sort_values("Ergebnisse", ascending=False)
            
            # Zeige Top 10
            st.dataframe(
                df_agents.head(10),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "⌀ Konfidenz": st.column_config.ProgressColumn(
                        "⌀ Konfidenz",
                        format="%.0%%",
                        min_value=0,
                        max_value=1
                    )
                }
            )
            
            # Bar Chart
            st.bar_chart(
                df_agents.head(10).set_index("Agent")["Ergebnisse"],
                use_container_width=True
            )