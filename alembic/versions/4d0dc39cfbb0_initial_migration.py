"""Initial migration

Revision ID: 4d0dc39cfbb0
Revises: 68c447878b3d
Create Date: 2025-03-21 22:18:21.605026

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d0dc39cfbb0'
down_revision: Union[str, None] = '68c447878b3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('super_coins', sa.String(), nullable=True))
    op.create_unique_constraint(None, 'user', ['super_coins'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'user', type_='unique')
    op.drop_column('user', 'super_coins')
    # ### end Alembic commands ###
