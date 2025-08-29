# MineSearch Deployment Guide
Author: rahn  
Datum: 23.06.2025  
Version: 1.0

## Übersicht

Dieser Guide beschreibt die Deployment-Optionen für MineSearch in verschiedenen Umgebungen.

## Deployment-Optionen

### 1. Lokales Deployment (Entwicklung)

#### Requirements
- Python 3.10+
- 4GB RAM minimum
- 10GB freier Speicherplatz
- SQLite3

#### Installation
```bash
# Repository klonen
git clone https://github.com/yourusername/minesearch.git
cd minesearch

# Virtual Environment erstellen
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Dependencies installieren
pip install -r requirements.txt

# Playwright Browser installieren
playwright install chromium

# Environment Setup
cp .env.example .env
# API-Keys in .env eintragen
```

#### Starten
```bash
# Einzelner Befehl
streamlit run src/ui/main.py

# Mit Make
make run

# Mit Custom Port
streamlit run src/ui/main.py --server.port 8080
```

### 2. Docker Deployment

#### Dockerfile
```dockerfile
FROM python:3.10-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Working directory
WORKDIR /app

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright
RUN playwright install chromium
RUN playwright install-deps

# Application files
COPY . .

# Create data directories
RUN mkdir -p data logs

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run
CMD ["streamlit", "run", "src/ui/main.py", "--server.address", "0.0.0.0"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  minesearch:
    build: .
    container_name: minesearch-app
    ports:
      - "8501:8501"
    environment:
      - STREAMLIT_SERVER_HEADLESS=true
      - STREAMLIT_SERVER_ENABLE_CORS=false
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

#### Build & Run
```bash
# Build
docker build -t minesearch:latest .

# Run mit Docker
docker run -d \
  --name minesearch \
  -p 8501:8501 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  minesearch:latest

# Run mit Docker Compose
docker-compose up -d

# Logs anzeigen
docker logs -f minesearch
```

### 3. Cloud Deployment

#### AWS EC2

##### Instance Setup
```bash
# EC2 Instance: t3.medium oder größer
# OS: Ubuntu 20.04 LTS
# Security Group: Port 8501 öffnen

# Nach SSH Login:
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3-pip git

# Repository klonen und setup
git clone https://github.com/yourusername/minesearch.git
cd minesearch
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
playwright install-deps

# Systemd Service erstellen
sudo nano /etc/systemd/system/minesearch.service
```

##### Systemd Service
```ini
[Unit]
Description=MineSearch Application
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/minesearch
Environment="PATH=/home/ubuntu/minesearch/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/ubuntu/minesearch/venv/bin/streamlit run src/ui/main.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

##### Service starten
```bash
sudo systemctl daemon-reload
sudo systemctl enable minesearch
sudo systemctl start minesearch
sudo systemctl status minesearch
```

#### Google Cloud Run

##### Container Registry
```bash
# Build für Cloud Run
docker build -t gcr.io/YOUR-PROJECT-ID/minesearch:latest .

# Push to Registry
docker push gcr.io/YOUR-PROJECT-ID/minesearch:latest

# Deploy
gcloud run deploy minesearch \
  --image gcr.io/YOUR-PROJECT-ID/minesearch:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --port 8501
```

#### Heroku

##### Procfile
```
web: streamlit run src/ui/main.py --server.port $PORT --server.address 0.0.0.0
```

##### heroku.yml
```yaml
build:
  docker:
    web: Dockerfile
run:
  web: streamlit run src/ui/main.py --server.port $PORT --server.address 0.0.0.0
```

##### Deployment
```bash
# Heroku CLI installieren
heroku create minesearch-app
heroku stack:set container
git push heroku main
heroku open
```

### 4. Kubernetes Deployment

#### deployment.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: minesearch
  labels:
    app: minesearch
spec:
  replicas: 3
  selector:
    matchLabels:
      app: minesearch
  template:
    metadata:
      labels:
        app: minesearch
    spec:
      containers:
      - name: minesearch
        image: minesearch:latest
        ports:
        - containerPort: 8501
        env:
        - name: STREAMLIT_SERVER_HEADLESS
          value: "true"
        envFrom:
        - secretRef:
            name: minesearch-secrets
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /_stcore/health
            port: 8501
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /_stcore/health
            port: 8501
          initialDelaySeconds: 5
          periodSeconds: 10
        volumeMounts:
        - name: data
          mountPath: /app/data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: minesearch-pvc
```

#### service.yaml
```yaml
apiVersion: v1
kind: Service
metadata:
  name: minesearch-service
spec:
  selector:
    app: minesearch
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8501
  type: LoadBalancer
```

## Environment Variables

### Erforderliche Variablen
```bash
# API Keys (mindestens einer erforderlich)
CLAUDE_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
PERPLEXITY_API_KEY=pplx-...

# Optional
EXA_API_KEY=...
BRIGHTDATA_API_KEY=...
FIRECRAWL_API_KEY=...
SCRAPINGBEE_API_KEY=...
APIFY_API_KEY=...
```

### Performance-Tuning
```bash
# Connection Pools
MAX_CONNECTIONS=100
MAX_CONNECTIONS_PER_HOST=30

# Caching
CACHE_TTL_SECONDS=3600
CACHE_MAX_SIZE=1000

# Concurrency
MAX_CONCURRENT_AGENTS=10
MAX_CONCURRENT_SEARCHES=5

