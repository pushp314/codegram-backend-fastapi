"""add username

Revision ID: 640924edde91
Revises: 47e4185c0efa
Create Date: 2025-04-02 18:31:59.902397

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '640924edde91'
down_revision: Union[str, None] = '47e4185c0efa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_chat_messages_id', table_name='chat_messages')
    op.drop_table('chat_messages')
    op.add_column('user', sa.Column('username', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'username')
    op.create_table('chat_messages',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('sender', sa.VARCHAR(), nullable=False),
    sa.Column('receiver', sa.VARCHAR(), nullable=False),
    sa.Column('message', sa.VARCHAR(), nullable=False),
    sa.Column('timestamp', sa.DATETIME(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chat_messages_id', 'chat_messages', ['id'], unique=False)
    # ### end Alembic commands ###
