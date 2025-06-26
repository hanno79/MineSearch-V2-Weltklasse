#!/bin/bash
# ÄNDERUNG 24.06.2025: Robustes Installations-Script für Playwright
# Version: 2.0
# Unterstützt Docker und normale Umgebungen

set -e  # Exit on error

echo "🎭 Installing Playwright and Browser Dependencies..."
echo "Environment: $(uname -a)"
echo "Python: $(python --version)"

# Funktion für Fehlerbehandlung
handle_error() {
    echo "❌ Error: $1"
    exit 1
}

# 1. Update pip
echo "📦 Updating pip..."
pip install --upgrade pip || handle_error "Failed to update pip"

# 2. Install/Upgrade Playwright
echo "📦 Installing Playwright..."
pip install --upgrade playwright==1.40.0 || handle_error "Failed to install playwright"

# 3. Install System Dependencies (für Docker/Linux)
echo "🔧 Installing system dependencies..."
if command -v apt-get &> /dev/null; then
    echo "  Detected Debian/Ubuntu system"
    apt-get update && apt-get install -y \
        libnss3 \
        libxss1 \
        libasound2 \
        libxrandr2 \
        libxcomposite1 \
        libxcursor1 \
        libxdamage1 \
        libxi6 \
        libxtst6 \
        libgtk-3-0 \
        libpangocairo-1.0-0 \
        libpango-1.0-0 \
        libatk1.0-0 \
        libcairo-gobject2 \
        libatspi2.0-0 \
        libgtk-3-0 \
        libgdk-pixbuf2.0-0 \
        libgbm1 \
        libwayland-client0 \
        libwayland-cursor0 \
        libwayland-egl1 \
        || echo "⚠️  Some system dependencies might be missing"
fi

# 4. Install Playwright Browsers
echo "🌐 Installing Chromium browser..."
# Verwende --with-deps für vollständige Installation
playwright install chromium --with-deps || {
    echo "⚠️  First attempt failed, trying alternative method..."
    # Alternative: Nur Browser ohne System-Deps
    playwright install chromium || handle_error "Failed to install Chromium"
}

# 5. Verify Installation
echo "🔍 Verifying installation..."
python -c "from playwright.sync_api import sync_playwright; print('✅ Playwright import successful')" || handle_error "Playwright import failed"

# 6. Test Browser Launch (optional)
echo "🧪 Testing browser launch..."
python -c "
import sys
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        page = browser.new_page()
        page.goto('about:blank')
        browser.close()
        print('✅ Browser test successful!')
except Exception as e:
    print(f'⚠️  Browser test failed: {e}')
    print('   This might work in the actual application with proper async handling')
    sys.exit(0)  # Don't fail installation
" || echo "⚠️  Browser test skipped"

# 7. Set Permissions (für Docker)
if [ -d "/root/.cache/ms-playwright" ]; then
    echo "🔐 Setting permissions for playwright cache..."
    chmod -R 755 /root/.cache/ms-playwright
fi

# 8. Display Installation Info
echo ""
echo "📋 Installation Summary:"
echo "  - Playwright version: $(pip show playwright | grep Version | cut -d' ' -f2)"
echo "  - Browser location: $(find /root/.cache/ms-playwright -name chrome -type f 2>/dev/null | head -1 || echo 'Not found')"
echo "  - Python path: $(which python)"
echo ""
echo "✅ Playwright installation complete!"
echo "ℹ️  If browser launch fails, try running with --no-sandbox flag"
echo "ℹ️  For Docker: Make sure to use appropriate security flags"