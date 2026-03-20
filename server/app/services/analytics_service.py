from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime, timedelta, date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.orm import selectinload

from app.models.transaction import Transaction
from app.models.prediction import Prediction
from app.models.fraud_alert import FraudAlert, AlertLevel
from app.models.card import Card
from app.models.user import User
from app.redis_client import redis_client
import json


class AnalyticsService:
    """Business logic for analytics and dashboard metrics."""
    
    async def get_dashboard_metrics(
        self,
        db: AsyncSession,
        user_id: UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get comprehensive dashboard metrics for a user.
        
        Args:
            db: Database session
            user_id: User ID
            days: Number of days to look back
            
        Returns:
            Dictionary with dashboard metrics
        """
        cache_key = f"dashboard_metrics:{user_id}:{days}"
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached) if isinstance(cached, str) else cached
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total transactions
        total_query = select(func.count(Transaction.id)).join(
            Card, Transaction.card_id == Card.id
        ).where(and_(Card.user_id == user_id, Transaction.transaction_date >= start_date))
        total_result = await db.execute(total_query)
        total_transactions = total_result.scalar() or 0
        
        # Total amount
        amount_query = select(func.sum(Transaction.amount)).join(
            Card, Transaction.card_id == Card.id
        ).where(and_(Card.user_id == user_id, Transaction.transaction_date >= start_date))
        amount_result = await db.execute(amount_query)
        total_amount = float(amount_result.scalar() or 0)
        
        # Fraud count
        fraud_query = select(func.count(Transaction.id)).join(
            Card, Transaction.card_id == Card.id
        ).where(
            and_(
                Card.user_id == user_id,
                Transaction.transaction_date >= start_date,
                Transaction.is_fraud == True
            )
        )
        fraud_result = await db.execute(fraud_query)
        fraud_count = fraud_result.scalar() or 0
        
        # Average transaction amount
        avg_query = select(func.avg(Transaction.amount)).join(
            Card, Transaction.card_id == Card.id
        ).where(and_(Card.user_id == user_id, Transaction.transaction_date >= start_date))
        avg_result = await db.execute(avg_query)
        avg_amount = float(avg_result.scalar() or 0)
        
        # High risk alerts
        alerts_query = select(func.count(FraudAlert.id)).join(
            Transaction, FraudAlert.transaction_id == Transaction.id
        ).join(
            Card, Transaction.card_id == Card.id
        ).where(
            and_(
                Card.user_id == user_id,
                FraudAlert.created_at >= start_date,
                FraudAlert.alert_level.in_([AlertLevel.HIGH, AlertLevel.CRITICAL])
            )
        )
        alerts_result = await db.execute(alerts_query)
        high_risk_alerts = alerts_result.scalar() or 0
        
        # Active cards
        cards_query = select(func.count(Card.id)).where(
            and_(Card.user_id == user_id, Card.is_active == True)
        )
        cards_result = await db.execute(cards_query)
        active_cards = cards_result.scalar() or 0
        
        # Model metrics (from predictions)
        predictions_query = select(
            func.avg(Prediction.fraud_probability),
            func.avg(Prediction.processing_time_ms),
            func.count(Prediction.id)
        ).join(
            Transaction, Prediction.transaction_id == Transaction.id
        ).join(
            Card, Transaction.card_id == Card.id
        ).where(
            and_(
                Card.user_id == user_id,
                Prediction.created_at >= start_date
            )
        )
        pred_result = await db.execute(predictions_query)
        pred_row = pred_result.first()
        avg_fraud_prob = float(pred_row[0] or 0) if pred_row else 0.0
        avg_pred_time = float(pred_row[1] or 0) if pred_row else 0.0
        total_predictions = pred_row[2] or 0
        
        # Model accuracy (simplified - would need feedback data)
        model_accuracy = 0.95  # Placeholder - would calculate from feedback
        
        metrics = {
            "total_transactions": total_transactions,
            "total_amount": Decimal(str(total_amount)),
            "fraud_count": fraud_count,
            "fraud_rate": (fraud_count / total_transactions * 100) if total_transactions > 0 else 0.0,
            "avg_transaction_amount": Decimal(str(avg_amount)),
            "high_risk_alerts": high_risk_alerts,
            "active_cards": active_cards,
            "active_users": 1,  # Per-user dashboard
            "model_accuracy": model_accuracy,
            "avg_prediction_time_ms": avg_pred_time,
            "date_range_start": start_date.date(),
            "date_range_end": datetime.utcnow().date()
        }
        
        # Cache for 5 minutes
        await redis_client.set(cache_key, json.dumps(metrics, default=str), expire=300)
        
        return metrics
    
    async def get_fraud_trends(
        self,
        db: AsyncSession,
        user_id: UUID,
        days: int = 30,
        period: str = "daily"
    ) -> Dict[str, Any]:
        """
        Get fraud trends over time.
        
        Args:
            db: Database session
            user_id: User ID
            days: Number of days to look back
            period: Aggregation period (daily, weekly, monthly)
            
        Returns:
            Dictionary with trend data
        """
        cache_key = f"fraud_trends:{user_id}:{days}:{period}"
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached) if isinstance(cached, str) else cached
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Build date truncation based on period
        if period == "daily":
            date_trunc = func.date_trunc('day', Transaction.transaction_date)
        elif period == "weekly":
            date_trunc = func.date_trunc('week', Transaction.transaction_date)
        elif period == "monthly":
            date_trunc = func.date_trunc('month', Transaction.transaction_date)
        else:
            date_trunc = func.date_trunc('day', Transaction.transaction_date)
        
        # Query transactions grouped by period
        trends_query = select(
            date_trunc.label('period_date'),
            func.count(Transaction.id).label('total_transactions'),
            func.sum(case((Transaction.is_fraud == True, 1), else_=0)).label('fraud_transactions'),
            func.sum(Transaction.amount).label('total_amount'),
            func.sum(case((Transaction.is_fraud == True, Transaction.amount), else_=0)).label('fraud_amount')
        ).join(
            Card, Transaction.card_id == Card.id
        ).where(
            and_(
                Card.user_id == user_id,
                Transaction.transaction_date >= start_date
            )
        ).group_by(date_trunc).order_by(date_trunc)
        
        result = await db.execute(trends_query)
        rows = result.all()
        
        trends = []
        for row in rows:
            period_date = row.period_date.date() if hasattr(row.period_date, 'date') else row.period_date
            if isinstance(period_date, str):
                period_date = datetime.fromisoformat(period_date).date()
            total_tx = row.total_transactions or 0
            fraud_tx = int(row.fraud_transactions or 0)
            total_amt = Decimal(str(row.total_amount or 0))
            fraud_amt = Decimal(str(row.fraud_amount or 0))
            
            trends.append({
                "date": period_date,
                "total_transactions": total_tx,
                "fraud_transactions": fraud_tx,
                "fraud_rate": (fraud_tx / total_tx * 100) if total_tx > 0 else 0.0,
                "total_amount": total_amt,
                "fraud_amount": fraud_amt
            })
        
        # Summary statistics
        total_all = sum(t["total_transactions"] for t in trends)
        fraud_all = sum(t["fraud_transactions"] for t in trends)
        
        response = {
            "trends": trends,
            "period": period,
            "start_date": start_date.date(),
            "end_date": datetime.utcnow().date(),
            "summary": {
                "total_transactions": total_all,
                "total_fraud": fraud_all,
                "overall_fraud_rate": (fraud_all / total_all * 100) if total_all > 0 else 0.0
            }
        }
        
        # Cache for 10 minutes
        await redis_client.set(cache_key, json.dumps(response, default=str), expire=600)
        
        return response
    
    async def get_geographic_analysis(
        self,
        db: AsyncSession,
        user_id: UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get fraud analysis by geographic location."""
        cache_key = f"geo_analysis:{user_id}:{days}"
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached) if isinstance(cached, str) else cached
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        geo_query = select(
            Transaction.location,
            func.count(Transaction.id).label('transaction_count'),
            func.sum(case((Transaction.is_fraud == True, 1), else_=0)).label('fraud_count'),
            func.sum(Transaction.amount).label('total_amount')
        ).join(
            Card, Transaction.card_id == Card.id
        ).where(
            and_(
                Card.user_id == user_id,
                Transaction.transaction_date >= start_date,
                Transaction.location.isnot(None)
            )
        ).group_by(Transaction.location).order_by(func.count(Transaction.id).desc())
        
        result = await db.execute(geo_query)
        rows = result.all()
        
        data = []
        high_risk_locations = []
        
        for row in rows:
            location = row.location or "Unknown"
            tx_count = row.transaction_count or 0
            fraud_count = int(row.fraud_count or 0)
            total_amt = Decimal(str(row.total_amount or 0))
            fraud_rate = (fraud_count / tx_count * 100) if tx_count > 0 else 0.0
            
            # Simple risk score based on fraud rate
            risk_score = min(100.0, fraud_rate * 2)
            
            data.append({
                "location": location,
                "transaction_count": tx_count,
                "fraud_count": fraud_count,
                "fraud_rate": fraud_rate,
                "total_amount": total_amt,
                "risk_score": risk_score
            })
            
            if fraud_rate > 10.0:  # High risk threshold
                high_risk_locations.append(location)
        
        response = {
            "data": data,
            "total_locations": len(data),
            "high_risk_locations": high_risk_locations,
            "analysis_date": datetime.utcnow().isoformat()
        }
        
        # Cache for 15 minutes
        await redis_client.set(cache_key, json.dumps(response, default=str), expire=900)
        
        return response
    
    async def get_merchant_category_analysis(
        self,
        db: AsyncSession,
        user_id: UUID,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get fraud analysis by merchant category."""
        cache_key = f"merchant_analysis:{user_id}:{days}"
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached) if isinstance(cached, str) else cached
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        category_query = select(
            Transaction.merchant_category,
            func.count(Transaction.id).label('transaction_count'),
            func.sum(case((Transaction.is_fraud == True, 1), else_=0)).label('fraud_count'),
            func.avg(Transaction.amount).label('avg_amount')
        ).join(
            Card, Transaction.card_id == Card.id
        ).where(
            and_(
                Card.user_id == user_id,
                Transaction.transaction_date >= start_date,
                Transaction.merchant_category.isnot(None)
            )
        ).group_by(Transaction.merchant_category).order_by(func.count(Transaction.id).desc())
        
        result = await db.execute(category_query)
        rows = result.all()
        
        analysis = []
        for row in rows:
            category = row.merchant_category or "Unknown"
            tx_count = row.transaction_count or 0
            fraud_count = int(row.fraud_count or 0)
            avg_amt = Decimal(str(row.avg_amount or 0))
            fraud_rate = (fraud_count / tx_count * 100) if tx_count > 0 else 0.0
            
            # Risk score based on fraud rate and transaction volume
            risk_score = min(100.0, fraud_rate * 1.5 + (tx_count / 100))
            
            analysis.append({
                "category": category,
                "transaction_count": tx_count,
                "fraud_count": fraud_count,
                "fraud_rate": fraud_rate,
                "avg_amount": avg_amt,
                "risk_score": risk_score
            })
        
        # Cache for 15 minutes
        await redis_client.set(cache_key, json.dumps(analysis, default=str), expire=900)
        
        return analysis


# Global analytics service instance
analytics_service = AnalyticsService()

