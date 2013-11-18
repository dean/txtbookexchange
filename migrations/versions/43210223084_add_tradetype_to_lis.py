"""add tradetype to listing

Revision ID: 43210223084
Revises: None
Create Date: 2013-09-18 04:44:23.081529

"""

# revision identifiers, used by Alembic.
revision = '43210223084'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('listings', sa.Column('trade_type', sa.Enum('Buying', 'Selling', name="trade_types")))


def downgrade():
    op.drop_column('listings', 'trade_type')


