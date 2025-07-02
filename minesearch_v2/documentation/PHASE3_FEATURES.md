# MineSearch v2 - Phase 3 Features Dokumentation

**Author:** rahn  
**Datum:** 01.07.2025  
**Version:** 1.0

## Übersicht

Phase 3 fokussiert sich auf erweiterte Datenfelder, externe API-Integrationen und umfassendes Monitoring. Diese Features erweitern MineSearch v2 zu einer vollständigen Mining-Intelligence-Plattform.

## 1. Erweiterte Datenfelder

### 1.1 Umweltgenehmigungen Schema

```python
class EnvironmentalPermit(Base):
    __tablename__ = 'environmental_permits'
    
    id = Column(Integer, primary_key=True)
    mine_id = Column(Integer, ForeignKey('mines.id'))
    permit_type = Column(String(100))  # EIA, Water Use, Air Quality, etc.
    permit_number = Column(String(100))
    issuing_authority = Column(String(255))
    issue_date = Column(Date)
    expiry_date = Column(Date)
    status = Column(String(50))  # Active, Expired, Pending, Revoked
    conditions = Column(JSON)
    compliance_status = Column(String(50))
    last_inspection = Column(Date)
    documents = Column(JSON)  # Links zu Permit-Dokumenten
    
    # Relationships
    mine = relationship("Mine")
    compliance_records = relationship("ComplianceRecord")
```

### 1.2 Bonds und Sicherheitsleistungen

```python
class SecurityBond(Base):
    __tablename__ = 'security_bonds'
    
    id = Column(Integer, primary_key=True)
    mine_id = Column(Integer, ForeignKey('mines.id'))
    bond_type = Column(String(100))  # Closure, Environmental, Performance
    amount = Column(Numeric(15, 2))
    currency = Column(String(3))
    provider = Column(String(255))  # Bank/Versicherung
    issue_date = Column(Date)
    maturity_date = Column(Date)
    status = Column(String(50))
    collateral_type = Column(String(100))
    review_frequency = Column(String(50))  # Annual, Bi-annual
    last_review = Column(Date)
    next_review = Column(Date)
    adjustment_history = Column(JSON)
    
    # Calculated fields
    @property
    def amount_usd(self):
        return self.amount * get_exchange_rate(self.currency, 'USD')
```

### 1.3 Restaurations-Timeline

```python
class RestorationPhase(Base):
    __tablename__ = 'restoration_phases'
    
    id = Column(Integer, primary_key=True)
    mine_id = Column(Integer, ForeignKey('mines.id'))
    phase_name = Column(String(255))
    phase_number = Column(Integer)
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(String(50))  # Planned, Active, Completed
    activities = Column(JSON)
    estimated_cost = Column(Numeric(15, 2))
    actual_cost = Column(Numeric(15, 2))
    completion_percentage = Column(Integer)
    key_milestones = Column(JSON)
    responsible_party = Column(String(255))
    monitoring_requirements = Column(JSON)
    
    # Methods
    def calculate_progress(self):
        """Berechne Fortschritt basierend auf Meilensteinen"""
        pass
```

### 1.4 Behördliche Auflagen

```python
class RegulatoryRequirement(Base):
    __tablename__ = 'regulatory_requirements'
    
    id = Column(Integer, primary_key=True)
    mine_id = Column(Integer, ForeignKey('mines.id'))
    requirement_type = Column(String(100))
    description = Column(Text)
    regulatory_body = Column(String(255))
    legal_reference = Column(String(255))
    compliance_deadline = Column(Date)
    reporting_frequency = Column(String(50))
    last_report_date = Column(Date)
    next_report_due = Column(Date)
    compliance_status = Column(String(50))
    penalties_for_non_compliance = Column(Text)
    compliance_history = Column(JSON)
```

### 1.5 Wassernutzungslizenzen

```python
class WaterLicense(Base):
    __tablename__ = 'water_licenses'
    
    id = Column(Integer, primary_key=True)
    mine_id = Column(Integer, ForeignKey('mines.id'))
    license_number = Column(String(100))
    water_source = Column(String(255))
    permitted_volume_daily = Column(Numeric(10, 2))  # m³/day
    permitted_volume_annual = Column(Numeric(15, 2))  # m³/year
    actual_usage_daily_avg = Column(Numeric(10, 2))
    quality_parameters = Column(JSON)
    discharge_limits = Column(JSON)
    monitoring_points = Column(JSON)
    issue_date = Column(Date)
    expiry_date = Column(Date)
    renewal_status = Column(String(50))
```

