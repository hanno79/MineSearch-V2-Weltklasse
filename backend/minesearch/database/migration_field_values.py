"""
SCHEMA-NORMALISIERUNG 28.08.2025: Migration für atomische Feldwerte
Erstellt neue Tabellen für saubere Trennung von Werten und Quellenreferenzen

Revision ID: field_values_normalization
Revises: base
Create Date: 2025-08-28
"""

import logging
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers
revision = 'field_values_normalization'
down_revision = None
branch_labels = None
depends_on = None

logger = logging.getLogger('alembic.runtime.migration')

def upgrade():
    """Erstelle neue normalisierte Tabellen für Feldwerte"""
    
    # Erstelle field_values Tabelle
    op.create_table(
        'field_values',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('search_result_id', sa.Integer, sa.ForeignKey('search_results.id'), nullable=False),
        sa.Column('field_name', sa.String(100), nullable=False, index=True),
        sa.Column('atomic_value', sa.Text, nullable=True),
        sa.Column('confidence_score', sa.Float, nullable=False, default=0.0),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    
    # Erstelle Indizes für field_values
    op.create_index('idx_field_values_result', 'field_values', ['search_result_id'])
    op.create_index('idx_field_values_name', 'field_values', ['field_name'])
    op.create_index('idx_field_values_atomic', 'field_values', ['atomic_value'])
    op.create_index('idx_field_values_result_field', 'field_values', ['search_result_id', 'field_name'])
    
    # Erstelle field_value_sources Tabelle
    op.create_table(
        'field_value_sources',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('field_value_id', sa.Integer, sa.ForeignKey('field_values.id'), nullable=False),
        sa.Column('source_id', sa.Integer, sa.ForeignKey('sources.id'), nullable=False),
        sa.Column('extraction_confidence', sa.Float, nullable=False, default=50.0),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    
    # Erstelle Indizes für field_value_sources
    op.create_index('idx_fvs_field_value', 'field_value_sources', ['field_value_id'])
    op.create_index('idx_fvs_source', 'field_value_sources', ['source_id'])
    op.create_index('idx_fvs_field_source', 'field_value_sources', ['field_value_id', 'source_id'])
    
    logger.info("✅ Neue normalisierte Tabellen für atomische Feldwerte erstellt")


def downgrade():
    """Entferne normalisierte Tabellen (Rollback)"""
    
    # Lösche Indizes
    op.drop_index('idx_fvs_field_source', 'field_value_sources')
    op.drop_index('idx_fvs_source', 'field_value_sources')
    op.drop_index('idx_fvs_field_value', 'field_value_sources')
    
    op.drop_index('idx_field_values_result_field', 'field_values')
    op.drop_index('idx_field_values_atomic', 'field_values')
    op.drop_index('idx_field_values_name', 'field_values')
    op.drop_index('idx_field_values_result', 'field_values')
    
    # Lösche Tabellen
    op.drop_table('field_value_sources')
    op.drop_table('field_values')
    
    logger.info("❌ Normalisierte Tabellen für atomische Feldwerte entfernt")