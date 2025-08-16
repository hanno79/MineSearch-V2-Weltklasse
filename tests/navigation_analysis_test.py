"""
Author: rahn
Datum: 16.08.2025
Version: 1.0
Beschreibung: Navigation Structure Analysis für Quebec Mining Test
"""

import asyncio
from playwright.async_api import async_playwright

class NavigationAnalysisTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        
    async def analyze_navigation(self):
        """Analyze current navigation structure"""
        print("🔍 NAVIGATION STRUCTURE ANALYSIS")
        print("=" * 50)
        
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=False)
            page = await browser.new_page()
            
            await page.goto(f"{self.base_url}/static/index.html")
            await page.wait_for_load_state("networkidle")
            
            # Analyze all navigation elements
            nav_analysis = await page.evaluate("""
                () => {
                    // Find all navigation items
                    const navItems = document.querySelectorAll('nav a, .nav-item, .navigation a, [onclick*="Tab"], [data-tab]');
                    const navData = [];
                    
                    navItems.forEach((item, index) => {
                        navData.push({
                            index: index,
                            text: item.textContent.trim(),
                            href: item.href || 'no-href',
                            onclick: item.getAttribute('onclick') || 'no-onclick',
                            dataTab: item.getAttribute('data-tab') || 'no-data-tab',
                            className: item.className,
                            id: item.id || 'no-id'
                        });
                    });
                    
                    // Also find any buttons or upload elements
                    const uploadElements = document.querySelectorAll('input[type="file"], [class*="upload"], [id*="upload"]');
                    const uploadData = Array.from(uploadElements).map(el => ({
                        type: el.tagName,
                        id: el.id || 'no-id',
                        className: el.className,
                        text: el.textContent?.trim() || 'no-text'
                    }));
                    
                    // Find tabs or sections
                    const sections = document.querySelectorAll('[id*="tab"], .tab, .section, [class*="tab"]');
                    const sectionData = Array.from(sections).map(el => ({
                        id: el.id || 'no-id',
                        className: el.className,
                        visible: !el.hidden && el.style.display !== 'none'
                    }));
                    
                    return {
                        navItems: navData,
                        uploadElements: uploadData,
                        sections: sectionData,
                        totalNavItems: navData.length
                    };
                }
            """)
            
            await browser.close()
            
            print(f"📋 NAVIGATION ITEMS FOUND: {nav_analysis['totalNavItems']}")
            for item in nav_analysis['navItems']:
                print(f"   {item['index']}: '{item['text']}' (data-tab: {item['dataTab']})")
            
            print(f"\n📤 UPLOAD ELEMENTS FOUND: {len(nav_analysis['uploadElements'])}")
            for upload in nav_analysis['uploadElements']:
                print(f"   - {upload['type']} (id: {upload['id']}, class: {upload['className']})")
            
            print(f"\n📁 SECTIONS FOUND: {len(nav_analysis['sections'])}")
            for section in nav_analysis['sections']:
                print(f"   - {section['id']} (visible: {section['visible']})")
            
            return nav_analysis
            
        except Exception as e:
            print(f"❌ Navigation analysis error: {e}")
            return None

# Main execution
if __name__ == "__main__":
    async def main():
        analyzer = NavigationAnalysisTest()
        await analyzer.analyze_navigation()
    
    asyncio.run(main())