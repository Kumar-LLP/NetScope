from typing import List
from app.schemas.network import (
    TopologyNode,
    TopologyEdge,
    TopologyResponse,
    TopologyNodeData,
    DeviceSchema
)
from app.network.interfaces import get_active_interface_ip, get_network_interfaces
from app.network.gateway import get_default_gateway, get_gateway_mac, get_dns_servers

def generate_topology(devices: List[DeviceSchema]) -> TopologyResponse:
    """
    Transforms network discovery and interface state into a normalized
    React Flow node & edge graph structure.
    """
    nodes: List[TopologyNode] = []
    edges: List[TopologyEdge] = []

    active_ip = get_active_interface_ip() or "127.0.0.1"
    gateway_ip = get_default_gateway() or "192.168.1.1"
    gateway_mac = get_gateway_mac(gateway_ip) or "Gateway MAC"
    dns_servers = get_dns_servers()
    primary_dns = dns_servers[0] if dns_servers else "1.1.1.1"

    # 1. Internet Node
    nodes.append(
        TopologyNode(
            id="node-internet",
            type="internetNode",
            data=TopologyNodeData(
                label="Internet Cloud",
                subLabel="WAN Uplink",
                ip="Public WAN",
                status="online",
                nodeType="internet"
            ),
            position={"x": 420.0, "y": 40.0}
        )
    )

    # 2. DNS Resolver Node
    nodes.append(
        TopologyNode(
            id="node-dns",
            type="dnsNode",
            data=TopologyNodeData(
                label=f"DNS Server",
                subLabel="Primary Resolver",
                ip=primary_dns,
                status="online",
                nodeType="dns"
            ),
            position={"x": 720.0, "y": 90.0}
        )
    )

    # 3. Default Gateway Node
    nodes.append(
        TopologyNode(
            id="node-gateway",
            type="gatewayNode",
            data=TopologyNodeData(
                label="Gateway Router",
                subLabel="Default Gateway",
                ip=gateway_ip,
                mac=gateway_mac,
                vendor="Router / AP",
                status="online",
                nodeType="gateway"
            ),
            position={"x": 420.0, "y": 180.0}
        )
    )

    # Edge: Gateway -> Internet
    edges.append(
        TopologyEdge(
            id="e-gw-internet",
            source="node-gateway",
            target="node-internet",
            animated=True,
            style={"stroke": "#06B6D4", "strokeWidth": 2}
        )
    )

    # Edge: Gateway -> DNS
    edges.append(
        TopologyEdge(
            id="e-gw-dns",
            source="node-gateway",
            target="node-dns",
            animated=False,
            style={"stroke": "#8B5CF6", "strokeDasharray": "5,5"}
        )
    )

    # 4. Local Host Node (You)
    nodes.append(
        TopologyNode(
            id="node-localhost",
            type="hostNode",
            data=TopologyNodeData(
                label="Local Host (This PC)",
                subLabel="Monitoring Station",
                ip=active_ip,
                status="online",
                nodeType="host"
            ),
            position={"x": 420.0, "y": 320.0}
        )
    )

    # Edge: Host -> Gateway
    edges.append(
        TopologyEdge(
            id="e-host-gw",
            source="node-localhost",
            target="node-gateway",
            animated=True,
            style={"stroke": "#10B981", "strokeWidth": 2}
        )
    )

    # 5. Connected LAN Devices
    # Position LAN satellite devices in a clean arc or grid below/around the gateway
    lan_devices = [d for d in devices if not d.is_local_host and not d.is_gateway]
    total_lan = len(lan_devices)

    start_x = 100.0
    spacing_x = 240.0

    for idx, dev in enumerate(lan_devices):
        node_id = f"node-device-{idx}"
        pos_x = start_x + (idx % 4) * spacing_x
        pos_y = 480.0 + (idx // 4) * 140.0

        label_name = dev.hostname or dev.vendor or f"Host-{dev.ip.split('.')[-1]}"
        nodes.append(
            TopologyNode(
                id=node_id,
                type="deviceNode",
                data=TopologyNodeData(
                    label=label_name,
                    subLabel=dev.vendor,
                    ip=dev.ip,
                    mac=dev.mac,
                    vendor=dev.vendor,
                    status=dev.status,
                    nodeType="device"
                ),
                position={"x": pos_x, "y": pos_y}
            )
        )

        # Connect Device to Gateway
        edges.append(
            TopologyEdge(
                id=f"e-gw-{node_id}",
                source="node-gateway",
                target=node_id,
                animated=False,
                style={"stroke": "#38BDF8", "strokeWidth": 1.5}
            )
        )

    return TopologyResponse(nodes=nodes, edges=edges)
