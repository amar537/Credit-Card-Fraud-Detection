import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models.transaction import Transaction
from app.models.prediction import Prediction, PredictionFeedback
from app.models.fraud_alert import FraudAlert, AlertLevel
from app.models.card import Card
from app.models.user import User
from app.ml.inference import prediction_engine, PredictionResult, RiskLevel


class PredictionService:
    """Business logic for fraud predictions and database integration."""
    
    def __init__(self):
        self.engine = prediction_engine
    
    async def create_prediction(
        self,
        db: AsyncSession,
        transaction_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Tuple[PredictionResult, Prediction, Optional[FraudAlert]]:
        """
        Create a prediction for a transaction and save to database.
        
        Args:
            db: Database session
            transaction_id: Transaction ID
            user_id: User ID making the request
            
        Returns:
            Tuple of (PredictionResult, Prediction record, optional FraudAlert)
        """
        # 1. Fetch transaction from database with authorization
        transaction = await self._get_transaction_with_auth(db, transaction_id, user_id)
        if not transaction:
            raise ValueError("Transaction not found or access denied")
        
        # 2. Check Redis cache (5 min TTL)
        cached_result = await self.engine._check_cache(str(transaction_id))
        if cached_result:
            # Load existing prediction from database
            existing_prediction = await self._get_prediction_by_transaction(db, transaction_id)
            if existing_prediction:
                return cached_result, existing_prediction, None
        
        # 3. Run ML model prediction
        transaction_data = self._transaction_to_dict(transaction)
        prediction_result = await self.engine.predict_single(transaction_data)
        
        # 4. Save Prediction record
        prediction_record = await self._save_prediction(db, transaction_id, prediction_result)
        
        # 5. Update Transaction.is_fraud & fraud_score
        await self._update_transaction_fraud_flags(db, transaction_id, prediction_result)
        
        # 6. Create FraudAlert if high/critical risk
        fraud_alert = None
        if prediction_result.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            fraud_alert = await self._create_fraud_alert(
                db, transaction, prediction_result, user_id
            )
        
        # 7. Cache result
        await self.engine._cache_result(str(transaction_id), prediction_result)
        
        # Commit all changes
        await db.commit()
        
        return prediction_result, prediction_record, fraud_alert
    
    async def get_prediction_history(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        risk_level: Optional[str] = None
    ) -> Tuple[List[Prediction], int]:
        """
        Get prediction history for a user with filtering.
        
        Args:
            db: Database session
            user_id: User ID
            limit: Number of records to return
            offset: Offset for pagination
            start_date: Filter start date
            end_date: Filter end date
            risk_level: Filter by risk level
            
        Returns:
            Tuple of (predictions list, total count)
        """
        # Build base query with authorization (explicit join paths to avoid ambiguity)
        base_query = (
            select(Prediction)
            .join(Transaction, Prediction.transaction_id == Transaction.id)
            .join(Card, Transaction.card_id == Card.id)
            .join(User, Card.user_id == User.id)
            .where(User.id == user_id)
        )
        
        # Apply filters
        if start_date:
            base_query = base_query.where(Prediction.created_at >= start_date)
        if end_date:
            base_query = base_query.where(Prediction.created_at <= end_date)
        if risk_level:
            base_query = base_query.where(Prediction.risk_level == risk_level)
        
        # Get total count (use scalar() to avoid NoResultFound and fallback to 0)
        count_query = base_query.with_only_columns(func.count(Prediction.id)).order_by(None)
        count_result = await db.execute(count_query)
        total_count = count_result.scalar() or 0
        
        # Get paginated results
        query = base_query.order_by(Prediction.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        predictions = result.scalars().all()
        
        return list(predictions), total_count
    
    async def update_prediction_feedback(
        self,
        db: AsyncSession,
        prediction_id: uuid.UUID,
        user_id: uuid.UUID,
        is_correct_fraud: Optional[bool] = None,
        feedback_notes: Optional[str] = None
    ) -> Optional[Prediction]:
        """
        Update feedback for a prediction to improve model.
        
        Args:
            db: Database session
            prediction_id: Prediction ID
            user_id: User ID for authorization
            is_correct_fraud: Whether the fraud prediction was correct
            feedback_notes: Additional feedback notes
            
        Returns:
            Updated prediction record or None if not found
        """
        # Get prediction with authorization
        query = select(Prediction).join(Transaction).join(Card).join(User).where(
            and_(Prediction.id == prediction_id, User.id == user_id)
        )
        result = await db.execute(query)
        prediction = result.scalar_one_or_none()
        
        if not prediction:
            return None
        
        # Update feedback
        if is_correct_fraud is not None:
            prediction.feedback = (
                PredictionFeedback.CORRECT
                if is_correct_fraud
                else PredictionFeedback.INCORRECT
            )
        if feedback_notes is not None:
            prediction.feedback_notes = feedback_notes
        if is_correct_fraud is not None or feedback_notes is not None:
            prediction.reviewed_by = user_id
            prediction.reviewed_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(prediction)
        
        return prediction
    
    async def batch_predict(
        self,
        db: AsyncSession,
        transaction_ids: List[uuid.UUID],
        user_id: uuid.UUID
    ) -> List[Tuple[PredictionResult, Optional[Prediction], Optional[FraudAlert], uuid.UUID]]:
        """
        Batch predictions for multiple transactions.
        
        Args:
            db: Database session
            transaction_ids: List of transaction IDs
            user_id: User ID for authorization
            
        Returns:
            List of prediction results tuples
        """
        results = []
        
        # Process in batches to avoid overwhelming the system
        batch_size = 50
        for i in range(0, len(transaction_ids), batch_size):
            batch_ids = transaction_ids[i:i + batch_size]
            
            # Get transactions with authorization
            transactions = await self._get_transactions_with_auth(db, batch_ids, user_id)
            
            # Prepare transaction data for batch prediction
            transactions_data = [self._transaction_to_dict(t) for t in transactions]
            prediction_results = await self.engine.predict_batch(transactions_data)
            
            # Process each prediction result
            for j, (transaction, pred_result) in enumerate(zip(transactions, prediction_results)):
                try:
                    # Save prediction record
                    prediction_record = await self._save_prediction(db, transaction.id, pred_result)
                    
                    # Update transaction
                    await self._update_transaction_fraud_flags(db, transaction.id, pred_result)
                    
                    # Create alert if needed
                    fraud_alert = None
                    if pred_result.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                        fraud_alert = await self._create_fraud_alert(
                            db, transaction, pred_result, user_id
                        )
                    
                    # Cache result
                    await self.engine._cache_result(str(transaction.id), pred_result)
                    
                    results.append((pred_result, prediction_record, fraud_alert, transaction.id))
                    
                except Exception as e:
                    # Log error but continue processing other transactions
                    print(f"Error processing prediction for transaction {transaction.id}: {e}")
                    results.append((pred_result, None, None, transaction.id))
            
            # Commit batch
            await db.commit()
        
        return results
    
    async def get_prediction_statistics(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        days: int = 30
    ) -> Dict:
        """
        Get prediction statistics for the user.
        
        Args:
            db: Database session
            user_id: User ID
            days: Number of days to look back
            
        Returns:
            Dictionary with statistics
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get predictions for the period
        query = select(Prediction).join(Transaction).join(Card).join(User).where(
            and_(
                User.id == user_id,
                Prediction.created_at >= start_date
            )
        )
        result = await db.execute(query)
        predictions = result.scalars().all()
        
        # Calculate statistics
        total_predictions = len(predictions)
        fraud_predictions = sum(1 for p in predictions if p.prediction_class is True)
        high_risk_predictions = sum(1 for p in predictions if p.risk_level in ['high', 'critical'])
        
        # Risk level breakdown
        risk_counts = {}
        for p in predictions:
            key = p.risk_level or "unknown"
            risk_counts[key] = risk_counts.get(key, 0) + 1
        
        # Average confidence
        avg_confidence = (
            sum(p.confidence_score or 0 for p in predictions) / total_predictions
            if total_predictions > 0
            else 0
        )
        
        return {
            "period_days": days,
            "total_predictions": total_predictions,
            "fraud_predictions": fraud_predictions,
            "fraud_rate": fraud_predictions / total_predictions if total_predictions > 0 else 0,
            "high_risk_predictions": high_risk_predictions,
            "high_risk_rate": high_risk_predictions / total_predictions if total_predictions > 0 else 0,
            "risk_level_breakdown": risk_counts,
            "average_confidence": avg_confidence,
            "start_date": start_date,
            "end_date": datetime.utcnow()
        }
    
    # Private helper methods
    
    async def _get_transaction_with_auth(
        self,
        db: AsyncSession,
        transaction_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Optional[Transaction]:
        """Get transaction with authorization check."""
        query = select(Transaction).join(Card).join(User).where(
            and_(Transaction.id == transaction_id, User.id == user_id)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_transactions_with_auth(
        self,
        db: AsyncSession,
        transaction_ids: List[uuid.UUID],
        user_id: uuid.UUID
    ) -> List[Transaction]:
        """Get multiple transactions with authorization check."""
        query = select(Transaction).join(Card).join(User).where(
            and_(Transaction.id.in_(transaction_ids), User.id == user_id)
        )
        result = await db.execute(query)
        return list(result.scalars().all())
    
    def _transaction_to_dict(self, transaction: Transaction) -> Dict:
        """Convert transaction to dictionary for ML model."""
        txn_type = getattr(transaction.transaction_type, "value", None)
        return {
            "id": str(getattr(transaction, "id", "")),
            "card_id": str(getattr(transaction, "card_id", "")),
            "amount": float(getattr(transaction, "amount", 0.0) or 0.0),
            "merchant_name": getattr(transaction, "merchant_name", None) or "Unknown",
            "merchant_category": getattr(transaction, "merchant_category", None) or "unknown",
            "transaction_date": (getattr(transaction, "transaction_date", None) or datetime.utcnow()).isoformat(),
            "transaction_type": txn_type or (getattr(transaction, "transaction_type", None) or "unknown"),
            "location": getattr(transaction, "location", None) or "unknown",
            "ip_address": str(getattr(transaction, "ip_address", None)) if getattr(transaction, "ip_address", None) else None,
            "device_info": getattr(transaction, "device_info", None),
        }
    
    async def _get_prediction_by_transaction(
        self,
        db: AsyncSession,
        transaction_id: uuid.UUID
    ) -> Optional[Prediction]:
        """Get existing prediction by transaction ID."""
        query = select(Prediction).where(Prediction.transaction_id == transaction_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def _save_prediction(
        self,
        db: AsyncSession,
        transaction_id: uuid.UUID,
        prediction_result: PredictionResult
    ) -> Prediction:
        """Save prediction record to database."""
        prediction = Prediction(
            id=uuid.uuid4(),
            transaction_id=transaction_id,
            model_version=prediction_result.model_version,
            fraud_probability=prediction_result.fraud_probability,
            prediction_class=prediction_result.is_fraud,
            confidence_score=prediction_result.confidence_score,
            risk_level=prediction_result.risk_level.value,
            processing_time_ms=int(prediction_result.processing_time_ms),
            feature_importance=prediction_result.feature_importance,
        )
        
        db.add(prediction)
        await db.flush()
        await db.refresh(prediction)
        
        return prediction
    
    async def _update_transaction_fraud_flags(
        self,
        db: AsyncSession,
        transaction_id: uuid.UUID,
        prediction_result: PredictionResult
    ):
        """Update transaction with fraud prediction results."""
        query = select(Transaction).where(Transaction.id == transaction_id)
        result = await db.execute(query)
        transaction = result.scalar_one_or_none()
        
        if transaction:
            transaction.is_fraud = prediction_result.is_fraud
            transaction.fraud_score = prediction_result.fraud_probability
            transaction.updated_at = datetime.utcnow()
    
    async def _create_fraud_alert(
        self,
        db: AsyncSession,
        transaction: Transaction,
        prediction_result: PredictionResult,
        user_id: uuid.UUID
    ) -> FraudAlert:
        """Create fraud alert for high-risk transactions."""
        severity = (
            AlertLevel.CRITICAL
            if prediction_result.risk_level == RiskLevel.CRITICAL
            else AlertLevel.HIGH
        )
        
        alert = FraudAlert(
            id=uuid.uuid4(),
            transaction_id=transaction.id,
            alert_level=severity,
            alert_message=(
                f"Transaction of ${transaction.amount} at {transaction.merchant_name} "
                f"flagged as {prediction_result.risk_level.value} risk "
                f"(score: {prediction_result.fraud_probability:.2%})"
            ),
        )
        
        db.add(alert)
        await db.flush()
        await db.refresh(alert)
        
        return alert


# Global prediction service instance
prediction_service = PredictionService()