### 1.6 Kontaminierte Flächen

```python
class ContaminatedArea(Base):
    __tablename__ = 'contaminated_areas'
    
    id = Column(Integer, primary_key=True)
    mine_id = Column(Integer, ForeignKey('mines.id'))
    area_name = Column(String(255))
    location_coordinates = Column(JSON)  # Polygon coordinates
    area_size_hectares = Column(Numeric(10, 2))
    contamination_type = Column(String(100))
    contaminants = Column(JSON)
    risk_level = Column(String(50))  # High, Medium, Low
    remediation_status = Column(String(50))
    remediation_method = Column(String(255))
    estimated_remediation_cost = Column(Numeric(15, 2))
    target_completion_date = Column(Date)
    monitoring_frequency = Column(String(50))
    last_assessment_date = Column(Date)
```

### 1.7 Monitoring-Dauer

```python
class MonitoringProgram(Base):
    __tablename__ = 'monitoring_programs'
    
    id = Column(Integer, primary_key=True)
    mine_id = Column(Integer, ForeignKey('mines.id'))
    program_type = Column(String(100))  # Water, Air, Soil, Wildlife
    start_date = Column(Date)
    duration_years = Column(Integer)
    frequency = Column(String(50))
    parameters_monitored = Column(JSON)
    monitoring_locations = Column(JSON)
    responsible_party = Column(String(255))
    reporting_to = Column(String(255))
    budget_annual = Column(Numeric(10, 2))
    success_criteria = Column(JSON)
    adaptive_management_triggers = Column(JSON)
```

## 2. API-Integrationen

### 2.1 GESTIM Integration (Quebec)

```python
class GESTIMConnector:
    """
    Integration mit Quebec's GESTIM System
    https://gestim.mines.gouv.qc.ca/
    """
    
    BASE_URL = "https://gestim.mines.gouv.qc.ca/api/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = aiohttp.ClientSession()
    
    async def get_mining_titles(self, region: str) -> List[Dict]:
        """Hole Mining Titles für eine Region"""
        endpoint = f"{self.BASE_URL}/titles"
        params = {
            "region": region,
            "status": "active",
            "include": "claims,leases,permits"
        }
        return await self._make_request("GET", endpoint, params)
    
    async def get_claim_details(self, claim_id: str) -> Dict:
        """Detaillierte Claim-Informationen"""
        endpoint = f"{self.BASE_URL}/claims/{claim_id}"
        return await self._make_request("GET", endpoint)
    
    async def get_environmental_obligations(self, title_id: str) -> Dict:
        """Umweltauflagen für einen Title"""
        endpoint = f"{self.BASE_URL}/titles/{title_id}/environmental"
        return await self._make_request("GET", endpoint)
```

### 2.2 BLM MLRS Integration (USA)

```python
class BLMConnector:
    """
    Bureau of Land Management - Mineral & Land Records System
    https://mlrs.blm.gov/
    """
    
    BASE_URL = "https://api.blm.gov/mlrs/v1"
    
    async def search_mining_claims(self, state: str, commodity: str = None) -> List[Dict]:
        """Suche Mining Claims in einem Bundesstaat"""
        endpoint = f"{self.BASE_URL}/claims/search"
        params = {
            "state": state,
            "commodity": commodity,
            "status": "active",
            "format": "json"
        }
        return await self._make_request("GET", endpoint, params)
    
    async def get_case_recordation(self, case_number: str) -> Dict:
        """Case Recordation Details"""
        endpoint = f"{self.BASE_URL}/cases/{case_number}"
        return await self._make_request("GET", endpoint)
```

### 2.3 SARIG Integration (Australien)

```python
class SARIGConnector:
    """
    South Australian Resources Information Gateway
    https://map.sarig.sa.gov.au/
    """
    
    WFS_URL = "https://sarig.pir.sa.gov.au/geoserver/wfs"
    
    async def get_mineral_tenements(self, bbox: Tuple[float, float, float, float]) -> List[Dict]:
        """Hole Mineral Tenements in einer Bounding Box"""
        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeName": "sarig:MineralTenements",
            "bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
            "outputFormat": "application/json"
        }
        return await self._make_request("GET", self.WFS_URL, params)
```

