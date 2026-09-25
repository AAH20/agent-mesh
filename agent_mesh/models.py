"""
Data models and network packet schemas for Agent-Mesh.
Zero-config P2P encrypted mesh for distributed agent swarms and cross-machine MCP tools.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import time


class NodeRole(str, Enum):
    DEVELOPER_DESKTOP = "desktop"    # Mac / Local dev environment
    GPU_RIG = "gpu_rig"              # Remote high-compute inference machine (RTX 4090 / H100)
    CLOUD_CLUSTER = "cloud_cluster"  # Kubernetes / AWS / GCP production backend
    EDGE_DEVICE = "edge"             # Raspberry Pi / Jetson / Mobile


class PacketType(str, Enum):
    HANDSHAKE = "HANDSHAKE"
    HEARTBEAT = "HEARTBEAT"
    TOOL_DISCOVERY = "TOOL_DISCOVERY"
    TOOL_CALL = "TOOL_CALL"
    TOOL_RESPONSE = "TOOL_RESPONSE"
    PEER_UPDATE = "PEER_UPDATE"


@dataclass
class MCPToolDescriptor:
    name: str
    description: str
    input_schema: Dict[str, Any]
    hosting_node_id: str
    endpoint_uri: str
    tags: List[str] = field(default_factory=list)


@dataclass
class MeshNode:
    node_id: str
    name: str
    role: NodeRole
    virtual_ip: str                # e.g. 100.64.0.12
    public_key: str
    endpoint: str                  # Physical IP:port or relay
    hosted_tools: Dict[str, MCPToolDescriptor] = field(default_factory=dict)
    is_online: bool = True
    last_seen: float = field(default_factory=time.time)
    latency_ms: float = 0.0


@dataclass
class MeshPacket:
    packet_id: str
    source_node_id: str
    target_node_id: str
    packet_type: PacketType
    payload: Dict[str, Any]
    signature: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class ToolCallResult:
    call_id: str
    success: bool
    tool_name: str
    executing_node: str
    result: Optional[Any] = None
    error: Optional[str] = None
    round_trip_ms: float = 0.0
