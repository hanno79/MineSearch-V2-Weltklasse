"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: CSV-Verarbeitungslogik für Sidebar-Komponente
"""
import streamlit as st
import pandas as pd
from typing import List, Dict, Optional


class CSVHandler:
    """Verarbeitung von CSV-Uploads für Minen-Daten"""
    
    def handle_upload(self, uploaded_file) -> List[Dict]:
        """Hauptmethode für CSV-Upload und Verarbeitung"""
        if uploaded_file is None:
            return []
        
        try:
            df = self._parse_csv_file(uploaded_file)
            if df is None:
                return []
            
            # Column mapping
            column_mapping = self._detect_columns(df)
            if not column_mapping.get('mine_name'):
                st.error("CSV must contain a mine name column")
                return []
            
            # Extract mines data
            mines_data = self._extract_mines_data(df, column_mapping)
            
            # Handle selection UI
            if mines_data:
                return self._handle_mine_selection(mines_data)
            
            return []
            
        except Exception as e:
            st.error(f"Error processing CSV: {str(e)}")
            return []
    
    def _parse_csv_file(self, uploaded_file) -> Optional[pd.DataFrame]:
        """Parse CSV mit verschiedenen Encodings und Separatoren"""
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        separators = [';', ',', '\t', '|']
        
        for encoding in encodings:
            for sep in separators:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding=encoding, sep=sep)
                    
                    # Check if parse was successful
                    if len(df.columns) > 1:
                        # Clean column names
                        df.columns = df.columns.str.strip()
                        if len(df.columns) > 0 and df.columns[0].startswith('\ufeff'):
                            df.columns.values[0] = df.columns[0][1:]
                        return df
                        
                except:
                    continue
        
        st.error("Could not read CSV file. Please check the file encoding.")
        return None
    
    def _detect_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """Automatische Spalten-Erkennung"""
        column_mapping = {}
        
        # Mapping-Definitionen für verschiedene Spaltentypen
        mappings = {
            'mine_name': ['mine_name', 'name', 'Mine Name', 'Name', 'Mine', 'mine'],
            'region': ['region', 'Region', 'Province', 'State', 'province', 'state'],
            'country': ['country', 'Country', 'Nation', 'nation']
        }
        
        # Durchlaufe alle Mapping-Typen
        for map_type, variants in mappings.items():
            for col in df.columns:
                if col in variants or col.lower() in [v.lower() for v in variants]:
                    column_mapping[map_type] = col
                    break
        
        return column_mapping
    
    def _extract_mines_data(self, df: pd.DataFrame, column_mapping: Dict[str, str]) -> List[Dict]:
        """Extrahiert Minen-Daten aus DataFrame"""
        mines_data = []
        
        for _, row in df.iterrows():
            mine_data = {
                'mine_name': row[column_mapping['mine_name']],
                'region': row.get(column_mapping.get('region', ''), ''),
                'country': row.get(column_mapping.get('country', ''), '')
            }
            
            # Skip empty rows
            if mine_data['mine_name'] and pd.notna(mine_data['mine_name']):
                mines_data.append(mine_data)
        
        return mines_data
    
    def _handle_mine_selection(self, mines_data: List[Dict]) -> List[Dict]:
        """UI für Minen-Auswahl"""
        st.success(f"✅ Loaded {len(mines_data)} mines from CSV")
        st.markdown("### Select Mines to Search")
        
        # Session State Initialisierung
        self._init_session_state(mines_data)
        
        # Kontroll-Buttons
        self._render_control_buttons(mines_data)
        
        # Max Mines Eingabe
        max_mines = self._render_max_mines_input()
        
        # Minen-Auswahl Interface
        with st.expander(f"Select mines", expanded=True):
            self._render_selection_status(max_mines)
            
            if len(mines_data) <= 50:
                self._render_checkbox_selection(mines_data, max_mines)
            else:
                self._render_multiselect_selection(mines_data, max_mines)
        
        # Finale Zusammenfassung
        return self._get_active_mines(mines_data)
    
    def _init_session_state(self, mines_data: List[Dict]):
        """Initialisiert Session State für Minen-Auswahl"""
        if 'all_selected_mine_indices' not in st.session_state:
            # ÄNDERUNG 27.06.2025: Standard auf 5 Minen reduziert
            st.session_state['all_selected_mine_indices'] = list(range(min(5, len(mines_data))))
        
        if 'active_mine_indices' not in st.session_state:
            st.session_state['active_mine_indices'] = st.session_state['all_selected_mine_indices'][:5]
        
        if 'max_mines_limit' not in st.session_state:
            st.session_state['max_mines_limit'] = 20
    
    def _render_control_buttons(self, mines_data: List[Dict]):
        """Rendert Kontroll-Buttons für Minen-Auswahl"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✅ Select All", use_container_width=True):
                st.session_state['all_selected_mine_indices'] = list(range(len(mines_data)))
                max_limit = st.session_state.get('max_mines_limit', 20)
                st.session_state['active_mine_indices'] = list(range(min(max_limit, len(mines_data))))
        
        with col2:
            if st.button("❌ Deselect All", use_container_width=True):
                st.session_state['all_selected_mine_indices'] = []
                st.session_state['active_mine_indices'] = []
        
        with col3:
            if st.button("🔄 Activate All", use_container_width=True):
                num_selected = len(st.session_state['all_selected_mine_indices'])
                if num_selected > 0:
                    st.session_state['max_mines_limit'] = num_selected
                    st.session_state['active_mine_indices'] = st.session_state['all_selected_mine_indices'].copy()
                    st.info(f"✅ Activated all {num_selected} selected mines")
    
    def _render_max_mines_input(self) -> int:
        """Rendert Max Mines Eingabefeld"""
        def on_max_mines_change():
            new_max = st.session_state['max_mines_input']
            old_max = st.session_state.get('max_mines_limit', 20)
            
            if new_max != old_max:
                st.session_state['max_mines_limit'] = new_max
                all_selected = st.session_state.get('all_selected_mine_indices', [])
                
                if new_max > old_max:
                    st.session_state['active_mine_indices'] = all_selected[:new_max]
                else:
                    st.session_state['active_mine_indices'] = st.session_state['active_mine_indices'][:new_max]
        
        return st.number_input(
            "Max mines to search at once",
            min_value=1,
            max_value=100,
            value=st.session_state.get('max_mines_limit', 20),
            key="max_mines_input",
            on_change=on_max_mines_change,
            help="Limit the number of mines for better performance"
        )
    
    def _render_selection_status(self, max_mines: int):
        """Zeigt Auswahl-Status an"""
        num_all_selected = len(st.session_state.get('all_selected_mine_indices', []))
        num_active = len(st.session_state.get('active_mine_indices', []))
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Selected Mines", num_all_selected)
        with col2:
            st.metric("Active for Search", f"{num_active} / {max_mines}")
        
        if num_all_selected > max_mines:
            st.warning(f"⚠️ {num_all_selected - max_mines} selected mines are inactive. Increase 'Max mines' or click 'Activate All'")
        
        st.markdown("---")
    
    def _render_checkbox_selection(self, mines_data: List[Dict], max_mines: int):
        """Rendert Checkbox-basierte Auswahl für kleine Listen"""
        new_selected_indices = []
        
        for idx, mine in enumerate(mines_data):
            is_selected = idx in st.session_state.get('all_selected_mine_indices', [])
            is_active = idx in st.session_state.get('active_mine_indices', [])
            
            label = f"{mine['mine_name']} - {mine['region']}, {mine['country']}"
            if is_selected and not is_active:
                label += " ⚠️ (selected but inactive)"
            
            if st.checkbox(label, value=is_selected, key=f"mine_checkbox_{idx}"):
                new_selected_indices.append(idx)
        
        st.session_state['all_selected_mine_indices'] = new_selected_indices
        
        if len(new_selected_indices) > max_mines:
            st.session_state['max_mines_limit'] = len(new_selected_indices)
            st.session_state['active_mine_indices'] = new_selected_indices
            st.success(f"✅ Automatically increased max mines to {len(new_selected_indices)}")
        else:
            st.session_state['active_mine_indices'] = new_selected_indices[:max_mines]
    
    def _render_multiselect_selection(self, mines_data: List[Dict], max_mines: int):
        """Rendert Multiselect-basierte Auswahl für große Listen"""
        mine_options = [
            f"{mine['mine_name']} - {mine['region']}, {mine['country']}"
            for mine in mines_data
        ]
        
        default_selection = [
            mine_options[i] 
            for i in st.session_state.get('all_selected_mine_indices', [])
        ]
        
        selected_options = st.multiselect(
            "Choose mines (no limit on selection)",
            options=mine_options,
            default=default_selection,
            help="Select as many as you want. Active mines will be limited by 'Max mines' setting."
        )
        
        new_selected_indices = [
            idx for idx, option in enumerate(mine_options)
            if option in selected_options
        ]
        
        st.session_state['all_selected_mine_indices'] = new_selected_indices
        
        if len(new_selected_indices) > max_mines:
            if st.checkbox("Auto-increase max mines to match selection?", value=True):
                st.session_state['max_mines_limit'] = len(new_selected_indices)
                st.session_state['active_mine_indices'] = new_selected_indices
            else:
                st.session_state['active_mine_indices'] = new_selected_indices[:max_mines]
        else:
            st.session_state['active_mine_indices'] = new_selected_indices[:max_mines]
    
    def _get_active_mines(self, mines_data: List[Dict]) -> List[Dict]:
        """Gibt aktive Minen für die Suche zurück"""
        num_active = len(st.session_state.get('active_mine_indices', []))
        
        if num_active > 0:
            st.success(f"✅ Ready to search {num_active} mines")
            active_mines = [
                mines_data[idx] 
                for idx in st.session_state.get('active_mine_indices', [])
            ]
            return active_mines
        else:
            st.warning("⚠️ Please select at least one mine to search")
            return []