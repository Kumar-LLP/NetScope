"""initial schema

Revision ID: 577e827427ad
Revises: 
Create Date: 2026-11-09 19:46:18.530241

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '577e827427ad'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - creates base tables idempotently for both fresh and existing databases."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if 'network_interfaces' not in existing_tables:
        op.create_table(
            'network_interfaces',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('name', sa.String(length=128), nullable=False),
            sa.Column('ip_address', sa.String(length=45), nullable=True),
            sa.Column('netmask', sa.String(length=45), nullable=True),
            sa.Column('mac_address', sa.String(length=17), nullable=True),
            sa.Column('is_default', sa.Boolean(), nullable=True, server_default=sa.text('0')),
            sa.Column('is_up', sa.Boolean(), nullable=True, server_default=sa.text('1')),
            sa.Column('speed_mbps', sa.Integer(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_network_interfaces_id'), 'network_interfaces', ['id'], unique=False)
        op.create_index(op.f('ix_network_interfaces_name'), 'network_interfaces', ['name'], unique=False)

    if 'network_devices' not in existing_tables:
        op.create_table(
            'network_devices',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('ip_address', sa.String(length=45), nullable=False),
            sa.Column('mac_address', sa.String(length=17), nullable=True),
            sa.Column('vendor', sa.String(length=255), nullable=True, server_default='Unknown'),
            sa.Column('hostname', sa.String(length=255), nullable=True),
            sa.Column('custom_name', sa.String(length=128), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('category', sa.String(length=64), nullable=True, server_default='workstation'),
            sa.Column('is_trusted', sa.Boolean(), nullable=True, server_default=sa.text('0')),
            sa.Column('is_gateway', sa.Boolean(), nullable=True, server_default=sa.text('0')),
            sa.Column('is_local_host', sa.Boolean(), nullable=True, server_default=sa.text('0')),
            sa.Column('status', sa.String(length=32), nullable=True, server_default='online'),
            sa.Column('first_seen', sa.DateTime(), nullable=True),
            sa.Column('last_seen', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_network_devices_id'), 'network_devices', ['id'], unique=False)
        op.create_index(op.f('ix_network_devices_ip_address'), 'network_devices', ['ip_address'], unique=False)
        op.create_index(op.f('ix_network_devices_mac_address'), 'network_devices', ['mac_address'], unique=True)

    if 'network_scans' not in existing_tables:
        op.create_table(
            'network_scans',
            sa.Column('id', sa.String(length=64), nullable=False),
            sa.Column('scan_type', sa.String(length=32), nullable=False),
            sa.Column('target_range', sa.String(length=128), nullable=False),
            sa.Column('status', sa.String(length=32), nullable=False, server_default='in_progress'),
            sa.Column('total_targets', sa.Integer(), nullable=True, server_default=sa.text('0')),
            sa.Column('found_targets', sa.Integer(), nullable=True, server_default=sa.text('0')),
            sa.Column('duration_seconds', sa.Float(), nullable=True, server_default=sa.text('0.0')),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

    if 'scan_results' not in existing_tables:
        op.create_table(
            'scan_results',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('scan_id', sa.String(length=64), nullable=False),
            sa.Column('device_id', sa.Integer(), nullable=True),
            sa.Column('ip_address', sa.String(length=45), nullable=False),
            sa.Column('mac_address', sa.String(length=17), nullable=True),
            sa.Column('response_time_ms', sa.Float(), nullable=True),
            sa.Column('discovered_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['device_id'], ['network_devices.id'], ),
            sa.ForeignKeyConstraint(['scan_id'], ['network_scans.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_scan_results_id'), 'scan_results', ['id'], unique=False)
        op.create_index(op.f('ix_scan_results_scan_id'), 'scan_results', ['scan_id'], unique=False)

    if 'network_metrics' not in existing_tables:
        op.create_table(
            'network_metrics',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('interface_id', sa.Integer(), nullable=True),
            sa.Column('interface_name', sa.String(length=128), nullable=True),
            sa.Column('download_bytes_sec', sa.Float(), nullable=False, server_default=sa.text('0.0')),
            sa.Column('upload_bytes_sec', sa.Float(), nullable=False, server_default=sa.text('0.0')),
            sa.Column('latency_ms', sa.Float(), nullable=True),
            sa.Column('packet_loss_pct', sa.Float(), nullable=True, server_default=sa.text('0.0')),
            sa.Column('total_bytes_sent', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
            sa.Column('total_bytes_recv', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
            sa.Column('timestamp', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['interface_id'], ['network_interfaces.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_network_metrics_id'), 'network_metrics', ['id'], unique=False)
        op.create_index(op.f('ix_network_metrics_timestamp'), 'network_metrics', ['timestamp'], unique=False)

    if 'ping_results' not in existing_tables:
        op.create_table(
            'ping_results',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('target', sa.String(length=255), nullable=False),
            sa.Column('packets_sent', sa.Integer(), nullable=False),
            sa.Column('packets_received', sa.Integer(), nullable=False),
            sa.Column('min_rtt_ms', sa.Float(), nullable=True),
            sa.Column('avg_rtt_ms', sa.Float(), nullable=True),
            sa.Column('max_rtt_ms', sa.Float(), nullable=True),
            sa.Column('packet_loss_pct', sa.Float(), nullable=False, server_default=sa.text('0.0')),
            sa.Column('raw_output', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_ping_results_id'), 'ping_results', ['id'], unique=False)

    if 'dns_results' not in existing_tables:
        op.create_table(
            'dns_results',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('domain', sa.String(length=255), nullable=False),
            sa.Column('record_type', sa.String(length=16), nullable=False),
            sa.Column('resolved_server', sa.String(length=64), nullable=True),
            sa.Column('records_json', sa.Text(), nullable=False),
            sa.Column('query_time_ms', sa.Float(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_dns_results_id'), 'dns_results', ['id'], unique=False)

    if 'port_diagnostics' not in existing_tables:
        op.create_table(
            'port_diagnostics',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('scan_id', sa.String(length=64), nullable=True),
            sa.Column('target_ip', sa.String(length=45), nullable=False),
            sa.Column('port', sa.Integer(), nullable=False),
            sa.Column('state', sa.String(length=16), nullable=False),
            sa.Column('service_name', sa.String(length=64), nullable=True),
            sa.Column('banner', sa.Text(), nullable=True),
            sa.Column('response_time_ms', sa.Float(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['scan_id'], ['network_scans.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_port_diagnostics_id'), 'port_diagnostics', ['id'], unique=False)
        op.create_index(op.f('ix_port_diagnostics_scan_id'), 'port_diagnostics', ['scan_id'], unique=False)

    if 'security_findings' not in existing_tables:
        op.create_table(
            'security_findings',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('device_id', sa.Integer(), nullable=True),
            sa.Column('rule_id', sa.String(length=32), nullable=False),
            sa.Column('severity', sa.String(length=16), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('category', sa.String(length=64), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('evidence', sa.Text(), nullable=False),
            sa.Column('impact', sa.Text(), nullable=False),
            sa.Column('remediation', sa.Text(), nullable=False),
            sa.Column('target', sa.String(length=255), nullable=True),
            sa.Column('confidence', sa.String(length=32), nullable=True, server_default='potential'),
            sa.Column('status', sa.String(length=32), nullable=True, server_default='active'),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
            sa.Column('resolved_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['device_id'], ['network_devices.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_security_findings_id'), 'security_findings', ['id'], unique=False)

    if 'application_settings' not in existing_tables:
        op.create_table(
            'application_settings',
            sa.Column('key', sa.String(length=128), primary_key=True, nullable=False),
            sa.Column('value', sa.Text(), nullable=False),
            sa.Column('description', sa.String(length=255), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('key')
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('application_settings')
    op.drop_table('security_findings')
    op.drop_table('port_diagnostics')
    op.drop_table('dns_results')
    op.drop_table('ping_results')
    op.drop_table('network_metrics')
    op.drop_table('scan_results')
    op.drop_table('network_scans')
    op.drop_table('network_devices')
    op.drop_table('network_interfaces')
