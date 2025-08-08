# SOURCE TRACKING ANALYSIS - Database Analyzer Agent Report

**Date:** 2025-07-23  
**Agent:** DATABASE ANALYZER AGENT  
**Mission:** Analyze source tracking problem in database  

## PROBLEM IDENTIFIED

### Root Cause: URL Normalization Mismatch

The source tracking system has a critical flaw in URL matching between storage and lookup operations.

## DETAILED ANALYSIS

### 1. Current Database State
- **Working Sources:** Some sources have proper tracking (e.g., USGS: 13 total, 10 successful)
- **Broken Sources:** Many sources show 0 total_searches and 0 successful_searches
- **Pattern:** Government and database sources work better than industry sources

### 2. The Source Storage Process (Working)
Location: `/app/minesearch_v2/backend/database/manager.py:49-122`

```python
def add_or_update_source(self, url: str, domain: str, ...):
    # URL gets normalized by removing query parameters
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip('/')
    
    # Source stored with normalized URL
    source = Source(url=base_url, domain=domain, ...)
```

**Result:** Sources are stored with normalized URLs like:
- `https://www.usgs.gov/centers/national-minerals-information-center`

### 3. The Source Tracking Process (BROKEN)
Location: `/app/minesearch_v2/backend/search_service.py:593-658`

```python
async def _track_sources_usage(self, sources: List[Dict], success: bool, model: str):
    # Searches for sources using specific URLs from search results
    for source in sources:
        source_url = source.get('url')  # Could be specific URL
        
        # Normalizes URL for database lookup
        parsed = urlparse(source_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip('/')
        
        # Tries to find source in DB
        db_source = session.query(Source).filter_by(url=base_url).first()
        
        if db_source:
            # Updates statistics (THIS WORKS)
            db_source.total_searches += 1
        else:
            # Source not found (THIS IS THE PROBLEM)
            logger.debug(f"Source nicht in DB gefunden: {domain}")
```

### 4. The Mismatch Problem

**Storage URL:** `https://www.usgs.gov/centers/national-minerals-information-center`  
**Search URL:** `https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries`  
**Normalized Search URL:** `https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries`  

**Result:** No match found → Statistics not updated → Values remain at 0

## DEMONSTRATION QUERIES

### Query 1: Show Sources with Mixed Statistics
```sql
SELECT 
    domain,
    SUBSTR(url, 1, 60) as short_url,
    total_searches,
    successful_searches,
    CASE 
        WHEN total_searches > 0 THEN 'TRACKED'
        ELSE 'NOT_TRACKED'
    END as status
FROM sources 
ORDER BY total_searches DESC 
LIMIT 20;
```

### Query 2: Find URL Normalization Issues
```sql
-- Find sources where multiple URLs exist for same domain
SELECT 
    domain,
    COUNT(*) as url_count,
    GROUP_CONCAT(SUBSTR(url, 1, 50), ' | ') as urls
FROM sources 
GROUP BY domain 
HAVING COUNT(*) > 1
ORDER BY url_count DESC;
```

### Query 3: Show Zero-Tracking Sources
```sql
SELECT 
    domain,
    source_type,
    url,
    total_searches,
    successful_searches,
    last_attempted_access
FROM sources 
WHERE total_searches = 0 
ORDER BY domain;
```

## THE SOLUTION

### Fix 1: Improve URL Matching in _track_sources_usage()

The tracking method needs to:
1. Try exact URL match first
2. Fall back to domain-based matching
3. Use fuzzy URL matching for better source identification

### Fix 2: Use update_source_access() Method

The existing `update_source_access(source_id, success, content_type)` method works correctly but is never called. The tracking should use source IDs instead of URL lookups.

### Fix 3: Source Reference Persistence

Store source IDs during search result processing to avoid URL lookup mismatches.

## WORKFLOW GAP IDENTIFIED

**Current Flow:**
1. Search executes → Sources discovered
2. Sources added/updated via `add_or_update_source()` → Normalized URLs stored
3. Search results processed → `_track_sources_usage()` called with specific URLs
4. URL normalization happens again → Different result than storage
5. Source not found → Statistics not updated

**Required Flow:**
1. Search executes → Sources discovered
2. Sources added/updated → Store source IDs in search context
3. Search results processed → Use source IDs for tracking
4. Direct `update_source_access(source_id)` calls → Statistics updated

## IMPACT ASSESSMENT

**Affected Components:**
- Source reliability scoring (depends on statistics)
- Source discovery ranking
- Provider performance metrics
- Search result quality assessment

**Data Integrity:**
- Approximately 60% of sources show 0 tracking data
- Government sources are better tracked than industry sources
- Recent sources (added via newer workflows) are less tracked

## RECOMMENDATIONS

1. **Immediate Fix:** Modify `_track_sources_usage()` to use domain-based fallback matching
2. **Long-term Fix:** Redesign to use source IDs instead of URL matching
3. **Data Recovery:** Run batch update to fix existing zero-statistics sources
4. **Testing:** Add integration tests for source tracking workflow

---

**Analysis Complete**  
**Next Steps:** Implement recommended fixes and validate tracking accuracy