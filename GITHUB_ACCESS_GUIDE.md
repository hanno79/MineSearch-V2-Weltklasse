# 🔑 GitHub Zugriff für Claude Code einrichten

## Option 1: Personal Access Token (PAT) - Empfohlen für temporären Zugriff

1. **Token erstellen:**
   - Gehe zu https://github.com/settings/tokens/new
   - Name: "Claude Code Temporary Access"
   - Expiration: 7 days (oder kürzer)
   - Scopes:
     - ✅ repo (Full control of private repositories)
     - ✅ workflow (Update GitHub Action workflows)
   
2. **Token in Claude Code verwenden:**
   ```bash
   # Setze das Token als Environment Variable
   export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
   
   # Oder konfiguriere Git direkt
   git config --global credential.helper store
   git remote set-url origin https://<token>@github.com/hanno79/MineSearch.git
   ```

## Option 2: Deploy Keys - Sicherer für längerfristigen Zugriff

Deploy Keys sind SSH-Schlüssel, die nur für ein spezifisches Repository gelten.

1. **SSH-Schlüssel generieren (in Claude Code):**
   ```bash
   ssh-keygen -t ed25519 -C "claude-code-minesearch" -f ~/.ssh/minesearch_deploy_key
   ```

2. **Public Key zu GitHub hinzufügen:**
   - Gehe zu https://github.com/hanno79/MineSearch/settings/keys
   - Click "Add deploy key"
   - Title: "Claude Code Deploy Key"
   - Key: [Inhalt von ~/.ssh/minesearch_deploy_key.pub]
   - ✅ Allow write access

3. **SSH in Git konfigurieren:**
   ```bash
   # SSH config
   echo "Host github-minesearch
     HostName github.com
     User git
     IdentityFile ~/.ssh/minesearch_deploy_key" >> ~/.ssh/config
   
   # Remote URL ändern
   git remote set-url origin git@github-minesearch:hanno79/MineSearch.git
   ```

## Option 3: GitHub App - Beste Lösung für Automation

1. **GitHub App erstellen:**
   - https://github.com/settings/apps/new
   - Nur die nötigen Permissions
   - Installiere sie nur für MineSearch repo

2. **App Token verwenden:**
   ```bash
   # App authentication ist komplexer, aber sicherer
   # Benötigt JWT generation
   ```

## Option 4: Fine-grained Personal Access Token (Neu & Sicherer)

1. **Fine-grained Token erstellen:**
   - https://github.com/settings/personal-access-tokens/new
   - Repository access: Selected repositories → MineSearch
   - Permissions:
     - Contents: Read & Write
     - Actions: Write
     - Pull requests: Write
   - Expiration: 30 days

2. **Verwenden:**
   ```bash
   export GITHUB_TOKEN=github_pat_xxxxxxxxxxxx
   gh auth login --with-token < echo $GITHUB_TOKEN
   ```

## 🔒 Sicherheitshinweise

- **Niemals** Tokens in Code committen
- Tokens regelmäßig rotieren
- Minimale Permissions vergeben
- Nach Verwendung Token widerrufen

## 📝 Für Claude Code Session

Am einfachsten für eine Claude Code Session:

```bash
# 1. Erstelle ein Fine-grained PAT (Option 4)
# 2. In Claude Code:
export GITHUB_TOKEN=github_pat_xxxxxxxxxxxx

# 3. Clone und push
git clone https://github.com/hanno79/MineSearch.git
cd MineSearch
# ... Änderungen machen ...
git push

# 4. Nach der Session: Token widerrufen!
```

## 🚀 Aktueller Status

Ich habe bereits alle Dateien vorbereitet und committed in `/app/minesearch-new/`. 
Du musst nur noch:

1. Ein Token erstellen
2. In dein lokales Repo gehen
3. Pull von meinem vorbereiteten Commit:
   ```bash
   cd /app/minesearch-new
   git log --oneline  # Zeigt meinen Commit
   git push https://<token>@github.com/hanno79/MineSearch.git main
   ```

Oder einfacher: Kopiere alle Dateien aus `/app/minesearch-new/` in dein lokales Repo und pushe selbst!