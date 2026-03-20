from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_async_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.analytics_service import analytics_service
from app.schemas.analytics import (
    DashboardMetrics,
    FraudTrendsResponse,
    GeographicAnalysis,
    MerchantCategoryAnalysis
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive dashboard metrics.
    
    - **days**: Number of days to look back (max 365)
    - Returns total transactions, amounts, fraud rates, alerts, and model metrics
    """
    try:
        metrics = await analytics_service.get_dashboard_metrics(
            db, current_user.id, days
        )
        return DashboardMetrics(**metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve dashboard metrics: {str(e)}")


@router.get("/trends", response_model=FraudTrendsResponse)
async def get_fraud_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    period: str = Query("daily", description="Aggregation period: daily, weekly, or monthly"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get fraud trends over time.
    
    - **days**: Number of days to look back (max 365)
    - **period**: Aggregation period (daily, weekly, monthly)
    - Returns trend data with fraud rates over time
    """
    try:
        if period not in ["daily", "weekly", "monthly"]:
            raise HTTPException(status_code=400, detail="Period must be: daily, weekly, or monthly")
        
        trends = await analytics_service.get_fraud_trends(
            db, current_user.id, days, period
        )
        return FraudTrendsResponse(**trends)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve fraud trends: {str(e)}")


@router.get("/geographic", response_model=GeographicAnalysis)
async def get_geographic_analysis(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get fraud analysis by geographic location.
    
    - **days**: Number of days to look back (max 365)
    - Returns location-based fraud statistics and risk scores
    """
    try:
        analysis = await analytics_service.get_geographic_analysis(
            db, current_user.id, days
        )
        return GeographicAnalysis(**analysis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve geographic analysis: {str(e)}")


@router.get("/merchant-categories", response_model=list[MerchantCategoryAnalysis])
async def get_merchant_category_analysis(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get fraud analysis by merchant category.
    
    - **days**: Number of days to look back (max 365)
    - Returns category-based fraud statistics and risk scores
    """
    try:
        analysis = await analytics_service.get_merchant_category_analysis(
            db, current_user.id, days
        )
        return [MerchantCategoryAnalysis(**item) for item in analysis]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve merchant category analysis: {str(e)}")

