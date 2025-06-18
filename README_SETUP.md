# GitHub Setup Instructions for MineSearch

## 🚀 Quick Setup Guide

Diese Anleitung erklärt, wie du die erstellten GitHub Actions und Docker-Konfigurationen in dein Repository einrichtest.

## 📁 Erstellte Dateien

### GitHub Actions Workflows (.github/workflows/)
1. **ci.yml** - Haupt-CI/CD Pipeline mit Tests, Linting und Coverage
2. **docker.yml** - Docker Build und Push zu GitHub Container Registry
3. **codeql.yml** - Security Scanning mit GitHub CodeQL
4. **dependency-review.yml** - Überprüfung von Dependencies bei PRs

### GitHub Konfiguration (.github/)
5. **dependabot.yml** - Automatische Dependency Updates
6. **ISSUE_TEMPLATE/bug_report.md** - Bug Report Template
7. **ISSUE_TEMPLATE/feature_request.md** - Feature Request Template
8. **pull_request_template.md** - Pull Request Template

### Docker Konfiguration
9. **Dockerfile** - Multi-stage Docker Build
10. **docker-compose.yml** - Docker Compose Setup
11. **.dockerignore** - Docker Ignore File

## 📋 Setup Schritte

### 1. Dateien ins Repository kopieren

```bash
# Clone dein Repository
git clone https://github.com/hanno79/MineSearch.git
cd MineSearch

# Kopiere die .github Ordner Struktur
cp -r /app/.github .

# Kopiere Docker Dateien
cp /app/Dockerfile .
cp /app/docker-compose.yml .
cp /app/.dockerignore .

# Commit und Push
git add .
git commit -m "Add GitHub Actions CI/CD pipeline and Docker configuration"
git push origin main
```

### 2. Repository Secrets einrichten

Gehe zu: https://github.com/hanno79/MineSearch/settings/secrets/actions

Füge folgende Secrets hinzu (falls benötigt):
- `DB_PASSWORD` - Passwort für PostgreSQL (für Production)
- Weitere API Keys können als Secrets hinterlegt werden

### 3. Branch Protection Rules

Gehe zu: https://github.com/hanno79/MineSearch/settings/branches

Erstelle eine Rule für `main`:
- ✅ Require pull request reviews before merging
- ✅ Require status checks to pass before merging
  - Required checks: `test`, `security`
- ✅ Require branches to be up to date before merging
- ✅ Include administrators

### 4. GitHub Pages für Coverage Reports (Optional)

1. Gehe zu: Settings → Pages
2. Source: Deploy from a branch
3. Branch: `gh-pages` (wird automatisch erstellt)

## 🔧 Lokale Entwicklung

### Mit Docker Compose:
```bash
# Starte die Anwendung
docker-compose up -d

# Logs anzeigen
docker-compose logs -f

# Stoppen
docker-compose down
```

### Ohne Docker:
```bash
# Virtual Environment erstellen
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate  # Windows

# Dependencies installieren
pip install -r requirements.txt

# Anwendung starten
python run.py
```

## 🧪 Tests lokal ausführen

```bash
# Alle Tests
pytest tests/ -v

# Mit Coverage
pytest tests/ -v --cov=src --cov-report=html

# Linting
flake8 src/
black --check src/

# Type Checking
mypy src/
```

## 📊 CI/CD Pipeline Features

- **Automatische Tests** bei jedem Push und PR
- **Code Quality Checks** (Flake8, Black, MyPy)
- **Security Scanning** mit Trivy und CodeQL
- **Dependency Updates** mit Dependabot
- **Docker Images** werden automatisch gebaut und zu ghcr.io gepusht
- **Coverage Reports** mit Codecov Integration

## 🐳 Docker Registry

Nach dem ersten erfolgreichen Build sind Images verfügbar unter:
```
ghcr.io/hanno79/minesearch:latest
ghcr.io/hanno79/minesearch:main
ghcr.io/hanno79/minesearch:<version>
```

## ⚠️ Wichtige Hinweise

1. Die CI Pipeline läuft bei jedem Push zu `main` oder `develop`
2. Docker Images werden nur bei Pushes zu `main` gebaut
3. Secrets müssen vor dem ersten Run konfiguriert werden
4. Die Pipeline verwendet Ubuntu Latest und Python 3.10

## 🆘 Troubleshooting

### Pipeline fehlschlägt:
1. Check die Logs in der Actions Tab
2. Stelle sicher, dass alle Dependencies in requirements.txt sind
3. Überprüfe, ob alle Secrets korrekt gesetzt sind

### Docker Build fehlschlägt:
1. Teste lokal mit: `docker build -t minesearch .`
2. Überprüfe die .dockerignore Datei
3. Stelle sicher, dass alle benötigten Dateien kopiert werden

## 📚 Weitere Ressourcen

- [GitHub Actions Dokumentation](https://docs.github.com/en/actions)
- [Docker Compose Dokumentation](https://docs.docker.com/compose/)
- [Dependabot Dokumentation](https://docs.github.com/en/code-security/dependabot)