# 📤 Upload Instructions for GitHub Pipeline

## Option 1: Manueller Upload (Empfohlen)

Alle Dateien befinden sich im Ordner `github-upload/`:

```bash
# 1. Lade das Archiv herunter: github-pipeline-files.tar.gz

# 2. Entpacke es in deinem lokalen Repository:
cd /pfad/zu/deinem/MineSearch
tar -xzf github-pipeline-files.tar.gz

# 3. Committe und pushe:
git add .
git commit -m "Add CI/CD pipeline, Docker configuration and GitHub workflows"
git push origin main
```

## Option 2: Direkt über GitHub Web Interface

1. Gehe zu https://github.com/hanno79/MineSearch
2. Klicke auf "Create new file"
3. Erstelle folgende Struktur:

### .github/workflows/ci.yml
```
[Kopiere Inhalt aus github-upload/.github/workflows/ci.yml]
```

### .github/workflows/docker.yml
```
[Kopiere Inhalt aus github-upload/.github/workflows/docker.yml]
```

### .github/workflows/codeql.yml
```
[Kopiere Inhalt aus github-upload/.github/workflows/codeql.yml]
```

### .github/workflows/dependency-review.yml
```
[Kopiere Inhalt aus github-upload/.github/workflows/dependency-review.yml]
```

### .github/dependabot.yml
```
[Kopiere Inhalt aus github-upload/.github/dependabot.yml]
```

### .github/ISSUE_TEMPLATE/bug_report.md
```
[Kopiere Inhalt aus github-upload/.github/ISSUE_TEMPLATE/bug_report.md]
```

### .github/ISSUE_TEMPLATE/feature_request.md
```
[Kopiere Inhalt aus github-upload/.github/ISSUE_TEMPLATE/feature_request.md]
```

### .github/pull_request_template.md
```
[Kopiere Inhalt aus github-upload/.github/pull_request_template.md]
```

### Dockerfile
```
[Kopiere Inhalt aus github-upload/Dockerfile]
```

### docker-compose.yml
```
[Kopiere Inhalt aus github-upload/docker-compose.yml]
```

### .dockerignore
```
[Kopiere Inhalt aus github-upload/.dockerignore]
```

## Option 3: Mit GitHub CLI (wenn du ein Access Token hast)

```bash
# Setze dein GitHub Token
export GITHUB_TOKEN=your_token_here

# Clone, kopiere Dateien und pushe
git clone https://github.com/hanno79/MineSearch.git
cd MineSearch
cp -r /app/github-upload/.github .
cp /app/github-upload/Dockerfile .
cp /app/github-upload/docker-compose.yml .
cp /app/github-upload/.dockerignore .
git add .
git commit -m "Add CI/CD pipeline and Docker configuration"
git push
```

## 📁 Dateistruktur

```
github-upload/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   ├── docker.yml
│   │   ├── codeql.yml
│   │   └── dependency-review.yml
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   ├── dependabot.yml
│   └── pull_request_template.md
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
└── README_SETUP.md
```

## ✅ Nach dem Upload

1. Die GitHub Actions werden automatisch aktiviert
2. Der erste CI-Run startet beim nächsten Push
3. Konfiguriere ggf. Secrets in den Repository Settings
4. Aktiviere Branch Protection Rules für `main`

Die vollständige Anleitung findest du in `README_SETUP.md`!