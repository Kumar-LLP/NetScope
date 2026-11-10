"""add packet capture, anomaly, device observation and intelligence models

Revision ID: 2ca1594d866b
Revises: 577e827427ad
Create Date: 2026-11-10 08:28:04.753302

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2ca1594d866b'
down_revision: Union[str, Sequence[str], None] = '577e827427ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema idempotently."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if 'network_anomalies' not in existing_tables:
        op.create_table(
            'network_anomalies',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('anomaly_type', sa.String(length=64), nullable=False),
            sa.Column('severity', sa.String(length=16), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('evidence', sa.Text(), nullable=False),
            sa.Column('target', sa.String(length=255), nullable=True),
            sa.Column('confidence', sa.String(length=32), nullable=True),
            sa.Column('threshold_trigger', sa.String(length=128), nullable=True),
            sa.Column('detected_at', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(length=32), nullable=True, server_default='active'),
            sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
            sa.Column('resolved_at', sa.DateTime(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_network_anomalies_id'), 'network_anomalies', ['id'], unique=False)
        op.create_index(op.f('ix_network_anomalies_anomaly_type'), 'network_anomalies', ['anomaly_type'], unique=False)
        op.create_index(op.f('ix_network_anomalies_status'), 'network_anomalies', ['status'], unique=False)

    if 'packet_capture_sessions' not in existing_tables:
        op.create_table(
            'packet_capture_sessions',
            sa.Column('id', sa.String(length=64), nullable=False),
            sa.Column('interface_name', sa.String(length=128), nullable=False),
            sa.Column('status', sa.String(length=32), nullable=True, server_default='running'),
            sa.Column('total_packets', sa.Integer(), nullable=True, server_default=sa.text('0')),
            sa.Column('tcp_packets', sa.Integer(), nullable=True, server_default=sa.text('0')),
            sa.Column('udp_packets', sa.Integer(), nullable=True, server_default=sa.text('0')),
            sa.Column('icmp_packets', sa.Integer(), nullable=True, server_default=sa.text('0')),
            sa.Column('dns_packets', sa.Integer(), nullable=True, server_default=sa.text('0')),
            sa.Column('other_packets', sa.Integer(), nullable=True, server_default=sa.text('0')),
            sa.Column('total_bytes', sa.Integer(), nullable=True, server_default=sa.text('0')),
            sa.Column('duration_seconds', sa.Float(), nullable=True, server_default=sa.text('0.0')),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('stopped_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

    if 'device_observations' not in existing_tables:
        op.create_table(
            'device_observations',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('device_id', sa.Integer(), nullable=True),
            sa.Column('ip_address', sa.String(length=45), nullable=False),
            sa.Column('mac_address', sa.String(length=17), nullable=True),
            sa.Column('interface_name', sa.String(length=128), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=True),
            sa.Column('scan_id', sa.String(length=64), nullable=True),
            sa.Column('source', sa.String(length=32), nullable=False, server_default='arp'),
            sa.Column('response_status', sa.String(length=32), nullable=True, server_default='responding'),
            sa.Column('confidence', sa.String(length=32), nullable=True, server_default='confirmed'),
            sa.ForeignKeyConstraint(['device_id'], ['network_devices.id'], ),
            sa.ForeignKeyConstraint(['scan_id'], ['network_scans.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_device_observations_id'), 'device_observations', ['id'], unique=False)
        op.create_index(op.f('ix_device_observations_ip_address'), 'device_observations', ['ip_address'], unique=False)
        op.create_index(op.f('ix_device_observations_mac_address'), 'device_observations', ['mac_address'], unique=False)
        op.create_index(op.f('ix_device_observations_timestamp'), 'device_observations', ['timestamp'], unique=False)

    if 'intelligence_events' not in existing_tables:
        op.create_table(
            'intelligence_events',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('event_id', sa.String(length=64), nullable=False),
            sa.Column('category', sa.String(length=64), nullable=False),
            sa.Column('severity', sa.String(length=16), nullable=False),
            sa.Column('confidence', sa.String(length=32), nullable=False),
            sa.Column('timestamp', sa.DateTime(), nullable=True),
            sa.Column('affected_device_ip', sa.String(length=45), nullable=True),
            sa.Column('affected_device_mac', sa.String(length=17), nullable=True),
            sa.Column('evidence_references', sa.Text(), nullable=False),
            sa.Column('explanation', sa.Text(), nullable=False),
            sa.Column('recommended_action', sa.Text(), nullable=False),
            sa.Column('investigation_status', sa.String(length=32), nullable=True, server_default='unreviewed'),
            sa.Column('resolved_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_intelligence_events_id'), 'intelligence_events', ['id'], unique=False)
        op.create_index(op.f('ix_intelligence_events_event_id'), 'intelligence_events', ['event_id'], unique=True)
        op.create_index(op.f('ix_intelligence_events_timestamp'), 'intelligence_events', ['timestamp'], unique=False)
        op.create_index(op.f('ix_intelligence_events_category'), 'intelligence_events', ['category'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('intelligence_events')
    op.drop_table('device_observations')
    op.drop_table('packet_capture_sessions')
    op.drop_table('network_anomalies')
