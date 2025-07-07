#!/bin/bash
# Author: rahn
# Datum: 04.07.2025
# Version: 1.0
# Beschreibung: Test-Befehle für MineSearch API

echo "=================================================="
echo "MINESEARCH API TEST-BEFEHLE"
echo "=================================================="

API_URL="http://localhost:8000/api"

echo -e "\n[1] MODELL-ÜBERSICHT"
echo "Verfügbare Modelle abrufen:"
echo "curl -X GET \"${API_URL}/models\" | python -m json.tool"

echo -e "\n[2] EINZELMODELL-TESTS"
echo "=================================================="

echo -e "\n2.1 Perplexity Sonar (schnell):"
cat << 'EOF'
curl -X POST "${API_URL}/search?model=sonar" \
-H "Content-Type: application/json" \
-d '{
  "mine_name": "Jeffrey Mine",
  "country": "Canada",
  "commodity": "Asbestos",
  "region": "Quebec"
}' | python -m json.tool
EOF

echo -e "\n2.2 Perplexity Sonar Pro (empfohlen):"
cat << 'EOF'
curl -X POST "${API_URL}/search?model=sonar-pro" \
-H "Content-Type: application/json" \
-d '{
  "mine_name": "Jeffrey Mine",
  "country": "Canada",
  "commodity": "Asbestos",
  "region": "Quebec"
}' | python -m json.tool
EOF

echo -e "\n2.3 OpenRouter DeepSeek Free (kostenlos):"
cat << 'EOF'
curl -X POST "${API_URL}/search?model=deepseek-free" \
-H "Content-Type: application/json" \
-d '{
  "mine_name": "Jeffrey Mine",
  "country": "Canada",
  "commodity": "Asbestos",
  "region": "Quebec"
}' | python -m json.tool
EOF

echo -e "\n[3] MULTI-MODELL-TESTS"
echo "=================================================="

echo -e "\n3.1 Kombination Perplexity + OpenRouter:"
cat << 'EOF'
curl -X POST "${API_URL}/search/multi" \
-H "Content-Type: application/json" \
-d '{
  "model_ids": ["perplexity:sonar-pro", "openrouter:deepseek-free"],
  "mine_name": "Jeffrey Mine",
  "country": "Canada",
  "commodity": "Asbestos",
  "region": "Quebec"
}' | python -m json.tool
EOF

echo -e "\n3.2 Alle kostenlosen Modelle:"
cat << 'EOF'
curl -X POST "${API_URL}/search/multi" \
-H "Content-Type: application/json" \
-d '{
  "model_ids": ["openrouter:deepseek-free", "openrouter:deepseek-chat"],
  "mine_name": "Escondida",
  "country": "Chile",
  "commodity": "Copper",
  "region": "Antofagasta"
}' | python -m json.tool
EOF

echo -e "\n[4] WEITERE TEST-MINEN"
echo "=================================================="

echo -e "\n4.1 Escondida (Chile):"
cat << 'EOF'
curl -X POST "${API_URL}/search?model=sonar-pro" \
-H "Content-Type: application/json" \
-d '{
  "mine_name": "Escondida",
  "country": "Chile",
  "commodity": "Copper",
  "region": "Antofagasta"
}' | python -m json.tool
EOF

echo -e "\n4.2 Jwaneng Diamond Mine (Botswana):"
cat << 'EOF'
curl -X POST "${API_URL}/search?model=sonar-pro" \
-H "Content-Type: application/json" \
-d '{
  "mine_name": "Jwaneng Diamond Mine",
  "country": "Botswana",
  "commodity": "Diamond"
}' | python -m json.tool
EOF

echo -e "\n[5] PERFORMANCE-TEST"
echo "=================================================="
echo "Parallele Anfragen mit time-Messung:"

cat << 'EOF'
# Zeitmessung für einzelne Anfrage
time curl -X POST "${API_URL}/search?model=sonar" \
-H "Content-Type: application/json" \
-d '{"mine_name": "Jeffrey Mine", "country": "Canada", "commodity": "Asbestos"}' \
-o /dev/null -s -w "%{time_total}s\n"
EOF

echo -e "\n[6] HEALTH-CHECK"
echo "=================================================="
echo "API-Status prüfen:"
echo "curl -X GET \"${API_URL}/health\""

echo -e "\n=================================================="
echo "HINWEISE:"
echo "- Fügen Sie --max-time 120 hinzu für Timeout-Kontrolle"
echo "- Verwenden Sie -v für verbose Output"
echo "- Speichern mit -o output.json"
echo "=================================================="