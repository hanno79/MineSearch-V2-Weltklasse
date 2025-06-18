"""add_languages_column_to_mines

Revision ID: d87cb8d324c2
Revises: d81cdd1a3db2
Create Date: 2025-06-16 16:37:33.473942

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd87cb8d324c2'
down_revision: Union[str, None] = 'd81cdd1a3db2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add languages column to mines table if not exists
    try:
        op.add_column('mines', sa.Column('languages', sa.JSON(), nullable=True))
    except:
        pass  # Column might already exist
    
    # The results and aggregated_data tables already exist, so skip creation
    
    # Update searches table to match model
    try:
        op.add_column('searches', sa.Column('total_results', sa.Integer(), nullable=True))
    except:
        pass
        
    try:
        op.add_column('searches', sa.Column('success_rate', sa.Float(), nullable=True))
    except:
        pass


def downgrade() -> None:
    # Remove added columns and tables
    op.drop_column('mines', 'languages')
    op.drop_table('aggregated_data')
    op.drop_table('results')
    op.drop_column('searches', 'total_results')
    op.drop_column('searches', 'success_rate')
    op.add_column('searches', sa.Column('results_count', sa.Integer(), nullable=True))
    op.add_column('searches', sa.Column('error_message', sa.Text(), nullable=True))
