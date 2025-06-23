"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Metrics Dashboard Komponente für MineSearch UI
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict
from collections import Counter
from datetime import datetime


class MetricsDashboardComponent:
    """Dashboard für Metriken und Statistiken"""
    
    def render(self, search_results: List[Dict], search_history: List[Dict] = None):
        """Rendert das Metrics Dashboard"""
        
        if not search_results:
            st.info("📊 No metrics to display yet. Complete a search to see statistics.")
            return
        
        st.header("📊 Search Metrics & Analytics")
        
        # Summary metrics
        self._render_summary_metrics(search_results)
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_confidence_chart(search_results)
            self._render_source_distribution(search_results)
        
        with col2:
            self._render_field_coverage(search_results)
            self._render_agent_performance(search_results)
        
        # Search history if available
        if search_history:
            self._render_search_history(search_history)
    
    def _render_summary_metrics(self, results: List[Dict]):
        """Zusammenfassende Metriken"""
        col1, col2, col3, col4 = st.columns(4)
        
        # Calculate metrics
        total_results = len(results)
        unique_mines = len(set(r.get('mine_name', '') for r in results))
        avg_confidence = sum(r.get('confidence_score', 0.5) for r in results) / max(total_results, 1)
        unique_sources = len(set(r.get('source', '') for r in results))
        
        with col1:
            st.metric(
                label="Total Results",
                value=total_results,
                delta=None
            )
        
        with col2:
            st.metric(
                label="Unique Mines",
                value=unique_mines,
                delta=None
            )
        
        with col3:
            st.metric(
                label="Avg. Confidence",
                value=f"{avg_confidence:.1%}",
                delta=None
            )
        
        with col4:
            st.metric(
                label="Data Sources",
                value=unique_sources,
                delta=None
            )
    
    def _render_confidence_chart(self, results: List[Dict]):
        """Konfidenz-Verteilung"""
        st.subheader("🎯 Confidence Distribution")
        
        # Extract confidence scores
        confidence_scores = [r.get('confidence_score', 0.5) for r in results]
        
        # Create histogram
        fig = go.Figure(data=[
            go.Histogram(
                x=confidence_scores,
                nbinsx=20,
                marker_color='lightblue',
                marker_line_color='darkblue',
                marker_line_width=1
            )
        ])
        
        fig.update_layout(
            xaxis_title="Confidence Score",
            yaxis_title="Count",
            showlegend=False,
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_source_distribution(self, results: List[Dict]):
        """Quellen-Verteilung"""
        st.subheader("📚 Source Distribution")
        
        # Count sources
        source_counts = Counter(r.get('source', 'Unknown') for r in results)
        
        # Create pie chart
        fig = px.pie(
            values=list(source_counts.values()),
            names=list(source_counts.keys()),
            hole=0.4
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=300)
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_field_coverage(self, results: List[Dict]):
        """Feld-Abdeckung"""
        st.subheader("📋 Field Coverage")
        
        # Group by mine and count fields
        mines_data = {}
        for result in results:
            mine_name = result.get('mine_name', 'Unknown')
            if mine_name not in mines_data:
                mines_data[mine_name] = set()
            mines_data[mine_name].add(result.get('field_name', ''))
        
        # Calculate coverage
        coverage_data = []
        for mine, fields in mines_data.items():
            coverage_data.append({
                'Mine': mine,
                'Fields Found': len(fields)
            })
        
        # Create bar chart
        df = pd.DataFrame(coverage_data)
        fig = px.bar(
            df,
            x='Mine',
            y='Fields Found',
            color='Fields Found',
            color_continuous_scale='Blues'
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            height=300,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_agent_performance(self, results: List[Dict]):
        """Agent-Performance"""
        st.subheader("🤖 Agent Performance")
        
        # Count results by agent
        agent_counts = Counter(r.get('agent', r.get('source', 'Unknown')) for r in results)
        
        # Create horizontal bar chart
        fig = go.Figure(data=[
            go.Bar(
                y=list(agent_counts.keys()),
                x=list(agent_counts.values()),
                orientation='h',
                marker_color='lightgreen'
            )
        ])
        
        fig.update_layout(
            xaxis_title="Results Found",
            yaxis_title="Agent",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_search_history(self, search_history: List[Dict]):
        """Such-Historie"""
        st.markdown("---")
        st.subheader("📜 Search History")
        
        if not search_history:
            st.info("No search history available")
            return
        
        # Create history table
        history_data = []
        for entry in search_history[-10:]:  # Last 10 searches
            history_data.append({
                'Timestamp': entry.get('timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M'),
                'Mine': entry.get('mine_name', 'Unknown'),
                'Results': entry.get('result_count', 0),
                'Duration': f"{entry.get('duration', 0):.1f}s"
            })
        
        df = pd.DataFrame(history_data)
        st.dataframe(df, use_container_width=True, hide_index=True)