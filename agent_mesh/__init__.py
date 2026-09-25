"""
Agent-Mesh: Zero-Config Tailscale / WireGuard P2P Mesh for Distributed Agent Swarms.
"""

from .models import (
    NodeRole,
    PacketType,
    MCPToolDescriptor,
    MeshNode,
    MeshPacket,
    ToolCallResult,
)
from .node import NodeIdentity
from .mesh import AgentMeshNetwork
from .proxy import TransparentMCPProxy

__version__ = "1.0.0"
__all__ = [
    "NodeRole",
    "PacketType",
    "MCPToolDescriptor",
    "MeshNode",
    "MeshPacket",
    "ToolCallResult",
    "NodeIdentity",
    "AgentMeshNetwork",
    "TransparentMCPProxy",
]
