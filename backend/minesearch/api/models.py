"""
Author: rahn
Datum: 04.07.2025
Version: 1.0
Beschreibung: Pydantic-Modelle für API Request/Response
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

# Request/Response Modelle
class MineSearchRequest(BaseModel):
    mine_name: str
    country: Optional[str] = None
    commodity: Optional[str] = None
    region: Optional[str] = None
    model: str  # CRITICAL FIX: Missing model field for single search

class MineSearchResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = datetime.now()
    search_query: Optional[str] = None

class MultiSearchRequest(BaseModel):
    mine_name: str
    country: Optional[str] = None
    commodity: Optional[str] = None
    region: Optional[str] = None
    model_ids: List[str]  # Liste der zu verwendenden Modelle

class SmartSearchRequest(BaseModel):
    mine_name: str
    country: Optional[str] = None
    commodity: Optional[str] = None
    region: Optional[str] = None

class SourceSearchRequest(BaseModel):
    mine_name: str
    country: Optional[str] = None
    region: Optional[str] = None