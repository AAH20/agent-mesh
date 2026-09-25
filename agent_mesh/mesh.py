"""
Zero-Config P2P Mesh Network Router & Coordination Layer for Agent-Mesh.
"""

import time
from typing import Dict, List, Optional, Tuple, Any
from .models import MeshNode, MeshPacket, PacketType, MCPToolDescriptor, ToolCallResult
from .node import NodeIdentity


class AgentMeshNetwork:
    """Simulated P2P encrypted WireGuard/Tailscale-style virtual mesh network."""

    def __init__(self, network_name: str = "agent-swarm-overlay"):
        self.network_name = network_name
        self.nodes: Dict[str, NodeIdentity] = {}
        self.peer_descriptors: Dict[str, MeshNode] = {}
        self.global_tool_registry: Dict[str, MCPToolDescriptor] = {}
        self.traffic_log: List[MeshPacket] = []

    def join(self, node: NodeIdentity) -> MeshNode:
        """Register a node onto the mesh network and perform mutual peer discovery."""
        self.nodes[node.node_id] = node
        desc = node.get_mesh_node()
        self.peer_descriptors[node.node_id] = desc

        # Register all tools into global registry
        for tool_name, descriptor in node.hosted_tools.items():
            self.global_tool_registry[tool_name] = descriptor

        # Dispatch peer discovery handshake to all other active nodes
        for peer_id, peer_node in self.peer_descriptors.items():
            if peer_id != node.node_id:
                peer_node.last_seen = time.time()

        return desc

    def leave(self, node_id: str) -> None:
        """Gracefully disconnect a node from the mesh."""
        if node_id in self.nodes:
            del self.nodes[node_id]
        if node_id in self.peer_descriptors:
            del self.peer_descriptors[node_id]
        # Clean up tool registry
        self.global_tool_registry = {
            t: desc for t, desc in self.global_tool_registry.items() if desc.hosting_node_id != node_id
        }

    def list_peers(self) -> List[MeshNode]:
        """List all active peers on the mesh network."""
        return list(self.peer_descriptors.values())

    def list_global_tools(self) -> List[MCPToolDescriptor]:
        """List all cross-machine MCP tools exposed across all mesh peers."""
        return list(self.global_tool_registry.values())

    def find_tool(self, tool_name: str) -> Optional[MCPToolDescriptor]:
        """Look up tool in global mesh registry."""
        return self.global_tool_registry.get(tool_name)

    def route_packet(self, packet: MeshPacket) -> MeshPacket:
        """Route packet point-to-point through encrypted mesh overlay."""
        self.traffic_log.append(packet)
        target_id = packet.target_node_id

        if target_id not in self.nodes:
            raise ConnectionError(f"Target node '{target_id}' unreachable on mesh '{self.network_name}'")

        target_node = self.nodes[target_id]

        if packet.packet_type == PacketType.TOOL_CALL:
            tool_name = packet.payload.get("tool_name")
            arguments = packet.payload.get("arguments", {})
            call_id = packet.payload.get("call_id")

            try:
                exec_result = target_node.execute_tool(tool_name, arguments)
                res_payload = {
                    "call_id": call_id,
                    "success": True,
                    "result": exec_result,
                    "tool_name": tool_name
                }
            except Exception as e:
                res_payload = {
                    "call_id": call_id,
                    "success": False,
                    "error": str(e),
                    "tool_name": tool_name
                }

            # Return response packet
            return target_node.create_packet(
                target_node_id=packet.source_node_id,
                packet_type=PacketType.TOOL_RESPONSE,
                payload=res_payload
            )

        elif packet.packet_type == PacketType.HEARTBEAT:
            return target_node.create_packet(
                target_node_id=packet.source_node_id,
                packet_type=PacketType.PEER_UPDATE,
                payload={"status": "online", "time": time.time()}
            )

        else:
            return target_node.create_packet(
                target_node_id=packet.source_node_id,
                packet_type=PacketType.PEER_UPDATE,
                payload={"acknowledged": True}
            )
