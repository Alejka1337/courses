"""Optional for attempt_score

Revision ID: 83d22992f773
Revises: 7b199785464a
Create Date: 2024-08-02 16:54:09.737678

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '83d22992f773'
down_revision: Union[str, None] = '7b199785464a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('student_exam_attempts', 'attempt_score',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('student_test_attempts', 'attempt_score',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('student_test_attempts', 'attempt_score',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('student_exam_attempts', 'attempt_score',
               existing_type=sa.INTEGER(),
               nullable=False)
    # ### end Alembic commands ###