-- SOURCE TRACKING PROBLEM DEMONSTRATION QUERIES
-- Database Analyzer Agent - 2025-07-23
-- Purpose: Demonstrate the exact URL normalization mismatch problem

-- QUERY 1: Show sources with mixed tracking statistics
-- This shows which sources are being tracked vs not tracked
SELECT 
    domain,
    SUBSTR(url, 1, 60) as short_url,
    total_searches,
    successful_searches,
    CASE 
        WHEN total_searches > 0 THEN 'TRACKED ✓'
        ELSE 'NOT_TRACKED ✗'
    END as tracking_status,
    source_type,
    reliability_score
FROM sources 
ORDER BY total_searches DESC, domain ASC
LIMIT 25;

-- QUERY 2: Count tracking vs non-tracking sources
-- Shows the scope of the problem
SELECT 
    CASE 
        WHEN total_searches > 0 THEN 'TRACKED'
        ELSE 'NOT_TRACKED'
    END as status,
    COUNT(*) as source_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM sources), 2) as percentage
FROM sources 
GROUP BY (total_searches > 0)
ORDER BY source_count DESC;

-- QUERY 3: Find potential URL normalization conflicts
-- Shows domains with multiple URL variants
SELECT 
    domain,
    COUNT(*) as url_variants,
    SUM(total_searches) as total_searches_all_variants,
    GROUP_CONCAT(SUBSTR(url, 1, 50) || ' (' || total_searches || ')', ' | ') as urls_with_counts
FROM sources 
GROUP BY domain 
HAVING COUNT(*) > 1
ORDER BY url_variants DESC, total_searches_all_variants DESC;

-- QUERY 4: Show zero-tracking sources by type
-- Identifies which source types are most affected
SELECT 
    source_type,
    COUNT(*) as zero_tracking_count,
    (SELECT COUNT(*) FROM sources s2 WHERE s2.source_type = s1.source_type) as total_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM sources s2 WHERE s2.source_type = s1.source_type), 2) as zero_percentage
FROM sources s1
WHERE total_searches = 0 
GROUP BY source_type
ORDER BY zero_tracking_count DESC;

-- QUERY 5: Recent search activity vs source tracking
-- Shows if recent searches are updating source statistics
SELECT 
    DATE(last_attempted_access) as access_date,
    COUNT(*) as sources_accessed,
    SUM(CASE WHEN total_searches > 0 THEN 1 ELSE 0 END) as sources_with_tracking,
    ROUND(SUM(CASE WHEN total_searches > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as tracking_success_rate
FROM sources 
WHERE last_attempted_access IS NOT NULL
GROUP BY DATE(last_attempted_access)
ORDER BY access_date DESC
LIMIT 10;

-- QUERY 6: Detailed problem demonstration
-- Shows specific examples of the URL mismatch problem
SELECT 
    'STORED_URL' as type,
    domain,
    url,
    total_searches,
    'Base URL in database' as note
FROM sources 
WHERE domain IN ('usgs.gov', 'mining.com', 'infomine.com')
UNION ALL
SELECT 
    'POTENTIAL_SEARCH_URL' as type,
    domain,
    url || '/specific-page' as url,
    0 as total_searches,
    'What search might look for' as note
FROM sources 
WHERE domain IN ('usgs.gov', 'mining.com', 'infomine.com')
ORDER BY domain, type;

-- QUERY 7: Success rate analysis by domain reliability
-- Shows correlation between tracking and reliability scores
SELECT 
    CASE 
        WHEN reliability_score >= 80 THEN 'HIGH (80+)'
        WHEN reliability_score >= 60 THEN 'MEDIUM (60-79)'
        WHEN reliability_score >= 40 THEN 'LOW (40-59)'
        ELSE 'VERY_LOW (<40)'
    END as reliability_category,
    COUNT(*) as source_count,
    SUM(CASE WHEN total_searches > 0 THEN 1 ELSE 0 END) as tracked_sources,
    ROUND(SUM(CASE WHEN total_searches > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as tracking_percentage,
    ROUND(AVG(total_searches), 2) as avg_searches,
    ROUND(AVG(successful_searches), 2) as avg_successful
FROM sources 
GROUP BY 
    CASE 
        WHEN reliability_score >= 80 THEN 'HIGH (80+)'
        WHEN reliability_score >= 60 THEN 'MEDIUM (60-79)'
        WHEN reliability_score >= 40 THEN 'LOW (40-59)'
        ELSE 'VERY_LOW (<40)'
    END
ORDER BY 
    CASE 
        WHEN reliability_score >= 80 THEN 1
        WHEN reliability_score >= 60 THEN 2
        WHEN reliability_score >= 40 THEN 3
        ELSE 4
    END;

-- QUERY 8: Timeline analysis - when did tracking start failing?
-- Shows temporal pattern of the tracking issue
SELECT 
    DATE(created_at) as creation_date,
    COUNT(*) as sources_created,
    SUM(CASE WHEN total_searches > 0 THEN 1 ELSE 0 END) as sources_tracked,
    ROUND(SUM(CASE WHEN total_searches > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as tracking_rate
FROM sources 
WHERE created_at IS NOT NULL
GROUP BY DATE(created_at)
ORDER BY creation_date DESC
LIMIT 15;