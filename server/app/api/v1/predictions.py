import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.prediction import Prediction
from app.schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
    PredictionHistory,
    PredictionFeedbackRequest,
    PredictionStatisticsResponse
)
from app.services.prediction_service import prediction_service
from app.ml.inference import prediction_engine, PredictionResult

# Expose all prediction endpoints under /api/v1/predictions/* to match frontend
router = APIRouter(prefix="/predictions", tags=["Predictions"])


def _parse_timestamp(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.utcnow()


@router.post("/predict", response_model=PredictionResponse, status_code=201)
async def create_prediction(
    request: PredictionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a fraud prediction for a single transaction.
    
    - **transaction_id**: ID of the transaction to analyze
    - Returns comprehensive prediction results with risk assessment
    """
    try:
        # Validate transaction ID format
        try:
            transaction_id = uuid.UUID(request.transaction_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid transaction ID format")
        
        # Create prediction
        prediction_result, prediction_record, fraud_alert = await prediction_service.create_prediction(
            db, transaction_id, current_user.id
        )
        
        # Add background task for additional processing if needed
        if fraud_alert:
            background_tasks.add_task(
                send_fraud_alert_notification,
                current_user.id,
                fraud_alert.id
            )
        
        return PredictionResponse(
            prediction_id=str(prediction_record.id),
            transaction_id=str(prediction_record.transaction_id),
            is_fraud=prediction_result.is_fraud,
            fraud_probability=prediction_result.fraud_probability,
            confidence_score=prediction_result.confidence_score or 0.0,
            risk_level=prediction_result.risk_level.value,
            model_version=prediction_result.model_version,
            processing_time_ms=prediction_result.processing_time_ms,
            timestamp=_parse_timestamp(prediction_result.timestamp),
            fraud_alert_id=str(fraud_alert.id) if fraud_alert else None,
            feature_importance=prediction_result.feature_importance,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/batch", response_model=BatchPredictionResponse, status_code=201)
async def create_batch_predictions(
    request: BatchPredictionRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create fraud predictions for multiple transactions.
    
    - **transaction_ids**: List of transaction IDs (max 1000)
    - Returns prediction results for all transactions
    """
    try:
        # Validate batch size
        if len(request.transaction_ids) > 1000:
            raise HTTPException(status_code=400, detail="Batch size cannot exceed 1000 transactions")
        
        if len(request.transaction_ids) == 0:
            raise HTTPException(status_code=400, detail="Transaction IDs list cannot be empty")
        
        # Validate and convert transaction IDs
        transaction_ids = []
        for tid in request.transaction_ids:
            try:
                transaction_ids.append(uuid.UUID(tid))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid transaction ID format: {tid}")
        
        # Create batch predictions
        results = await prediction_service.batch_predict(db, transaction_ids, current_user.id)
        
        # Format response
        predictions = []
        fraud_alerts = []
        
        for pred_result, pred_record, fraud_alert, txn_id in results:
            predictions.append(PredictionResponse(
                prediction_id=str(pred_record.id) if pred_record else pred_result.prediction_id,
                transaction_id=str(pred_record.transaction_id) if pred_record else str(txn_id),
                is_fraud=pred_result.is_fraud,
                fraud_probability=pred_result.fraud_probability,
                confidence_score=pred_result.confidence_score or 0.0,
                risk_level=pred_result.risk_level.value,
                model_version=pred_result.model_version,
                processing_time_ms=pred_result.processing_time_ms,
                timestamp=_parse_timestamp(pred_result.timestamp),
                    fraud_alert_id=str(fraud_alert.id) if fraud_alert else None,
                    feature_importance=pred_result.feature_importance,
            ))
            
            if fraud_alert:
                fraud_alerts.append(str(fraud_alert.id))
        
        return BatchPredictionResponse(
            predictions=predictions,
            total_requested=len(transaction_ids),
            total_processed=len(predictions),
            fraud_alerts_created=len(fraud_alerts),
            fraud_alert_ids=fraud_alerts
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")


@router.get("/history", response_model=PredictionHistory)
async def get_prediction_history(
    limit: int = Query(50, ge=1, le=1000, description="Number of predictions to return"),
    offset: int = Query(0, ge=0, description="Number of predictions to skip"),
    start_date: Optional[datetime] = Query(None, description="Filter predictions from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter predictions until this date"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level (low, medium, high, critical)"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get prediction history for the current user.
    
    - **limit**: Number of predictions to return (max 1000)
    - **offset**: Number of predictions to skip for pagination
    - **start_date**: Filter predictions from this date
    - **end_date**: Filter predictions until this date  
    - **risk_level**: Filter by risk level
    """
    try:
        # Validate risk level if provided
        if risk_level and risk_level not in ['low', 'medium', 'high', 'critical']:
            raise HTTPException(status_code=400, detail="Invalid risk level. Must be: low, medium, high, or critical")
        
        # Get prediction history
        predictions, total_count = await prediction_service.get_prediction_history(
            db, current_user.id, limit, offset, start_date, end_date, risk_level
        )
        
        # Format predictions
        formatted_predictions = []
        for pred in predictions:
            formatted_predictions.append(PredictionResponse(
                prediction_id=str(pred.id),
                transaction_id=str(pred.transaction_id),
                is_fraud=pred.prediction_class is True,
                fraud_probability=pred.fraud_probability,
                confidence_score=pred.confidence_score or 0.0,
                risk_level=pred.risk_level or "low",
                model_version=pred.model_version,
                processing_time_ms=pred.processing_time_ms,
                timestamp=pred.created_at,
                fraud_alert_id=None,  # Not joining with fraud_alerts for performance
                feature_importance=pred.feature_importance,
            ))
        
        return PredictionHistory(
            predictions=formatted_predictions,
            total_count=total_count,
            limit=limit,
            offset=offset,
            has_more=offset + limit < total_count
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve prediction history: {str(e)}")


@router.put("/{prediction_id}/feedback", response_model=PredictionResponse)
async def update_prediction_feedback(
    prediction_id: str,
    feedback: PredictionFeedbackRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update feedback for a prediction to improve model accuracy.
    
    - **prediction_id**: ID of the prediction to update
    - **is_correct_fraud**: Whether the fraud prediction was correct
    - **feedback_notes**: Additional feedback notes
    """
    try:
        # Validate prediction ID format
        try:
            pred_uuid = uuid.UUID(prediction_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid prediction ID format")
        
        # Update feedback
        updated_prediction = await prediction_service.update_prediction_feedback(
            db, pred_uuid, current_user.id, feedback.is_correct_fraud, feedback.feedback_notes
        )
        
        if not updated_prediction:
            raise HTTPException(status_code=404, detail="Prediction not found or access denied")
        
        return PredictionResponse(
            prediction_id=str(updated_prediction.id),
            transaction_id=str(updated_prediction.transaction_id),
            is_fraud=updated_prediction.prediction_class is True,
            fraud_probability=updated_prediction.fraud_probability,
            confidence_score=updated_prediction.confidence_score or 0.0,
            risk_level=updated_prediction.risk_level or "low",
            model_version=updated_prediction.model_version,
            processing_time_ms=updated_prediction.processing_time_ms,
            timestamp=updated_prediction.created_at,
            fraud_alert_id=None,
            feature_importance=updated_prediction.feature_importance,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update prediction feedback: {str(e)}")


@router.get("/statistics", response_model=PredictionStatisticsResponse)
async def get_prediction_statistics(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get prediction statistics for the current user.
    
    - **days**: Number of days to look back (max 365)
    """
    try:
        # Get statistics
        stats = await prediction_service.get_prediction_statistics(db, current_user.id, days)
        
        return PredictionStatisticsResponse(
            period_days=stats["period_days"],
            total_predictions=stats["total_predictions"],
            fraud_predictions=stats["fraud_predictions"],
            fraud_rate=stats["fraud_rate"],
            high_risk_predictions=stats["high_risk_predictions"],
            high_risk_rate=stats["high_risk_rate"],
            risk_level_breakdown=stats["risk_level_breakdown"],
            average_confidence=stats["average_confidence"],
            start_date=stats["start_date"],
            end_date=stats["end_date"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve prediction statistics: {str(e)}")


@router.get("/model/info")
async def get_model_info(current_user: User = Depends(get_current_user)):
    """
    Get information about the fraud detection model.
    """
    try:
        model_info = await prediction_engine.get_model_info()
        return model_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve model information: {str(e)}")


async def send_fraud_alert_notification(user_id: uuid.UUID, alert_id: uuid.UUID):
    """
    Background task to send fraud alert notifications.
    
    This would typically integrate with:
    - Email service
    - SMS service  
    - Push notifications
    - WebSocket real-time alerts
    """
    # TODO: Implement notification integration
    print(f"Fraud alert notification for user {user_id}, alert {alert_id}")
    pass
