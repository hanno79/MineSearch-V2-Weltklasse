from fastapi import APIRouter

router = APIRouter()

class ModelBenchmarkService:
    """Dummy benchmark service class"""
    def __init__(self):
        pass
    
    def get_status(self):
        return {"status": "disabled"}

@router.get("/benchmark/status")
async def benchmark_status():
    return {"status": "disabled"}
