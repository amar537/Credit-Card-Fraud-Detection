"""create core tables

Revision ID: 81df314e49c1
Revises: 
Create Date: 2025-11-18 06:37:25.775511

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '81df314e49c1'
down_revision = None
branch_labels = None
depends_on = None


CARD_TYPE_ENUM = postgresql.ENUM('credit', 'debit', name='cardtype')
TRANSACTION_TYPE_ENUM = postgresql.ENUM(
    'purchase', 'refund', 'cash_advance', 'payment', name='transactiontype'
)
PREDICTION_FEEDBACK_ENUM = postgresql.ENUM(
    'correct', 'incorrect', 'unknown', name='predictionfeedback'
)
ALERT_LEVEL_ENUM = postgresql.ENUM('low', 'medium', 'high', 'critical', name='alertlevel')


def upgrade() -> None:
    bind = op.get_bind()
    CARD_TYPE_ENUM.create(bind, checkfirst=True)
    TRANSACTION_TYPE_ENUM.create(bind, checkfirst=True)
    PREDICTION_FEEDBACK_ENUM.create(bind, checkfirst=True)
    ALERT_LEVEL_ENUM.create(bind, checkfirst=True)

    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255)),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_login', sa.DateTime(timezone=True)),
        sa.UniqueConstraint('email', name='uq_users_email'),
        sa.UniqueConstraint('username', name='uq_users_username'),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_username', 'users', ['username'])

    op.create_table(
        'cards',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('card_number', sa.String(length=16), nullable=False),
        sa.Column('card_type', CARD_TYPE_ENUM, nullable=False),
        sa.Column('card_brand', sa.String(length=50)),
        sa.Column('expiry_date', sa.Date(), nullable=False),
        sa.Column('cvv', sa.String(length=3), nullable=False),
        sa.Column('billing_address', sa.Text()),
        sa.Column('is_blocked', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('ix_cards_user_id', 'cards', ['user_id'])

    op.create_table(
        'transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('card_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cards.id', ondelete='CASCADE'), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('merchant_name', sa.String(length=255)),
        sa.Column('merchant_category', sa.String(length=100)),
        sa.Column('transaction_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('transaction_type', TRANSACTION_TYPE_ENUM, nullable=False),
        sa.Column('location', sa.String(length=255)),
        sa.Column('ip_address', postgresql.INET),
        sa.Column('device_info', postgresql.JSONB),
        sa.Column('is_fraud', sa.Boolean()),
        sa.Column('fraud_score', sa.Float()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['card_id'], ['cards.id'], ondelete='CASCADE')
    )
    op.create_index('ix_transactions_card_id', 'transactions', ['card_id'])
    op.create_index('ix_transactions_transaction_date', 'transactions', ['transaction_date'])

    op.create_table(
        'predictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('transactions.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('fraud_probability', sa.Float(), nullable=False),
        sa.Column('prediction_class', sa.Boolean(), nullable=False),
        sa.Column('confidence_score', sa.Float()),
        sa.Column('feature_importance', postgresql.JSONB),
        sa.Column('processing_time_ms', sa.Integer(), nullable=False),
        sa.Column('feedback', PREDICTION_FEEDBACK_ENUM, nullable=False, server_default='unknown'),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('reviewed_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'])
    )

    op.create_table(
        'fraud_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('transactions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('alert_level', ALERT_LEVEL_ENUM, nullable=False),
        sa.Column('alert_message', sa.Text(), nullable=False),
        sa.Column('is_resolved', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')), 
        sa.Column('resolved_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'])
    )
    op.create_index('ix_fraud_alerts_transaction_id', 'fraud_alerts', ['transaction_id'])


def downgrade() -> None:
    op.drop_index('ix_fraud_alerts_transaction_id', table_name='fraud_alerts')
    op.drop_table('fraud_alerts')

    op.drop_table('predictions')

    op.drop_index('ix_transactions_transaction_date', table_name='transactions')
    op.drop_index('ix_transactions_card_id', table_name='transactions')
    op.drop_table('transactions')

    op.drop_index('ix_cards_user_id', table_name='cards')
    op.drop_table('cards')

    op.drop_index('ix_users_username', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')

    bind = op.get_bind()
    ALERT_LEVEL_ENUM.drop(bind, checkfirst=True)
    PREDICTION_FEEDBACK_ENUM.drop(bind, checkfirst=True)
    TRANSACTION_TYPE_ENUM.drop(bind, checkfirst=True)
    CARD_TYPE_ENUM.drop(bind, checkfirst=True)
