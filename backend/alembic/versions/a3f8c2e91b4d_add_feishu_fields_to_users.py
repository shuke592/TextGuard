"""add_feishu_fields_to_users

Revision ID: a3f8c2e91b4d
Revises: dd92b5173a1f
Create Date: 2026-05-14 09:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a3f8c2e91b4d'
down_revision: Union[str, None] = 'dd92b5173a1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 添加飞书关联字段到users表
    op.add_column('users', sa.Column('feishu_open_id', sa.String(100), nullable=True, comment='飞书应用内用户ID'))
    op.add_column('users', sa.Column('feishu_union_id', sa.String(100), nullable=True, comment='飞书企业内唯一ID'))
    op.add_column('users', sa.Column('feishu_user_id', sa.String(100), nullable=True, comment='飞书用户ID'))
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(), nullable=True, comment='最后登录时间'))
    op.add_column('users', sa.Column('login_method', sa.String(20), nullable=True, server_default='password', comment='最近登录方式：password/feishu'))

    # 创建索引
    op.create_index('ix_users_feishu_open_id', 'users', ['feishu_open_id'])
    op.create_index('ix_users_feishu_union_id', 'users', ['feishu_union_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_users_feishu_union_id', table_name='users')
    op.drop_index('ix_users_feishu_open_id', table_name='users')
    op.drop_column('users', 'login_method')
    op.drop_column('users', 'last_login_at')
    op.drop_column('users', 'feishu_user_id')
    op.drop_column('users', 'feishu_union_id')
    op.drop_column('users', 'feishu_open_id')
