from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from decimal import Decimal
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, desc, func, select
from fastapi import HTTPException, status
import pandas as pd

from app.models.transaction import Transaction, TransactionType
from app.models.card import Card, CardType
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionFilters,
    TransactionResponse,
)
from app.redis_client import redis_client
import json


class TransactionService:
    """Business logic for transaction operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_transaction(
        self, 
        transaction_data: TransactionCreate,
        user_id: UUID
    ) -> Transaction:
        """Create a new transaction and trigger fraud detection"""
        
        # Verify card ownership
        card_stmt = select(Card).where(
            Card.id == transaction_data.card_id,
            Card.user_id == user_id,
        )
        card_result = await self.db.execute(card_stmt)
        card = card_result.scalar_one_or_none()
        
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found or unauthorized"
            )
        
        if card.is_blocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Card is blocked"
            )
        
        # Check for duplicate transactions (within 1 minute)
        duplicate_stmt = select(Transaction).where(
            Transaction.card_id == transaction_data.card_id,
            Transaction.amount == transaction_data.amount,
            Transaction.merchant_name == transaction_data.merchant_name,
            Transaction.created_at > datetime.utcnow() - timedelta(minutes=1),
        )
        duplicate_result = await self.db.execute(duplicate_stmt.limit(1))
        duplicate = duplicate_result.scalar_one_or_none()
        
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Duplicate transaction detected"
            )
        
        # Create transaction
        transaction = Transaction(**transaction_data.dict())
        self.db.add(transaction)
        await self.db.commit()
        await self.db.refresh(transaction)
        
        # Invalidate cache
        await self._invalidate_transaction_cache(user_id)
        
        return transaction
    
    async def get_transaction(
        self, 
        transaction_id: UUID,
        user_id: UUID
    ) -> Transaction:
        """Get single transaction with authorization check"""
        
        transaction_stmt = (
            select(Transaction)
            .join(Card)
            .where(Transaction.id == transaction_id, Card.user_id == user_id)
        )
        result = await self.db.execute(transaction_stmt)
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        return transaction
    
    async def get_transactions(
        self,
        user_id: UUID,
        filters: TransactionFilters,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get paginated and filtered transactions"""
        
        # Try cache first (v2 key to invalidate any old cached payloads)
        cache_key = f"transactions_v2:{user_id}:{skip}:{limit}:{hash(str(filters))}"
        cached_data = await redis_client.get(cache_key)

        # Cached value may already be a dict (if set by older code) or a JSON string.
        if cached_data:
            if isinstance(cached_data, (str, bytes)):
                return json.loads(cached_data)
            return cached_data
        
        filters_clause = [Card.user_id == user_id]
        
        if filters.start_date:
            filters_clause.append(Transaction.transaction_date >= filters.start_date)
        if filters.end_date:
            filters_clause.append(Transaction.transaction_date <= filters.end_date)
        if filters.min_amount:
            filters_clause.append(Transaction.amount >= filters.min_amount)
        if filters.max_amount:
            filters_clause.append(Transaction.amount <= filters.max_amount)
        if filters.is_fraud is not None:
            filters_clause.append(Transaction.is_fraud == filters.is_fraud)
        if filters.merchant_category:
            filters_clause.append(Transaction.merchant_category == filters.merchant_category)
        card_id = getattr(filters, "card_id", None)
        if card_id:
            filters_clause.append(Transaction.card_id == card_id)
        
        base_stmt = (
            select(Transaction)
            .join(Card)
            .where(*filters_clause)
            .order_by(desc(Transaction.transaction_date))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(base_stmt)
        orm_transactions = result.scalars().all()
        
        count_stmt = (
            select(func.count(Transaction.id))
            .join(Card)
            .where(*filters_clause)
        )
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Convert ORM objects to plain dicts via Pydantic so they are JSON-serializable
        transactions = [
            TransactionResponse.model_validate(t).model_dump(mode="json")
            for t in orm_transactions
        ]

        # Shape result to match TransactionListResponse schema
        page = (skip // limit) + 1 if limit > 0 else 1
        size = limit
        has_more = skip + len(transactions) < total

        result_payload = {
            "transactions": transactions,
            "total": total,
            "page": page,
            "size": size,
            "has_more": has_more,
        }

        # Cache for 5 minutes as proper JSON
        await redis_client.setex(
            cache_key,
            300,
            json.dumps(result_payload)
        )
        
        return result_payload
    
    async def update_transaction(
        self,
        transaction_id: UUID,
        user_id: UUID,
        update_data: TransactionUpdate
    ) -> Transaction:
        """Update transaction (limited fields)"""
        
        transaction = await self.get_transaction(transaction_id, user_id)
        
        # Only allow updating specific fields
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(transaction, field, value)
        
        await self.db.commit()
        await self.db.refresh(transaction)
        
        return transaction
    
    async def get_statistics(self, user_id: UUID) -> Dict[str, Any]:
        """Get transaction statistics"""
        
        cache_key = f"transaction_stats:{user_id}"
        cached = await redis_client.get(cache_key)
        
        if cached:
            return json.loads(cached)
        
        # Total transactions
        total_stmt = (
            select(func.count(Transaction.id))
            .join(Card)
            .where(Card.user_id == user_id)
        )
        res = await self.db.execute(total_stmt)
        total_transactions = res.scalar() or 0
        
        # Total amount
        amount_stmt = (
            select(func.sum(Transaction.amount))
            .join(Card)
            .where(Card.user_id == user_id)
        )
        res = await self.db.execute(amount_stmt)
        total_amount = res.scalar() or 0
        
        # Fraud statistics
        fraud_stmt = (
            select(func.count(Transaction.id))
            .join(Card)
            .where(Card.user_id == user_id, Transaction.is_fraud.is_(True))
        )
        res = await self.db.execute(fraud_stmt)
        fraud_count = res.scalar() or 0
        
        # Average transaction amount
        avg_stmt = (
            select(func.avg(Transaction.amount))
            .join(Card)
            .where(Card.user_id == user_id)
        )
        res = await self.db.execute(avg_stmt)
        avg_amount = res.scalar() or 0
        
        # Transactions by category
        categories_stmt = (
            select(
                Transaction.merchant_category,
                func.count(Transaction.id).label("count"),
                func.sum(Transaction.amount).label("total"),
            )
            .join(Card)
            .where(Card.user_id == user_id)
            .group_by(Transaction.merchant_category)
        )
        res = await self.db.execute(categories_stmt)
        categories = res.all()
        
        stats = {
            "total_transactions": total_transactions,
            "total_amount": float(total_amount),
            "fraud_count": fraud_count,
            "fraud_rate": (fraud_count / total_transactions * 100) if total_transactions > 0 else 0,
            "average_amount": float(avg_amount),
            "categories": [
                {
                    "category": cat[0],
                    "count": cat[1],
                    "total": float(cat[2])
                }
                for cat in categories
            ]
        }
        
        # Cache for 10 minutes
        await redis_client.setex(cache_key, 600, json.dumps(stats))
        
        return stats

    async def seed_demo(self, user_id: UUID, count: int = 25) -> Dict[str, Any]:
        """Create a demo card (if missing) and seed random transactions for the user."""
        # Ensure the user has at least one card
        card_stmt = select(Card).where(Card.user_id == user_id).limit(1)
        res = await self.db.execute(card_stmt)
        card = res.scalar_one_or_none()

        if not card:
            # Create a simple demo card
            card = Card(
                user_id=user_id,
                card_number="4111111111111111",
                card_type=CardType.CREDIT,
                card_brand="Visa",
                expiry_date=datetime.utcnow().date().replace(year=datetime.utcnow().year + 3),
                cvv="123",
                billing_address="Demo Street, Demo City",
                is_blocked=False,
                is_active=True,
            )
            self.db.add(card)
            await self.db.commit()
            await self.db.refresh(card)

        merchants = [
            ("Flipkart", "ecommerce"),
            ("Big Bazaar", "retail"),
            ("IRCTC", "travel"),
            ("Zomato", "food"),
            ("Swiggy", "food"),
            ("Paytm", "utilities"),
            ("Reliance Trends", "retail"),
            ("Tata Croma", "electronics"),
            ("Uber India", "transport"),
            ("Ola", "transport"),
            ("HP Petrol Pump", "fuel"),
        ]

        locations = [
            "Mumbai, IN",
            "Delhi, IN",
            "Bengaluru, IN",
            "Hyderabad, IN",
            "Chennai, IN",
            "Pune, IN",
            "Kolkata, IN",
            "Ahmedabad, IN",
            "Jaipur, IN",
            "Kochi, IN",
        ]

        created = 0
        for _ in range(max(1, count)):
            m_name, m_cat = random.choice(merchants)
            # Amounts in INR (rupees). Range ~₹100 to ₹50,000 with paise
            amount = Decimal(random.randint(100, 50000)) + (Decimal(random.randint(0, 99)) / Decimal(100))
            when = datetime.utcnow() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23), minutes=random.randint(0, 59))
            is_fraud = random.random() < 0.15
            fraud_score = round(random.uniform(0.0, 0.99), 2)

            txn = Transaction(
                card_id=card.id,
                amount=amount,
                merchant_name=m_name,
                merchant_category=m_cat,
                transaction_type=random.choice(list(TransactionType)),
                location=random.choice(locations),
                ip_address="192.168.1.%d" % random.randint(2, 254),
                device_info={"os": random.choice(["iOS", "Android", "Windows"])},
                transaction_date=when,
                is_fraud=is_fraud,
                fraud_score=float(fraud_score),
            )
            self.db.add(txn)
            created += 1

        await self.db.commit()
        # Invalidate caches
        await self._invalidate_transaction_cache(user_id)
        return {"created": created, "card_id": str(card.id)}

    async def import_csv(self, user_id: UUID, csv_bytes: bytes) -> Dict[str, Any]:
        """Import transactions from a CSV file for the given user.
        Expected columns (case-insensitive, optional where noted):
        - amount
        - merchant_name (optional)
        - merchant_category (optional)
        - transaction_type (optional; defaults to 'purchase')
        - location (optional)
        - ip_address (optional)
        - transaction_date (optional; ISO or parseable by pandas, defaults now)
        """
        # Ensure a card exists
        card_stmt = select(Card).where(Card.user_id == user_id).limit(1)
        res = await self.db.execute(card_stmt)
        card = res.scalar_one_or_none()
        if not card:
            card = Card(
                user_id=user_id,
                card_number="4111111111111111",
                card_type=CardType.CREDIT,
                card_brand="Visa",
                expiry_date=datetime.utcnow().date().replace(year=datetime.utcnow().year + 3),
                cvv="123",
                billing_address="Imported",
                is_blocked=False,
                is_active=True,
            )
            self.db.add(card)
            await self.db.commit()
            await self.db.refresh(card)

        # Read CSV (normalize common issues like unquoted commas in location fields)
        try:
            import io
            text = csv_bytes.decode("utf-8", errors="ignore")
            # Normalize patterns like "Mumbai, IN" to "Mumbai IN" to avoid delimiter splits
            text = text.replace(", IN", " IN")
            df = pd.read_csv(io.StringIO(text))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid CSV file")

        # Normalize columns
        df.columns = [str(c).strip().lower() for c in df.columns]
        created = 0

        def to_decimal(v) -> Decimal:
            if pd.isna(v):
                return Decimal("0")
            try:
                return Decimal(str(v)).quantize(Decimal("0.01"))
            except Exception:
                return Decimal("0")

        for _, row in df.iterrows():
            amount = to_decimal(row.get("amount"))
            if amount <= 0:
                continue
            m_name = row.get("merchant_name") if not pd.isna(row.get("merchant_name")) else None
            m_cat = row.get("merchant_category") if not pd.isna(row.get("merchant_category")) else None
            tx_type_raw = (row.get("transaction_type") or "purchase").lower()
            try:
                tx_type = TransactionType(tx_type_raw) if tx_type_raw in [e.value for e in TransactionType] else list(TransactionType)[0]
            except Exception:
                tx_type = list(TransactionType)[0]
            location = row.get("location") if not pd.isna(row.get("location")) else None
            ip = row.get("ip_address") if not pd.isna(row.get("ip_address")) else None
            when_val = row.get("transaction_date")
            try:
                when = pd.to_datetime(when_val).to_pydatetime() if when_val is not None and not pd.isna(when_val) else datetime.utcnow()
            except Exception:
                when = datetime.utcnow()

            txn = Transaction(
                card_id=card.id,
                amount=amount,
                merchant_name=m_name,
                merchant_category=m_cat,
                transaction_type=tx_type,
                location=location,
                ip_address=str(ip) if ip else None,
                device_info=None,
                transaction_date=when,
                is_fraud=None,
                fraud_score=None,
            )
            self.db.add(txn)
            created += 1

        await self.db.commit()
        await self._invalidate_transaction_cache(user_id)
        return {"created": created, "card_id": str(card.id)}
    
    async def export_transactions(
        self,
        user_id: UUID,
        filters: TransactionFilters
    ) -> pd.DataFrame:
        """Export transactions to DataFrame for CSV/Excel"""
        
        stmt_filters = [Card.user_id == user_id]
        if filters.start_date:
            stmt_filters.append(Transaction.transaction_date >= filters.start_date)
        if filters.end_date:
            stmt_filters.append(Transaction.transaction_date <= filters.end_date)
        if filters.min_amount:
            stmt_filters.append(Transaction.amount >= filters.min_amount)
        if filters.max_amount:
            stmt_filters.append(Transaction.amount <= filters.max_amount)
        if filters.is_fraud is not None:
            stmt_filters.append(Transaction.is_fraud == filters.is_fraud)
        if filters.merchant_category:
            stmt_filters.append(Transaction.merchant_category == filters.merchant_category)
        card_id = getattr(filters, "card_id", None)
        if card_id:
            stmt_filters.append(Transaction.card_id == card_id)
        
        stmt = select(Transaction).join(Card).where(*stmt_filters)
        res = await self.db.execute(stmt)
        transactions = res.scalars().all()
        
        # Convert to DataFrame
        data = [{
            "Transaction ID": str(t.id),
            "Date": t.transaction_date,
            "Amount": t.amount,
            "Merchant": t.merchant_name,
            "Category": t.merchant_category,
            "Type": t.transaction_type.value if hasattr(t.transaction_type, "value") else t.transaction_type,
            "Location": t.location,
            "Fraud": "Yes" if t.is_fraud else "No",
            "Fraud Score": t.fraud_score
        } for t in transactions]
        
        return pd.DataFrame(data)
    
    async def _invalidate_transaction_cache(self, user_id: UUID):
        """Clear transaction-related cache"""
        # Legacy v1 keys
        patterns = [
            f"transactions:{user_id}:*",
            f"transactions_v2:{user_id}:*",
        ]
        for pattern in patterns:
            keys = await redis_client.keys(pattern)
            if keys:
                await redis_client.delete(*keys)

        await redis_client.delete(f"transaction_stats:{user_id}")