### 2.4 API Integration Manager

```python
class ExternalAPIManager:
    """Zentrale Verwaltung aller externen APIs"""
    
    def __init__(self):
        self.connectors = {
            "GESTIM": GESTIMConnector(config.GESTIM_API_KEY),
            "BLM": BLMConnector(config.BLM_API_KEY),
            "SARIG": SARIGConnector(config.SARIG_API_KEY),
            "INGEMMET": INGEMMETConnector(config.INGEMMET_API_KEY),
            "SERNAGEOMIN": SERNAGEOMINConnector(config.SERNAGEOMIN_API_KEY)
        }
        self.cache = CacheManager()
    
    async def enrich_mine_data(self, mine: Mine) -> Dict:
        """Reichere Minendaten mit externen Quellen an"""
        enriched_data = {}
        
        # Wähle passende APIs basierend auf Land
        apis = self._select_apis_for_country(mine.country)
        
        # Parallele API-Aufrufe
        tasks = []
        for api_name in apis:
            connector = self.connectors[api_name]
            tasks.append(self._fetch_api_data(connector, mine))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Merge results
        for result in results:
            if not isinstance(result, Exception):
                enriched_data.update(result)
        
        return enriched_data
```

## 3. Monitoring & Analytics

### 3.1 Metrics Definition

```python
# metrics/definitions.py
METRICS = {
    "api_metrics": {
        "api_request_total": Counter(
            "api_request_total",
            "Total API requests",
            ["method", "endpoint", "status"]
        ),
        "api_request_duration": Histogram(
            "api_request_duration_seconds",
            "API request duration",
            ["method", "endpoint"]
        ),
        "api_errors_total": Counter(
            "api_errors_total",
            "Total API errors",
            ["method", "endpoint", "error_type"]
        )
    },
    "search_metrics": {
        "search_requests_total": Counter(
            "search_requests_total",
            "Total search requests",
            ["search_type", "model"]
        ),
        "search_quality_score": Histogram(
            "search_quality_score",
            "Search result quality scores",
            ["search_type"],
            buckets=[0, 25, 50, 75, 90, 100]
        ),
        "cache_hit_rate": Gauge(
            "cache_hit_rate",
            "Cache hit rate percentage"
        )
    },
    "business_metrics": {
        "mines_searched_total": Counter(
            "mines_searched_total",
            "Total mines searched",
            ["country", "commodity"]
        ),
        "data_completeness": Gauge(
            "data_completeness_percentage",
            "Average data completeness",
            ["country"]
        ),
        "active_users": Gauge(
            "active_users_total",
            "Currently active users"
        )
    }
}
```

### 3.2 Dashboard Design

```yaml
# grafana/dashboards/minesearch_overview.json
{
  "dashboard": {
    "title": "MineSearch v2 Overview",
    "panels": [
      {
        "title": "API Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(api_request_duration_seconds_sum[5m])/rate(api_request_duration_seconds_count[5m])",
            "legendFormat": "{{endpoint}}"
          }
        ]
      },
      {
        "title": "Search Quality Distribution",
        "type": "heatmap",
        "targets": [
          {
            "expr": "search_quality_score_bucket"
          }
        ]
      },
      {
        "title": "Cache Performance",
        "type": "stat",
        "targets": [
          {
            "expr": "cache_hit_rate",
            "format": "percent"
          }
        ]
      },
      {
        "title": "Top Searched Mines",
        "type": "table",
        "targets": [
          {
            "expr": "topk(10, increase(mines_searched_total[24h]))"
          }
        ]
      }
    ]
  }
}
```

### 3.3 Alert Strategy

