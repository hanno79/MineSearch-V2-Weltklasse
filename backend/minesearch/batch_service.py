"""BatchService für CSV Upload und Batch-Verarbeitung."""

import csv
import io
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List
from fastapi import UploadFile, HTTPException

logger = logging.getLogger(__name__)

class BatchService:
    """Service für CSV Upload und Batch-Verarbeitung von Minen"""
    
    def __init__(self, cache: Dict, results_cache: Dict):
        self.cache = cache
        self.results_cache = results_cache
    
    async def process_csv_upload(self, csv_file: UploadFile) -> Dict[str, Any]:
        """Verarbeite CSV Upload und gib Session-ID zurück"""
        try:
            logger.info(f"Processing CSV upload: {csv_file.filename}")
            
            # Lese CSV Inhalt
            contents = await csv_file.read()
            csv_content = contents.decode('utf-8')
            
            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            mines = []
            columns = []
            
            for i, row in enumerate(csv_reader):
                if i == 0:
                    columns = list(row.keys())
                mines.append(row)
                
                # Limit für Demo
                if i >= 100:
                    break
            
            # Erstelle Session
            session_id = str(uuid.uuid4())
            
            # Speichere in Cache
            self.cache[session_id] = {
                'mines': mines,
                'columns': columns,
                'timestamp': datetime.now()
            }
            
            logger.info(f"CSV processed: {len(mines)} mines, session: {session_id}")
            
            return {
                "success": True,
                "session_id": session_id,
                "mine_count": len(mines),
                "columns": columns
            }
            
        except Exception as e:
            logger.error(f"Error processing CSV: {str(e)}")
            raise HTTPException(status_code=400, detail=f"CSV processing error: {str(e)}")

__all__ = ["BatchService"]


