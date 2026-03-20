from fastapi import APIRouter, Depends, Query, status, Response, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
from datetime import datetime
from io import BytesIO

from app.database import get_async_db
from app.core.dependencies import get_current_user
from app.services.transaction_service import TransactionService
from app.schemas.transaction import (
    TransactionResponse, TransactionCreate, TransactionUpdate, 
    TransactionFilters, TransactionListResponse
)
from app.schemas.user import UserResponse

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction: TransactionCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create a new transaction
    
    - Validates card ownership
    - Checks for duplicate transactions
    - Triggers fraud detection (implemented in next task)
    """
    service = TransactionService(db)
    return await service.create_transaction(transaction, current_user.id)


@router.get("/", response_model=TransactionListResponse)
async def get_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    is_fraud: Optional[bool] = None,
    merchant_category: Optional[str] = None,
    card_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get paginated and filtered transactions
    
    - Supports filtering by date, amount, fraud status, category
    - Results are cached for 5 minutes
    """
    filters = TransactionFilters(
        start_date=start_date,
        end_date=end_date,
        min_amount=min_amount,
        max_amount=max_amount,
        is_fraud=is_fraud,
        merchant_category=merchant_category,
        card_id=card_id
    )
    service = TransactionService(db)
    result = await service.get_transactions(current_user.id, filters, skip=skip, limit=limit)
    return result


@router.post("/import", status_code=status.HTTP_200_OK)
async def import_transactions_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Import transactions from a CSV file for the current user."""
    content = await file.read()
    service = TransactionService(db)
    result = await service.import_csv(current_user.id, content)
    return {"message": "Import completed", **result}


@router.post("/import/csv", status_code=status.HTTP_200_OK)
async def import_transactions_csv_alt(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Alternate path for importing transactions from CSV."""
    content = await file.read()
    service = TransactionService(db)
    result = await service.import_csv(current_user.id, content)
    return {"message": "Import completed", **result}


@router.post("/upload", status_code=status.HTTP_200_OK)
async def upload_transactions_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Alternate simple upload endpoint for CSV imports."""
    content = await file.read()
    service = TransactionService(db)
    result = await service.import_csv(current_user.id, content)
    return {"message": "Import completed", **result}

@router.post("/seed", status_code=status.HTTP_200_OK)
async def seed_demo_transactions(
    count: int = Query(25, ge=1, le=200),
    db: AsyncSession = Depends(get_async_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Seed demo data for the signed-in user (creates a card if missing)."""
    service = TransactionService(db)
    result = await service.seed_demo(current_user.id, count=count)
    return {"message": "Demo data created", **result}


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get transaction by ID with authorization check"""
    service = TransactionService(db)
    transaction = await service.get_transaction(transaction_id, current_user.id)
    return transaction


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: UUID,
    update_data: TransactionUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Update transaction (limited fields)"""
    service = TransactionService(db)
    transaction = await service.update_transaction(transaction_id, current_user.id, update_data)
    return transaction


@router.get("/stats/summary")
async def get_statistics(
    db: AsyncSession = Depends(get_async_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get transaction statistics
    
    Returns: Total transactions, amounts, fraud rate, category breakdown
    """
    service = TransactionService(db)
    return await service.get_statistics(current_user.id)


@router.get("/export/csv")
async def export_transactions_csv(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Export transactions as CSV"""
    filters = TransactionFilters(start_date=start_date, end_date=end_date)
    service = TransactionService(db)
    df = await service.export_transactions(current_user.id, filters)
    
    # Convert to CSV
    output = BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"}
    )
