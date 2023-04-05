"""convert to declarative model

Revision ID: 347e8c39fd1b
Revises: 34f7ab360a3a
Create Date: 2023-04-06 16:56:55.343280

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '347e8c39fd1b'
down_revision = '34f7ab360a3a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('component', schema=None) as batch_op:
        batch_op.alter_column('name',
               existing_type=sa.VARCHAR(),
               nullable=False)

    with op.batch_alter_table('component_attribute', schema=None) as batch_op:
        batch_op.alter_column('name',
               existing_type=sa.VARCHAR(),
               nullable=False)
        batch_op.alter_column('value',
               existing_type=sa.VARCHAR(),
               nullable=False)
        batch_op.drop_constraint('u_attr_comp', type_='unique')

    with op.batch_alter_table('incident', schema=None) as batch_op:
        batch_op.alter_column('text',
               existing_type=sa.VARCHAR(),
               nullable=False)
        batch_op.alter_column('start_date',
               existing_type=sa.DATETIME(),
               nullable=False)
        batch_op.alter_column('impact',
               existing_type=sa.SMALLINT(),
               nullable=False)

    with op.batch_alter_table('incident_component_relation', schema=None) as batch_op:
        batch_op.alter_column('incident_id',
               existing_type=sa.INTEGER(),
               nullable=False)
        batch_op.alter_column('component_id',
               existing_type=sa.INTEGER(),
               nullable=False)
        batch_op.drop_index('inc_comp_rel')
        batch_op.create_index('inc_comp_rel', ['incident_id', 'component_id'], unique=True)
        batch_op.drop_column('id')

    with op.batch_alter_table('incident_status', schema=None) as batch_op:
        batch_op.alter_column('timestamp',
               existing_type=sa.DATETIME(),
               nullable=False)
        batch_op.alter_column('text',
               existing_type=sa.VARCHAR(),
               nullable=False)
        batch_op.alter_column('status',
               existing_type=sa.VARCHAR(),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('incident_status', schema=None) as batch_op:
        batch_op.alter_column('status',
               existing_type=sa.VARCHAR(),
               nullable=True)
        batch_op.alter_column('text',
               existing_type=sa.VARCHAR(),
               nullable=True)
        batch_op.alter_column('timestamp',
               existing_type=sa.DATETIME(),
               nullable=True)

    with op.batch_alter_table('incident_component_relation', schema=None) as batch_op:
        batch_op.add_column(sa.Column('id', sa.INTEGER(), nullable=False))
        batch_op.drop_index('inc_comp_rel')
        batch_op.create_index('inc_comp_rel', ['incident_id', 'component_id'], unique=False)
        batch_op.alter_column('component_id',
               existing_type=sa.INTEGER(),
               nullable=True)
        batch_op.alter_column('incident_id',
               existing_type=sa.INTEGER(),
               nullable=True)

    with op.batch_alter_table('incident', schema=None) as batch_op:
        batch_op.alter_column('impact',
               existing_type=sa.SMALLINT(),
               nullable=True)
        batch_op.alter_column('start_date',
               existing_type=sa.DATETIME(),
               nullable=True)
        batch_op.alter_column('text',
               existing_type=sa.VARCHAR(),
               nullable=True)

    with op.batch_alter_table('component_attribute', schema=None) as batch_op:
        batch_op.create_unique_constraint('u_attr_comp', ['component_id', 'name'])
        batch_op.alter_column('value',
               existing_type=sa.VARCHAR(),
               nullable=True)
        batch_op.alter_column('name',
               existing_type=sa.VARCHAR(),
               nullable=True)

    with op.batch_alter_table('component', schema=None) as batch_op:
        batch_op.alter_column('name',
               existing_type=sa.VARCHAR(),
               nullable=True)

    # ### end Alembic commands ###