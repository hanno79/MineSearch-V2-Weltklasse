---
command: branch-push
description: Erstellt einen neuen Branch, committed alle Änderungen und pusht zu GitHub
---

# Branch erstellen und pushen

Dieses Command erstellt automatisch einen neuen Branch mit Zeitstempel, committed alle Änderungen und pusht zu GitHub.

## Schritt 1: Branch-Name generieren und erstellen
```bash
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BRANCH_NAME="update_${TIMESTAMP}"
echo "🌿 Erstelle neuen Branch: $BRANCH_NAME"
git checkout -b $BRANCH_NAME
```

## Schritt 2: Alle Änderungen stagen
```bash
echo "📦 Stage alle Änderungen..."
git add -A
```

## Schritt 3: Status anzeigen
```bash
echo "📊 Git Status:"
git status --short
```

## Schritt 4: Commit erstellen
```bash
echo "💾 Erstelle Commit..."
COMMIT_MSG="🚀 Auto-Update $(date +"%d.%m.%Y %H:%M") - Alle Änderungen"
git commit -m "$COMMIT_MSG" || echo "⚠️ Keine Änderungen zum Committen vorhanden"
```

## Schritt 5: Branch zu GitHub pushen
```bash
echo "🔄 Push zu GitHub..."
git push -u origin $BRANCH_NAME
```

## Schritt 6: Erfolg bestätigen
```bash
echo "✅ Branch $BRANCH_NAME wurde erfolgreich erstellt und gepusht!"
echo "🔗 GitHub URL: https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/tree/$BRANCH_NAME"
```