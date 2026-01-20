from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status

from application.background_tasks.quote_miner import QuoteMiner

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/update-quotes", status_code=status.HTTP_202_ACCEPTED)
async def trigger_quote_update():
    """Запустить немедленное обновление цитат из внешних источников"""
    miner = QuoteMiner()
    try:
        results = await miner.update_now()
        return {
            "message": "Quote update triggered",
            "results": results
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update quotes: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "service": "quote-api",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }