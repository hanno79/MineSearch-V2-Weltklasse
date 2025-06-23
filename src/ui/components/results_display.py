"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Results Display Komponente für MineSearch UI
"""
import streamlit as st
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
from src.data.models import Mine
from src.data.exporter import DataExporter


class ResultsDisplayComponent:
    """Komponente zur Anzeige und Export von Suchergebnissen"""
    
    def __init__(self):
        self.exporter = DataExporter()
    
    def render(self, search_results: List[Dict]):
        """Rendert die Suchergebnisse"""
        if not search_results:
            st.info("💡 No search results yet. Start a search to see results.")
            return
        
        # Results header with count
        st.header(f"📊 Search Results ({len(search_results)} items)")
        
        # Export buttons
        self._render_export_buttons(search_results)
        
        # Display options
        display_mode = st.radio(
            "Display Mode",
            ["Table View", "Card View", "Raw Data"],
            horizontal=True
        )
        
        if display_mode == "Table View":
            self._render_table_view(search_results)
        elif display_mode == "Card View":
            self._render_card_view(search_results)
        else:
            self._render_raw_data(search_results)
    
    def _render_export_buttons(self, results: List[Dict]):
        """Export-Funktionalität"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # CSV Export
            csv_data = self._prepare_csv_export(results)
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"mine_search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            # JSON Export
            json_data = self._prepare_json_export(results)
            st.download_button(
                label="📥 Download JSON",
                data=json_data,
                file_name=f"mine_search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col3:
            # Excel Export (wenn openpyxl installiert)
            try:
                excel_data = self._prepare_excel_export(results)
                if excel_data:
                    st.download_button(
                        label="📥 Download Excel",
                        data=excel_data,
                        file_name=f"mine_search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
            except:
                st.button("📥 Excel (Not Available)", disabled=True, use_container_width=True)
    
    def _render_table_view(self, results: List[Dict]):
        """Tabellarische Ansicht"""
        # Group by mine
        mines_data = self._group_results_by_mine(results)
        
        # Create DataFrame
        df_data = []
        for mine_name, mine_results in mines_data.items():
            row = {'Mine Name': mine_name}
            
            # Add all fields
            for result in mine_results:
                field_name = result.get('field_name', 'Unknown')
                value = result.get('value', '')
                
                # Handle multiple values for same field
                if field_name in row:
                    if isinstance(row[field_name], list):
                        row[field_name].append(value)
                    else:
                        row[field_name] = [row[field_name], value]
                else:
                    row[field_name] = value
            
            # Convert lists to strings
            for key, val in row.items():
                if isinstance(val, list):
                    row[key] = ' | '.join(str(v) for v in val)
            
            df_data.append(row)
        
        if df_data:
            df = pd.DataFrame(df_data)
            
            # Reorder columns (Mine Name first)
            cols = ['Mine Name'] + [col for col in df.columns if col != 'Mine Name']
            df = df[cols]
            
            # Style the dataframe
            styled_df = df.style.set_properties(**{
                'background-color': 'white',
                'color': 'black',
                'border-color': 'gray'
            })
            
            # Display with column configuration
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Mine Name": st.column_config.TextColumn(
                        "Mine Name",
                        width="medium",
                    )
                }
            )
        else:
            st.warning("No data to display in table format")
    
    def _render_card_view(self, results: List[Dict]):
        """Karten-Ansicht für einzelne Ergebnisse"""
        mines_data = self._group_results_by_mine(results)
        
        for mine_name, mine_results in mines_data.items():
            with st.expander(f"⛏️ **{mine_name}** ({len(mine_results)} fields)", expanded=True):
                # Group by category
                categorized = self._categorize_results(mine_results)
                
                # Display by category
                for category, cat_results in categorized.items():
                    if cat_results:
                        st.subheader(f"📋 {category}")
                        
                        # Create columns for better layout
                        cols = st.columns(2)
                        for idx, result in enumerate(cat_results):
                            col_idx = idx % 2
                            with cols[col_idx]:
                                self._render_single_result(result)
    
    def _render_single_result(self, result: Dict):
        """Einzelnes Ergebnis als Karte"""
        field_name = result.get('field_name', 'Unknown')
        value = result.get('value', 'N/A')
        source = result.get('source', 'Unknown')
        confidence = result.get('confidence_score', 0.5)
        
        # Color based on confidence
        if confidence >= 0.8:
            color = "green"
        elif confidence >= 0.6:
            color = "orange"
        else:
            color = "red"
        
        # Result card
        st.markdown(f"""
        <div style="padding: 10px; border: 1px solid {color}; border-radius: 5px; margin-bottom: 10px;">
            <strong>{field_name}</strong><br>
            {value}<br>
            <small>Source: {source} | Confidence: {confidence:.0%}</small>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_raw_data(self, results: List[Dict]):
        """Rohdaten-Ansicht"""
        st.json(results)
    
    def _group_results_by_mine(self, results: List[Dict]) -> Dict[str, List[Dict]]:
        """Gruppiert Ergebnisse nach Mine"""
        mines_data = {}
        for result in results:
            mine_name = result.get('mine_name', 'Unknown')
            if mine_name not in mines_data:
                mines_data[mine_name] = []
            mines_data[mine_name].append(result)
        return mines_data
    
    def _categorize_results(self, results: List[Dict]) -> Dict[str, List[Dict]]:
        """Kategorisiert Ergebnisse nach Feldtyp"""
        categories = {
            "Basic Information": ["betreiber", "operator", "owner", "company", "koordinaten", 
                                "coordinates", "location", "GPS", "rohstofftyp", "commodity", 
                                "mineral", "aktivitaetsstatus", "status"],
            "Financial": ["sanierungskosten", "remediation_costs", "closure_costs", 
                         "environmental_liability", "restoration_costs", "financial_assurance"],
            "Production": ["production_start", "production_end", "mine_life", "reserve", 
                          "resource", "capacity"],
            "Technical": ["mining_method", "processing", "recovery_rate", "depth"],
            "Other": []
        }
        
        categorized = {cat: [] for cat in categories}
        
        for result in results:
            field_name = result.get('field_name', '').lower()
            categorized_flag = False
            
            for category, fields in categories.items():
                if category != "Other" and any(field in field_name for field in fields):
                    categorized[category].append(result)
                    categorized_flag = True
                    break
            
            if not categorized_flag:
                categorized["Other"].append(result)
        
        # Remove empty categories
        return {cat: results for cat, results in categorized.items() if results}
    
    def _prepare_csv_export(self, results: List[Dict]) -> str:
        """Bereitet CSV-Export vor"""
        mines_data = self._group_results_by_mine(results)
        
        # Create rows
        rows = []
        for mine_name, mine_results in mines_data.items():
            row = {'mine_name': mine_name}
            
            for result in mine_results:
                field_name = result.get('field_name', '')
                value = result.get('value', '')
                
                # Handle multiple values
                if field_name in row:
                    row[field_name] = f"{row[field_name]} | {value}"
                else:
                    row[field_name] = value
            
            rows.append(row)
        
        # Convert to DataFrame and CSV
        if rows:
            df = pd.DataFrame(rows)
            return df.to_csv(index=False, encoding='utf-8-sig')
        return ""
    
    def _prepare_json_export(self, results: List[Dict]) -> str:
        """Bereitet JSON-Export vor"""
        import json
        mines_data = self._group_results_by_mine(results)
        return json.dumps(mines_data, indent=2, ensure_ascii=False)
    
    def _prepare_excel_export(self, results: List[Dict]) -> Optional[bytes]:
        """Bereitet Excel-Export vor"""
        try:
            import io
            mines_data = self._group_results_by_mine(results)
            
            # Create DataFrame
            rows = []
            for mine_name, mine_results in mines_data.items():
                row = {'mine_name': mine_name}
                for result in mine_results:
                    field_name = result.get('field_name', '')
                    value = result.get('value', '')
                    row[field_name] = value
                rows.append(row)
            
            if rows:
                df = pd.DataFrame(rows)
                
                # Write to BytesIO
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Results')
                
                return output.getvalue()
        except:
            return None