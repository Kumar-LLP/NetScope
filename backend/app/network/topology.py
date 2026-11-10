from typing import List, Optional
from app.schemas.network import (
    TopologyNode,
    TopologyEdge,
    TopologyResponse,
    TopologyNodeData,
    DeviceSchema
)
from app.network.interfaces import get_active_interface_ip
from app.network.gateway import get_default_gateway, get_gateway_mac, get_dns_servers

def generate_topology(devices: List[DeviceSchema]) -> TopologyResponse:
    """
    Transforms network discovery and interface state into a normalized
    React Flow node & edge graph structure.
    Does NOT use misleading fake fallback IP addresses.
    """
    nodes: List[TopologyNode] = []
    edges: List[TopologyEdge] = []

    active_ip = get_active_interface_ip()
    gateway_ip = get_default_gateway()
    gateway_mac = get_gateway_mac(gateway_ip) if gateway_ip else None
    dns_servers = get_dns_servers()
    primary_dns = dns_servers[0] if dns_servers else None

    # 1. Internet Node
    has_internet = bool(gateway_ip)
    nodes.append(
        TopologyNode(
            id="node-internet",
            type="internetNode",
            data=TopologyNodeData(
                label="Internet Cloud",
                subLabel="WAN Uplink" if has_internet else "Uplink Unavailable",
                ip="Public WAN",
                status="online" if has_internet else "offline",
                nodeType="internet"
            ),
            position={"x": 420.0, "y": 40.0}
        )
    )

    # 2. DNS Resolver Node
    if primary_dns:
        nodes.append(
            TopologyNode(
                id="node-dns",
                type="dnsNode",
                data=TopologyNodeData(
                    label="DNS Server",
                    subLabel="Active Nameserver",
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
                subLabel="Default Gateway" if gateway_ip else "Gateway Not Detected",
                ip=gateway_ip or "Unavailable",
                mac=gateway_mac or "Not Resolved",
                vendor="Router / AP" if gateway_ip else "Unknown",
                status="online" if gateway_ip else "offline",
                nodeType="gateway"
            ),
            position={"x": 420.0, "y": 180.0}
        )
    )

    # Edge: Gateway -> Internet
    if gateway_ip:
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
    if gateway_ip and primary_dns:
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
            id="node-host",
            type="hostNode",
            data=TopologyNodeData(
                label="Local Workstation",
                subLabel="This Device (NetScope)",
                ip=active_ip or "Loopback / Isolated",
                mac="Local Adapter",
                vendor="Local Host",
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
            source="node-host",
            target="node-gateway",
            animated=True,
            style={"stroke": "#10B981", "strokeWidth": 2}
        )
    )

    # 5. Connected LAN Devices
    # Filter out gateway and local host to avoid duplicate nodes
    filtered_devices = [
        d for d in devices
        if d.ip != gateway_ip and d.ip != active_ip and not d.is_gateway and not d.is_local_host
    ]

    total_devs = len(filtered_devices)
    if total_devs > 0:
        spacing_x = 220.0
        start_x = 420.0 - ((total_devs - 1) * spacing_x / 2.0)
        y_pos = 460.0

        for idx, dev in enumerate(filtered_devices):
            node_id = f"node-dev-{idx}"
            display_name = dev.custom_name or dev.hostname or dev.vendor
            nodes.append(
                TopologyNode(
                    id=node_id,
                    type="deviceNode",
                    data=TopologyNodeData(
                        label=display_name[:24],
                        subLabel=dev.vendor,
                        ip=dev.ip,
                        mac=dev.mac,
                        vendor=dev.vendor,
                        status=dev.status or "online",
                        nodeType="device"
                    ),
                    position={"x": start_x + (idx * spacing_x), "y": y_pos + ((idx % 2) * 50.0)}
                )
            )

            # Edge: Device -> Gateway
            edges.append(
                TopologyEdge(
                    id=f"e-dev-{idx}-gw",
                    source=node_id,
                    target="node-gateway",
                    animated=False,
                    style={"stroke": "#64748B", "strokeDasharray": "3,3"}
                )
            )

    return TopologyResponse(nodes=nodes, edges=edges)
