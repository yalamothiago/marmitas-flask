"""Adiciona tabelas Carrinho e CarrinhoItem e atualiza relacionamentos

Revision ID: 975d305643ae
Revises: 9e02b1269165
Create Date: 2025-05-24 14:24:26.977237

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '975d305643ae'
down_revision = '9e02b1269165'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('carrinho',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['usuario.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )
    op.create_table('carrinho_item',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('carrinho_id', sa.Integer(), nullable=False),
    sa.Column('marmita_id', sa.Integer(), nullable=False),
    sa.Column('quantidade', sa.Integer(), nullable=False),
    sa.Column('preco_unitario', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['carrinho_id'], ['carrinho.id'], ),
    sa.ForeignKeyConstraint(['marmita_id'], ['marmita.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('carrinho_item')
    op.drop_table('carrinho')
    # ### end Alembic commands ###
