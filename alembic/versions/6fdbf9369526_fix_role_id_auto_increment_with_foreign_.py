"""Fix role_id auto increment with foreign key

Revision ID: 6fdbf9369526
Revises: 89eded433a9f
Create Date: 2025-12-23 14:24:05.541887

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6fdbf9369526'
down_revision: Union[str, Sequence[str], None] = '89eded433a9f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop foreign key constraint
    op.drop_constraint('user_roles_ibfk_1', 'user_roles', type_='foreignkey')
    
    # Modify role_id to add AUTO_INCREMENT
    op.execute('ALTER TABLE roles MODIFY role_id BIGINT AUTO_INCREMENT')
    
    # Re-add foreign key constraint
    op.create_foreign_key('user_roles_ibfk_1', 'user_roles', 'roles', ['role_id'], ['role_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop foreign key constraint
    op.drop_constraint('user_roles_ibfk_1', 'user_roles', type_='foreignkey')
    
    # Remove AUTO_INCREMENT from role_id
    op.execute('ALTER TABLE roles MODIFY role_id BIGINT')
    
    # Re-add foreign key constraint
    op.create_foreign_key('user_roles_ibfk_1', 'user_roles', 'roles', ['role_id'], ['role_id'])
