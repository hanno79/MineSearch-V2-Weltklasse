# 🔑 Deploy Key Setup für MineSearch

## Schritt 1: Deploy Key zu GitHub hinzufügen

1. **Gehe zu den Repository-Einstellungen:**
   https://github.com/hanno79/MineSearch/settings/keys

2. **Klicke auf "Add deploy key"**

3. **Fülle das Formular aus:**
   - **Title:** `Claude Code Deploy Key`
   - **Key:** Kopiere diese Zeile komplett:
   ```
   ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDdQv/1r+pm4AikZW3pGT8eWzU7wH9KKRMFh1LMfQbkz claude-code-minesearch-deploy
   ```
   - **✅ Allow write access** (Wichtig! Haken setzen)

4. **Klicke auf "Add key"**

## Schritt 2: SSH Config einrichten (in Claude Code)

Ich richte jetzt die SSH-Konfiguration ein: