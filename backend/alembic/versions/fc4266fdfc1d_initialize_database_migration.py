"""initialize database migration

Revision ID: fc4266fdfc1d
Revises:
Create Date: 2026-07-21 18:52:29.241699

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "fc4266fdfc1d"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
