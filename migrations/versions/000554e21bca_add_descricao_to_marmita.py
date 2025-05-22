"""add descricao to marmita

Revision ID: 000554e21bca
Revises: d26057868337
Create Date: 2025-05-22 15:23:53.473600

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '000554e21bca'
down_revision = 'd26057868337'
branch_labels = None
depends_on = None


def upgrade():
    # ✅ Adiciona coluna descricao na tabela marmita
    with op.batch_alter_table('marmita', schema=None) as batch_op:
        batch_op.add_column(sa.Column('descricao', sa.String(length=500), nullable=True))

    # 🔥 Removido alteração desnecessária da senha_hash


def downgrade():
    # ✅ Remove a coluna descricao
    with op.batch_alter_table('marmita', schema=None) as batch_op:
        batch_op.drop_column('descricao')

    # 🔥 Removido alteração desnecessária da senha_hash