```python
# monitoring/alerts.py
ALERT_RULES = [
    {
        "name": "HighAPIErrorRate",
        "expr": "rate(api_errors_total[5m]) > 0.05",
        "for": "5m",
        "labels": {
            "severity": "warning"
        },
        "annotations": {
            "summary": "High API error rate detected",
            "description": "Error rate is {{ $value }} errors per second"
        }
    },
    {
        "name": "LowCacheHitRate",
        "expr": "cache_hit_rate < 40",
        "for": "15m",
        "labels": {
            "severity": "info"
        },
        "annotations": {
            "summary": "Cache hit rate below threshold",
            "description": "Cache hit rate is {{ $value }}%"
        }
    },
    {
        "name": "SlowAPIResponse",
        "expr": "histogram_quantile(0.95, api_request_duration_seconds) > 5",
        "for": "10m",
        "labels": {
            "severity": "warning"
        },
        "annotations": {
            "summary": "API response time degraded",
            "description": "95th percentile response time is {{ $value }} seconds"
        }
    }
]
```

### 3.4 Analytics Pipeline

```python
class AnalyticsPipeline:
    """Pipeline für Datenanalyse und Insights"""
    
    def __init__(self):
        self.processors = [
            DataQualityAnalyzer(),
            TrendDetector(),
            AnomalyDetector(),
            RecommendationEngine()
        ]
    
    async def analyze_mine_data(self, mine_id: int) -> Dict:
        """Analysiere Minendaten für Insights"""
        insights = {}
        
        # Hole historische Daten
        historical_data = await self.get_historical_data(mine_id)
        
        # Führe Analysen durch
        for processor in self.processors:
            result = await processor.process(historical_data)
            insights[processor.name] = result
        
        return insights
    
    async def generate_market_report(self, commodity: str, region: str) -> Dict:
        """Generiere Marktbericht für Rohstoff/Region"""
        report = {
            "commodity": commodity,
            "region": region,
            "generated_at": datetime.utcnow(),
            "sections": {}
        }
        
        # Produktionstrends
        report["sections"]["production_trends"] = await self.analyze_production_trends(
            commodity, region
        )
        
        # Preiskorrelationen
        report["sections"]["price_correlations"] = await self.analyze_price_correlations(
            commodity
        )
        
        # Zukunftsprognosen
        report["sections"]["forecasts"] = await self.generate_forecasts(
            commodity, region
        )
        
        return report
```

## 4. Implementierungs-Roadmap

### Phase 3.1 - Erweiterte Datenfelder (3 Wochen)
1. Datenbankschema erweitern
2. Models und Repositories implementieren
3. UI-Komponenten für neue Felder
4. Datenextraktion anpassen
5. Tests und Validierung

### Phase 3.2 - API-Integrationen (4 Wochen)
1. API-Connectors entwickeln
2. Authentication und Rate Limiting
3. Daten-Mapping und Transformation
4. Error Handling und Retry Logic
5. Integration Tests

### Phase 3.3 - Monitoring Setup (2 Wochen)
1. Prometheus und Grafana Setup
2. Metrics instrumentieren
3. Dashboards erstellen
4. Alert Rules konfigurieren
5. Log Aggregation einrichten

### Phase 3.4 - Analytics (3 Wochen)
1. Analytics Pipeline entwickeln
2. ML-Modelle trainieren
3. Report-Generierung
4. API für Analytics
5. Frontend-Integration

## 5. Erwartete Ergebnisse

- **Datenqualität**: 40% mehr Datenfelder pro Mine
- **Aktualität**: Tägliche Updates aus offiziellen Quellen
- **Compliance**: Vollständige Übersicht über regulatorische Anforderungen
- **Insights**: Predictive Analytics für Markttrends
- **Transparenz**: Real-time Monitoring aller Systeme

## 6. Sicherheitsüberlegungen

### API-Sicherheit
- OAuth 2.0 für externe APIs
- API Key Rotation alle 90 Tage
- Verschlüsselte Speicherung von Credentials
- Audit Logs für alle API-Zugriffe

### Datenschutz
- GDPR-konforme Datenspeicherung
- Anonymisierung von Nutzerdaten
- Recht auf Löschung implementiert
- Datenminimierung Prinzip

### Compliance
- SOC 2 Type II Zertifizierung anstreben
- Regelmäßige Security Audits
- Penetration Testing
- Incident Response Plan

---

**Hinweis:** Phase 3 ist als langfristige Vision konzipiert und wird iterativ über 6-12 Monate implementiert. Die Priorisierung erfolgt basierend auf Nutzer-Feedback und Business Value.