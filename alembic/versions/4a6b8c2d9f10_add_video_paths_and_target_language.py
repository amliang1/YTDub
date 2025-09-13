"""Add video path fields and target_language to videos

Revision ID: 4a6b8c2d9f10
Revises: 3f8e9d2a1b4c
Create Date: 2025-01-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a6b8c2d9f10'
down_revision: Union[str, None] = '3f8e9d2a1b4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new nullable columns to videos table
    op.add_column('videos', sa.Column('target_language', sa.String(), nullable=True))
    op.add_column('videos', sa.Column('video_path', sa.String(), nullable=True))
    op.add_column('videos', sa.Column('audio_path', sa.String(), nullable=True))
    op.add_column('videos', sa.Column('output_path', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove columns on downgrade
    op.drop_column('videos', 'output_path')
    op.drop_column('videos', 'audio_path')
    op.drop_column('videos', 'video_path')
    op.drop_column('videos', 'target_language')