# Timeouts
DEFAULT_TIMEOUT=30
AGENT_TIMEOUT=60
```

### Datenbank
```bash
# SQLite (Standard)
DATABASE_URL=sqlite:///data/minesearch.db

# Analyse-/Wartungs-Skripte (optional):
# Diese Skripte (z. B. backend/analyze_database_contamination.py) lesen zuerst DATABASE_PATH,
# dann MINES_DB_PATH, dann (falls sqlite) DATABASE_URL und nutzen andernfalls einen Fallback.
# Setze dies, um Pfade ohne Codeänderung zu überschreiben.
DATABASE_PATH=/app/data/minesearch.db
# Kompatibilitäts-Variable, wird in Tests häufig gesetzt
MINES_DB_PATH=/app/backend/minesearch/database/mines.db

# PostgreSQL (Production)
DATABASE_URL=postgresql://user:pass@host:5432/minesearch

# MySQL
DATABASE_URL=mysql://user:pass@host:3306/minesearch
```

#### Monitoring‑Status‑Skript
Das Skript `backend/monitoring_status.py` ermittelt den Datenbankpfad in folgender
Priorität: `DATABASE_PATH` → `MINES_DB_PATH` → `DATABASE_URL` (nur `sqlite://`) →
Fallback (`backend/minesearch/database/mines.db` relativ zum Repo‑Root). Der
aufgelöste Pfad wird vor Nutzung validiert. Ist die Datei nicht vorhanden,
bricht das Skript mit einer klaren Fehlermeldung ab.

## Monitoring & Logging

### Logging Configuration
```python
# logging_config.py
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/minesearch.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'standard',
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['file']
    }
}
```

### Health Check Endpoint
```python
# Streamlit bietet automatisch:
# http://localhost:8501/_stcore/health
```

### Metriken
- Request-Zeiten pro Agent
- Cache Hit-Rate
- Aktive Verbindungen
- Memory-Nutzung

#### Speicherort & Aufbewahrung (NEU)
- Roh-Metriken werden NICHT im Git-Repository versioniert.
- Externer Speicher: S3/Azure Blob/Google Cloud Storage (empfohlen).
- Beispiel-Variablen:
  - METRICS_STORE=s3
  - METRICS_BUCKET=minesearch-metrics
  - METRICS_PREFIX=system/
  - METRICS_RETENTION_MAX=500      # letzte 500 Einträge
  - METRICS_ROTATE_DAYS=1          # tägliche Rotation
- Alternative: Git LFS möglich, bevorzugt jedoch Object Storage.
- Pipelines/Crons sollen alte Dateien gemäß Retention entfernen.

## Sicherheit

### Best Practices
1. **API Keys**
   - Niemals im Code committen
   - Environment Variables nutzen
   - Secrets Management verwenden

2. **Netzwerk**
   - HTTPS für Production
   - Firewall-Regeln konfigurieren
   - Rate Limiting aktivieren

3. **Updates**
   - Regelmäßige Dependency Updates
   - Security Patches zeitnah einspielen
   - Container Images aktuell halten

### Nginx Reverse Proxy
```nginx
server {
    listen 443 ssl http2;
    server_name minesearch.example.com;

    ssl_certificate /etc/letsencrypt/live/minesearch.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/minesearch.example.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    location /_stcore/stream {
        proxy_pass http://localhost:8501/_stcore/stream;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## Backup & Recovery

### Datenbank Backup
```bash
# SQLite Backup
sqlite3 data/minesearch.db ".backup data/backup/minesearch_$(date +%Y%m%d).db"

# PostgreSQL Backup
pg_dump -h localhost -U user minesearch > backup/minesearch_$(date +%Y%m%d).sql

# Automatisiertes Backup (Cron)
0 2 * * * /home/ubuntu/minesearch/scripts/backup.sh
```

### Recovery
```bash
# SQLite Recovery
cp data/backup/minesearch_20250623.db data/minesearch.db

# PostgreSQL Recovery
psql -h localhost -U user minesearch < backup/minesearch_20250623.sql
```

## Troubleshooting

### Häufige Probleme

#### Port bereits belegt
```bash
# Port 8501 bereits in Verwendung
lsof -i :8501
kill -9 <PID>
```

#### Memory-Probleme
```bash
# Swap hinzufügen
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### Playwright-Fehler
```bash
# Browser neu installieren
playwright install chromium
playwright install-deps
```

### Performance-Optimierung
1. **Database Indexing**
   ```sql
   CREATE INDEX idx_mines_name ON mines(name);
   CREATE INDEX idx_results_mine_field ON search_results(mine_id, field_name);
   ```

2. **Connection Pooling**
   - Erhöhe MAX_CONNECTIONS für mehr parallele Nutzer
   - Nutze Redis für Session-State in Multi-Instance Setup

3. **Caching**
   - Redis als externer Cache für Skalierung
   - CDN für statische Assets

## Maintenance

### Regular Tasks
- **Täglich**: Log-Rotation prüfen
- **Wöchentlich**: Datenbank-Backup
- **Monatlich**: Dependency Updates
- **Quartal**: Security Audit

### Update-Prozess
```bash
# Backup erstellen
./scripts/backup.sh

# Code aktualisieren
git pull origin main

# Dependencies aktualisieren
pip install -r requirements.txt --upgrade

# Migrationen ausführen (falls vorhanden)
python scripts/migrate.py

# Service neu starten
sudo systemctl restart minesearch
```