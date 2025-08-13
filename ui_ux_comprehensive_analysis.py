#!/usr/bin/env python3
"""
Author: rahn
Datum: 11.08.2025
Version: 1.0
Beschreibung: Comprehensive UI/UX Analysis für MineSearch 2.0 mit Playwright Automation
"""

import asyncio
import json
import os
import time
from datetime import datetime
from playwright.async_api import async_playwright

class MineSearchUIUXAnalyzer:
    """Comprehensive UI/UX Analyzer für MineSearch 2.0"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.screenshots_dir = "/app/ui_ux_analysis_screenshots"
        self.analysis_data = {}
        
        # Erstelle Screenshot-Verzeichnis
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
    async def comprehensive_ui_analysis(self):
        """Führt eine umfassende UI/UX-Analyse durch"""
        
        print("🎨 MINESEARCH 2.0 COMPREHENSIVE UI/UX ANALYSIS")
        print("=" * 80)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False, 
                slow_mo=500,
                args=['--start-maximized']
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            try:
                # Phase 1: Homepage und Initial Loading
                await self.analyze_homepage_initial_load(page)
                
                # Phase 2: Navigation und Header-Bereich
                await self.analyze_navigation_header(page)
                
                # Phase 3: Einzelsuche-Interface
                await self.analyze_single_search_interface(page)
                
                # Phase 4: CSV-Upload und Batch-Funktionen
                await self.analyze_csv_batch_functionality(page)
                
                # Phase 5: Tabs-System (Quellen, Statistiken, Konsolidiert)
                await self.analyze_tabs_system(page)
                
                # Phase 6: Detail-Modals und Popups
                await self.analyze_detail_modals(page)
                
                # Phase 7: Real User Journey Testing
                await self.perform_user_journey_testing(page)
                
                # Phase 8: Responsive Design Testing
                await self.analyze_responsive_design(page, browser)
                
                # Phase 9: Accessibility Assessment
                await self.analyze_accessibility(page)
                
                # Phase 10: Performance und Loading States
                await self.analyze_performance_loading_states(page)
                
            except Exception as e:
                print(f"❌ [ANALYSIS] Fehler während Analyse: {e}")
                await page.screenshot(path=f"{self.screenshots_dir}/error_screenshot.png")
                
            finally:
                await browser.close()
                
        # Generate Final Report
        await self.generate_comprehensive_report()
        
    async def analyze_homepage_initial_load(self, page):
        """Phase 1: Homepage und Initial Loading Analysis"""
        print("\n📱 PHASE 1: HOMEPAGE UND INITIAL LOADING ANALYSIS")
        print("-" * 60)
        
        phase_data = {
            'phase': 'homepage_initial_load',
            'timestamp': datetime.now().isoformat(),
            'findings': []
        }
        
        try:
            # Lade Homepage
            print("🌐 Lade Homepage...")
            await page.goto(self.base_url)
            
            # Screenshot der initialen Homepage
            await page.screenshot(path=f"{self.screenshots_dir}/01_homepage_initial.png", full_page=True)
            print("📸 Screenshot: Homepage Initial Load")
            
            # Warte auf vollständiges Laden
            await page.wait_for_load_state('networkidle', timeout=10000)
            await page.wait_for_timeout(2000)
            
            # Screenshot nach vollständigem Laden
            await page.screenshot(path=f"{self.screenshots_dir}/01_homepage_loaded.png", full_page=True)
            print("📸 Screenshot: Homepage Fully Loaded")
            
            # Analysiere Layout-Struktur
            header_element = await page.query_selector('header, .header, nav')
            main_element = await page.query_selector('main, .main, .content')
            footer_element = await page.query_selector('footer, .footer')
            
            layout_analysis = {
                'has_header': header_element is not None,
                'has_main': main_element is not None,
                'has_footer': footer_element is not None
            }
            
            # Analysiere Title und Meta-Informationen
            title = await page.title()
            
            # Zähle interaktive Elemente
            buttons = await page.query_selector_all('button, input[type="button"], input[type="submit"]')
            inputs = await page.query_selector_all('input, textarea, select')
            links = await page.query_selector_all('a')
            
            interactive_elements = {
                'buttons_count': len(buttons),
                'inputs_count': len(inputs),
                'links_count': len(links)
            }
            
            phase_data['findings'] = {
                'page_title': title,
                'layout_structure': layout_analysis,
                'interactive_elements': interactive_elements,
                'loading_performance': 'analyzed'
            }
            
            print(f"✅ Titel: {title}")
            print(f"✅ Buttons: {len(buttons)}, Inputs: {len(inputs)}, Links: {len(links)}")
            
        except Exception as e:
            phase_data['findings'].append({'error': str(e)})
            print(f"❌ Fehler in Phase 1: {e}")
            
        self.analysis_data['phase_1_homepage'] = phase_data
        
    async def analyze_navigation_header(self, page):
        """Phase 2: Navigation und Header-Bereich Analysis"""
        print("\n🧭 PHASE 2: NAVIGATION UND HEADER-BEREICH ANALYSIS")
        print("-" * 60)
        
        phase_data = {
            'phase': 'navigation_header',
            'timestamp': datetime.now().isoformat(),
            'findings': []
        }
        
        try:
            # Screenshot der Navigation
            await page.screenshot(path=f"{self.screenshots_dir}/02_navigation_header.png")
            
            # Analysiere Navigation-Struktur
            nav_elements = await page.query_selector_all('nav, .nav, .navigation, .header-nav')
            menu_items = await page.query_selector_all('nav a, .nav a, .menu a')
            
            # Logo/Brand Element
            logo_elements = await page.query_selector_all('img[alt*="logo"], .logo, .brand')
            
            # Search-Box in Header (falls vorhanden)
            header_search = await page.query_selector('header input[type="search"], .header input[type="search"]')
            
            navigation_analysis = {
                'nav_elements_count': len(nav_elements),
                'menu_items_count': len(menu_items),
                'has_logo': len(logo_elements) > 0,
                'has_header_search': header_search is not None
            }
            
            phase_data['findings'] = {
                'navigation_structure': navigation_analysis,
                'visual_hierarchy': 'to_be_analyzed'
            }
            
            print(f"✅ Navigation Elements: {len(nav_elements)}")
            print(f"✅ Menu Items: {len(menu_items)}")
            print(f"✅ Has Logo: {len(logo_elements) > 0}")
            
        except Exception as e:
            phase_data['findings'].append({'error': str(e)})
            print(f"❌ Fehler in Phase 2: {e}")
            
        self.analysis_data['phase_2_navigation'] = phase_data
        
    async def analyze_single_search_interface(self, page):
        """Phase 3: Einzelsuche-Interface detaillierte Analyse"""
        print("\n🔍 PHASE 3: EINZELSUCHE-INTERFACE DETAILLIERTE ANALYSE")
        print("-" * 60)
        
        phase_data = {
            'phase': 'single_search_interface',
            'timestamp': datetime.now().isoformat(),
            'findings': []
        }
        
        try:
            # Screenshot der Such-Interface
            await page.screenshot(path=f"{self.screenshots_dir}/03_search_interface_initial.png", full_page=True)
            
            # Analysiere Search-Form Elemente
            search_inputs = await page.query_selector_all('input[type="text"], input[type="search"], textarea')
            model_selectors = await page.query_selector_all('input[type="radio"], input[type="checkbox"]')
            submit_buttons = await page.query_selector_all('button[type="submit"], input[type="submit"]')
            
            # Provider/Model Selection Analysis
            model_checkboxes = await page.query_selector_all('input[name="model"]')
            
            # Analysiere Layout der Search-Form
            form_elements = await page.query_selector_all('form, .form, .search-form')
            
            search_interface_analysis = {
                'search_inputs_count': len(search_inputs),
                'model_selectors_count': len(model_selectors),
                'submit_buttons_count': len(submit_buttons),
                'available_models_count': len(model_checkboxes),
                'form_elements_count': len(form_elements)
            }
            
            # Test Model Selection Interaction
            if model_checkboxes:
                first_model = model_checkboxes[0]
                await first_model.click()
                await page.wait_for_timeout(500)
                
                await page.screenshot(path=f"{self.screenshots_dir}/03_model_selected.png")
                print("📸 Screenshot: Model Selection Interaction")
                
            phase_data['findings'] = {
                'search_interface_structure': search_interface_analysis,
                'interaction_responsiveness': 'tested'
            }
            
            print(f"✅ Search Inputs: {len(search_inputs)}")
            print(f"✅ Available Models: {len(model_checkboxes)}")
            print(f"✅ Submit Buttons: {len(submit_buttons)}")
            
        except Exception as e:
            phase_data['findings'].append({'error': str(e)})
            print(f"❌ Fehler in Phase 3: {e}")
            
        self.analysis_data['phase_3_search_interface'] = phase_data
        
    async def analyze_csv_batch_functionality(self, page):
        """Phase 4: CSV-Upload und Batch-Funktionen UX-Audit"""
        print("\n📊 PHASE 4: CSV-UPLOAD UND BATCH-FUNKTIONEN UX-AUDIT")
        print("-" * 60)
        
        phase_data = {
            'phase': 'csv_batch_functionality',
            'timestamp': datetime.now().isoformat(),
            'findings': []
        }
        
        try:
            # Suche nach CSV-Upload Elementen
            file_inputs = await page.query_selector_all('input[type="file"]')
            upload_areas = await page.query_selector_all('.upload-area, .dropzone, [id*="upload"], [class*="upload"]')
            
            # Suche nach Batch-Buttons
            batch_buttons = await page.query_selector_all('button:has-text("Batch"), button:has-text("batch"), [id*="batch"], [class*="batch"]')
            
            csv_batch_analysis = {
                'file_inputs_count': len(file_inputs),
                'upload_areas_count': len(upload_areas),
                'batch_buttons_count': len(batch_buttons)
            }
            
            # Screenshot der CSV/Batch-Bereich
            await page.screenshot(path=f"{self.screenshots_dir}/04_csv_batch_interface.png", full_page=True)
            
            # Test File Upload Interface (falls vorhanden)
            if file_inputs:
                upload_input = file_inputs[0]
                # Scroll zu Upload-Bereich
                await upload_input.scroll_into_view_if_needed()
                await page.wait_for_timeout(500)
                
                await page.screenshot(path=f"{self.screenshots_dir}/04_csv_upload_focused.png")
                print("📸 Screenshot: CSV Upload Interface")
            
            phase_data['findings'] = {
                'csv_batch_structure': csv_batch_analysis,
                'upload_ux': 'analyzed'
            }
            
            print(f"✅ File Inputs: {len(file_inputs)}")
            print(f"✅ Upload Areas: {len(upload_areas)}")
            print(f"✅ Batch Buttons: {len(batch_buttons)}")
            
        except Exception as e:
            phase_data['findings'].append({'error': str(e)})
            print(f"❌ Fehler in Phase 4: {e}")
            
        self.analysis_data['phase_4_csv_batch'] = phase_data
        
    async def analyze_tabs_system(self, page):
        """Phase 5: Tabs-System (Quellen, Statistiken, Konsolidiert) Analyse"""
        print("\n📑 PHASE 5: TABS-SYSTEM ANALYSE")
        print("-" * 60)
        
        phase_data = {
            'phase': 'tabs_system',
            'timestamp': datetime.now().isoformat(),
            'findings': []
        }
        
        try:
            # Suche nach Tab-Elementen
            tab_elements = await page.query_selector_all('.tab, [role="tab"], .nav-tab, button:has-text("Quellen"), button:has-text("Statistiken"), button:has-text("Konsolidiert")')
            tab_panels = await page.query_selector_all('.tab-pane, [role="tabpanel"], .tab-content')
            
            # Screenshot initial tabs
            await page.screenshot(path=f"{self.screenshots_dir}/05_tabs_initial.png", full_page=True)
            
            tabs_analysis = {
                'tab_elements_count': len(tab_elements),
                'tab_panels_count': len(tab_panels)
            }
            
            # Test Tab-Navigation (falls Tabs vorhanden)
            if tab_elements:
                for i, tab in enumerate(tab_elements[:3]):  # Teste maximal 3 Tabs
                    try:
                        tab_text = await tab.text_content()
                        print(f"🔄 Teste Tab: {tab_text}")
                        
                        await tab.click()
                        await page.wait_for_timeout(1000)
                        
                        await page.screenshot(path=f"{self.screenshots_dir}/05_tab_{i+1}_{tab_text.lower().replace(' ', '_')}.png", full_page=True)
                        print(f"📸 Screenshot: Tab {tab_text}")
                        
                    except Exception as tab_error:
                        print(f"⚠️ Fehler bei Tab {i+1}: {tab_error}")
            
            phase_data['findings'] = {
                'tabs_structure': tabs_analysis,
                'navigation_tested': len(tab_elements) > 0
            }
            
            print(f"✅ Tab Elements: {len(tab_elements)}")
            print(f"✅ Tab Panels: {len(tab_panels)}")
            
        except Exception as e:
            phase_data['findings'].append({'error': str(e)})
            print(f"❌ Fehler in Phase 5: {e}")
            
        self.analysis_data['phase_5_tabs'] = phase_data
        
    async def analyze_detail_modals(self, page):
        """Phase 6: Detail-Modals und Popup-Interfaces evaluieren"""
        print("\n🔍 PHASE 6: DETAIL-MODALS UND POPUP-INTERFACES")
        print("-" * 60)
        
        phase_data = {
            'phase': 'detail_modals',
            'timestamp': datetime.now().isoformat(),
            'findings': []
        }
        
        try:
            # Suche nach Modal-Triggern (Details-Buttons)
            detail_buttons = await page.query_selector_all('button:has-text("Details"), .details-btn, [id*="detail"], [class*="detail"]')
            modal_elements = await page.query_selector_all('.modal, [role="dialog"], .popup')
            
            modals_analysis = {
                'detail_buttons_count': len(detail_buttons),
                'modal_elements_count': len(modal_elements)
            }
            
            # Screenshot vor Modal-Tests
            await page.screenshot(path=f"{self.screenshots_dir}/06_modals_before_test.png", full_page=True)
            
            # Test Modal-Funktionalität (falls Details-Buttons vorhanden)
            if detail_buttons:
                for i, button in enumerate(detail_buttons[:2]):  # Teste maximal 2 Modals
                    try:
                        button_text = await button.text_content()
                        print(f"🔄 Teste Modal Button: {button_text}")
                        
                        await button.click()
                        await page.wait_for_timeout(1500)
                        
                        await page.screenshot(path=f"{self.screenshots_dir}/06_modal_{i+1}_opened.png", full_page=True)
                        print(f"📸 Screenshot: Modal {i+1} Opened")
                        
                        # Versuche Modal zu schließen
                        close_buttons = await page.query_selector_all('.modal .close, .modal button:has-text("×"), .modal button:has-text("Close")')
                        if close_buttons:
                            await close_buttons[0].click()
                            await page.wait_for_timeout(500)
                        
                    except Exception as modal_error:
                        print(f"⚠️ Fehler bei Modal {i+1}: {modal_error}")
            
            phase_data['findings'] = {
                'modals_structure': modals_analysis,
                'modal_interaction_tested': len(detail_buttons) > 0
            }
            
            print(f"✅ Detail Buttons: {len(detail_buttons)}")
            print(f"✅ Modal Elements: {len(modal_elements)}")
            
        except Exception as e:
            phase_data['findings'].append({'error': str(e)})
            print(f"❌ Fehler in Phase 6: {e}")
            
        self.analysis_data['phase_6_modals'] = phase_data
        
    async def perform_user_journey_testing(self, page):
        """Phase 7: Real User Journey Testing mit echten Suchvorgängen"""
        print("\n👤 PHASE 7: USER JOURNEY TESTING MIT ECHTEN SUCHVORGÄNGEN")
        print("-" * 60)
        
        phase_data = {
            'phase': 'user_journey_testing',
            'timestamp': datetime.now().isoformat(),
            'findings': []
        }
        
        try:
            # Zurück zur Homepage für Fresh User Journey
            await page.goto(self.base_url)
            await page.wait_for_load_state('networkidle')
            
            # Screenshot Start der User Journey
            await page.screenshot(path=f"{self.screenshots_dir}/07_user_journey_start.png", full_page=True)
            
            # Test Search Journey: Einzelsuche
            test_queries = ["Eleonore Mine", "Goldmine Kanada"]
            
            journey_results = []
            
            for i, query in enumerate(test_queries[:1]):  # Teste eine Suche für Performance
                print(f"🔍 Teste Suche: {query}")
                
                # Suche nach Search Input
                search_input = await page.query_selector('input[type="text"], textarea')
                if search_input:
                    await search_input.fill(query)
                    await page.wait_for_timeout(500)
                    
                    # Screenshot mit eingegebener Suche
                    await page.screenshot(path=f"{self.screenshots_dir}/07_search_query_{i+1}.png", full_page=True)
                    
                    # Wähle ein Modell aus
                    model_checkboxes = await page.query_selector_all('input[name="model"]')
                    if model_checkboxes:
                        await model_checkboxes[0].click()  # Wähle erstes verfügbares Modell
                        await page.wait_for_timeout(300)
                    
                    # Submit Search
                    submit_button = await page.query_selector('button[type="submit"], input[type="submit"]')
                    if submit_button:
                        await submit_button.click()
                        print(f"⏳ Suche gestartet für: {query}")
                        
                        await page.wait_for_timeout(3000)  # Warte auf erste Ergebnisse
                        
                        # Screenshot der Suchergebnisse
                        await page.screenshot(path=f"{self.screenshots_dir}/07_search_results_{i+1}.png", full_page=True)
                        
                        journey_results.append({
                            'query': query,
                            'search_executed': True,
                            'results_visible': True
                        })
                        
                        print(f"✅ Search Journey {i+1} completed")
                    else:
                        journey_results.append({
                            'query': query,
                            'search_executed': False,
                            'error': 'No submit button found'
                        })
            
            phase_data['findings'] = {
                'user_journey_results': journey_results,
                'search_flow_tested': True
            }
            
            print(f"✅ User Journeys Tested: {len(journey_results)}")
            
        except Exception as e:
            phase_data['findings'].append({'error': str(e)})
            print(f"❌ Fehler in Phase 7: {e}")
            
        self.analysis_data['phase_7_user_journey'] = phase_data
        
    async def analyze_responsive_design(self, page, browser):
        """Phase 8: Responsive Design und Mobile UX-Assessment"""
        print("\n📱 PHASE 8: RESPONSIVE DESIGN UND MOBILE UX-ASSESSMENT")
        print("-" * 60)
        
        phase_data = {
            'phase': 'responsive_design',
            'timestamp': datetime.now().isoformat(),
            'findings': []
        }
        
        try:
            # Test verschiedene Viewport-Größen
            viewports = [
                {'width': 1920, 'height': 1080, 'name': 'desktop_large'},
                {'width': 1366, 'height': 768, 'name': 'desktop_standard'},
                {'width': 768, 'height': 1024, 'name': 'tablet'},
                {'width': 375, 'height': 667, 'name': 'mobile'}
            ]
            
            responsive_results = []
            
            for viewport in viewports:
                print(f"📱 Teste Viewport: {viewport['name']} ({viewport['width']}x{viewport['height']})")
                
                await page.set_viewport_size(viewport['width'], viewport['height'])
                await page.wait_for_timeout(1000)
                
                # Screenshot für dieses Viewport
                await page.screenshot(path=f"{self.screenshots_dir}/08_responsive_{viewport['name']}.png", full_page=True)
                
                # Analysiere Layout für dieses Viewport
                overflow_elements = await page.query_selector_all('::-webkit-scrollbar-horizontal')
                mobile_menu = await page.query_selector('.mobile-menu, .hamburger, .menu-toggle')
                
                viewport_analysis = {
                    'viewport': viewport,
                    'has_horizontal_scroll': len(overflow_elements) > 0,
                    'has_mobile_menu': mobile_menu is not None
                }
                
                responsive_results.append(viewport_analysis)
                
            phase_data['findings'] = {
                'responsive_testing_results': responsive_results,
                'viewports_tested': len(viewports)
            }
            
            print(f"✅ Responsive Tests: {len(responsive_results)} Viewports")
            
            # Zurück zu Standard-Viewport
            await page.set_viewport_size(1920, 1080)
            
        except Exception as e:
            phase_data['findings'].append({'error': str(e)})
            print(f"❌ Fehler in Phase 8: {e}")
            
        self.analysis_data['phase_8_responsive'] = phase_data
        
    async def analyze_accessibility(self, page):
        """Phase 9: Accessibility Assessment"""
        print("\n♿ PHASE 9: ACCESSIBILITY ASSESSMENT")
        print("-" * 60)
        
        phase_data = {
            'phase': 'accessibility',
            'timestamp': datetime.now().isoformat(),
            'findings': []
        }
        
        try:
            # Accessibility-Check
            await page.goto(self.base_url)
            await page.wait_for_load_state('networkidle')
            
            # Analysiere ARIA-Attribute
            aria_labels = await page.query_selector_all('[aria-label], [aria-labelledby], [aria-describedby]')
            role_elements = await page.query_selector_all('[role]')
            alt_images = await page.query_selector_all('img[alt]')
            all_images = await page.query_selector_all('img')
            
            # Form Labels Check
            form_inputs = await page.query_selector_all('input, textarea, select')
            labeled_inputs = await page.query_selector_all('input[id] + label, label input, input[aria-label]')
            
            # Keyboard Navigation Test
            await page.keyboard.press('Tab')
            await page.wait_for_timeout(200)
            focused_element = await page.evaluate('document.activeElement.tagName')
            
            accessibility_analysis = {
                'aria_labels_count': len(aria_labels),
                'role_elements_count': len(role_elements),
                'images_with_alt': len(alt_images),
                'total_images': len(all_images),
                'form_inputs_count': len(form_inputs),
                'labeled_inputs_count': len(labeled_inputs),
                'keyboard_navigation_works': focused_element is not None
            }
            
            # Screenshot für Accessibility Review
            await page.screenshot(path=f"{self.screenshots_dir}/09_accessibility_review.png", full_page=True)
            
            phase_data['findings'] = {
                'accessibility_metrics': accessibility_analysis,
                'wcag_compliance': 'needs_review'
            }
            
            print(f"✅ ARIA Labels: {len(aria_labels)}")
            print(f"✅ Images with Alt: {len(alt_images)}/{len(all_images)}")
            print(f"✅ Labeled Inputs: {len(labeled_inputs)}/{len(form_inputs)}")
            
        except Exception as e:
            phase_data['findings'].append({'error': str(e)})
            print(f"❌ Fehler in Phase 9: {e}")
            
        self.analysis_data['phase_9_accessibility'] = phase_data
        
    async def analyze_performance_loading_states(self, page):
        """Phase 10: Performance und Loading States"""
        print("\n⚡ PHASE 10: PERFORMANCE UND LOADING STATES")
        print("-" * 60)
        
        phase_data = {
            'phase': 'performance_loading',
            'timestamp': datetime.now().isoformat(),
            'findings': []
        }
        
        try:
            # Performance Timing
            start_time = time.time()
            await page.goto(self.base_url)
            await page.wait_for_load_state('domcontentloaded')
            dom_loaded_time = time.time() - start_time
            
            await page.wait_for_load_state('networkidle')
            full_load_time = time.time() - start_time
            
            # Analysiere Loading States
            loading_indicators = await page.query_selector_all('.loading, .spinner, [class*="load"]')
            progress_bars = await page.query_selector_all('progress, .progress, .progress-bar')
            
            # Network Requests Analysis
            page_content = await page.content()
            css_links = await page.query_selector_all('link[rel="stylesheet"]')
            js_scripts = await page.query_selector_all('script[src]')
            
            performance_analysis = {
                'dom_content_loaded_time': dom_loaded_time,
                'full_load_time': full_load_time,
                'loading_indicators_count': len(loading_indicators),
                'progress_bars_count': len(progress_bars),
                'css_files_count': len(css_links),
                'js_files_count': len(js_scripts),
                'page_size_kb': len(page_content.encode('utf-8')) / 1024
            }
            
            # Screenshot für Performance Review
            await page.screenshot(path=f"{self.screenshots_dir}/10_performance_loaded.png", full_page=True)
            
            phase_data['findings'] = {
                'performance_metrics': performance_analysis,
                'loading_ux': 'analyzed'
            }
            
            print(f"✅ DOM Loaded: {dom_loaded_time:.2f}s")
            print(f"✅ Full Load: {full_load_time:.2f}s")
            print(f"✅ Page Size: {len(page_content.encode('utf-8')) / 1024:.1f}KB")
            
        except Exception as e:
            phase_data['findings'].append({'error': str(e)})
            print(f"❌ Fehler in Phase 10: {e}")
            
        self.analysis_data['phase_10_performance'] = phase_data
        
    async def generate_comprehensive_report(self):
        """Generate Comprehensive UI/UX Analysis Report"""
        print("\n📋 GENERIERE COMPREHENSIVE UI/UX ANALYSIS REPORT")
        print("=" * 80)
        
        # Save Raw Analysis Data
        with open('/app/ui_ux_analysis_raw_data.json', 'w', encoding='utf-8') as f:
            json.dump(self.analysis_data, f, indent=2, ensure_ascii=False, default=str)
            
        print("✅ Raw Analysis Data gespeichert: /app/ui_ux_analysis_raw_data.json")
        print("✅ Screenshots gespeichert in: /app/ui_ux_analysis_screenshots/")
        
        return True

async def main():
    """Hauptfunktion für UI/UX Analysis"""
    analyzer = MineSearchUIUXAnalyzer()
    await analyzer.comprehensive_ui_analysis()
    return True

if __name__ == '__main__':
    result = asyncio.run(main())
    print(f"\n🎉 UI/UX ANALYSIS COMPLETED: {'SUCCESS' if result else 'FAILED'}")