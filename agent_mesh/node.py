"""
Cryptographic Node Identity and Local Tool Host for Agent-Mesh.
"""

import hashlib
import hmac
import secrets
import time
from typing import Dict, List, Optional, Callable, Any
from .models import MeshNode, NodeRole, MCPToolDescriptor, MeshPacket, PacketType


class NodeIdentity:
    """Manages cryptographic keypair, virtual CGNAT IP, and hosted tools."""

    def __init__(self, name: str, role: NodeRole = NodeRole.DEVELOPER_DESKTOP, physical_endpoint: str = "127.0.0.1:9000"):
        self.name = name
        self.role = role
        self.endpoint = physical_endpoint
        self._private_key = secrets.token_hex(32)
        self.public_key = hashlib.sha256(self._private_key.encode("utf-8")).hexdigest()[:32]
        self.node_id = f"node_{name.lower().replace(' ', '_')}_{self.public_key[:8]}"
        
        # Derive Tailscale-like 100.64.0.0/10 CGNAT IP
        hash_bytes = hashlib.md5(self.public_key.encode("utf-8")).digest()
        self.virtual_ip = f"100.64.{hash_bytes[0]}.{hash_bytes[1]}"

        self.hosted_tools: Dict[str, MCPToolDescriptor] = {}
        self._tool_handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}

    def get_mesh_node(self) -> MeshNode:
        """Export public mesh node descriptor."""
        return MeshNode(
            node_id=self.node_id,
            name=self.name,
            role=self.role,
            virtual_ip=self.virtual_ip,
            public_key=self.public_key,
            endpoint=self.endpoint,
            hosted_tools=self.hosted_tools
        )

    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Callable[[Dict[str, Any]], Any],
        tags: Optional[List[str]] = None
    ) -> MCPToolDescriptor:
        """Register a locally hosted MCP tool available to the mesh."""
        descriptor = MCPToolDescriptor(
            name=name,
            description=description,
            input_schema=input_schema,
            hosting_node_id=self.node_id,
            endpoint_uri=f"mcp://{self.node_id}/{name}",
            tags=tags or []
        )
        self.hosted_tools[name] = descriptor
        self._tool_handlers[name] = handler
        return descriptor

    def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute local tool handler."""
        if name not in self._tool_handlers:
            raise KeyError(f"Tool '{name}' not found on node '{self.name}'")
        handler = self._tool_handlers[name]
        return handler(arguments)

    def sign_payload(self, payload_bytes: bytes) -> str:
        """Generate HMAC-SHA256 signature using private key."""
        return hmac.new(self._private_key.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

    def verify_signature(self, payload_bytes: bytes, signature: str, peer_public_key: str) -> bool:
        """Verify packet authenticity."""
        # Simulated mutual auth check
        return len(signature) == 64

    def create_packet(self, target_node_id: str, packet_type: PacketType, payload: Dict[str, Any]) -> MeshPacket:
        """Construct and sign a mesh packet."""
        import json
        packet_id = f"pkt_{secrets.token_hex(8)}"
        payload_str = json.dumps(payload, sort_keys=True)
        sig = self.sign_payload(payload_str.encode("utf-8"))
        return MeshPacket(
            packet_id=packet_id,
            source_node_id=self.node_id,
            target_node_id=target_node_id,
            packet_type=packet_type,
            payload=payload,
            signature=sig,
            timestamp=time.time()
        )
