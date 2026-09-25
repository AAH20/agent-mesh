"""
Transparent Cross-Host MCP Proxy for Agent-Mesh.
Allows local agent loops to invoke remote GPU / Cloud tools as native local MCP tools.
"""

import secrets
import time
from typing import Dict, List, Optional, Any
from .models import ToolCallResult, MCPToolDescriptor, PacketType
from .node import NodeIdentity
from .mesh import AgentMeshNetwork


class TransparentMCPProxy:
    """Transparent proxy exposing entire mesh tool catalog as local MCP tools."""

    def __init__(self, local_node: NodeIdentity, mesh: AgentMeshNetwork):
        self.local_node = local_node
        self.mesh = mesh

    def get_available_mcp_tools(self) -> List[Dict[str, Any]]:
        """
        Export standard MCP tools list schema suitable for Claude / Cursor / Gemini.
        Transparently includes all cross-machine tools from the mesh.
        """
        tools = []
        for descriptor in self.mesh.list_global_tools():
            tools.append({
                "name": descriptor.name,
                "description": f"[{descriptor.hosting_node_id}] {descriptor.description}",
                "inputSchema": descriptor.input_schema,
                "mesh_endpoint": descriptor.endpoint_uri
            })
        return tools

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolCallResult:
        """
        Invoke any tool across the mesh transparently.
        Handles target resolution, mTLS packet encapsulation, and latency timing.
        """
        start_time = time.time()
        call_id = f"call_{secrets.token_hex(6)}"

        descriptor = self.mesh.find_tool(tool_name)
        if not descriptor:
            return ToolCallResult(
                call_id=call_id,
                success=False,
                tool_name=tool_name,
                executing_node="none",
                error=f"Tool '{tool_name}' not discovered anywhere on mesh network",
                round_trip_ms=(time.time() - start_time) * 1000.0
            )

        target_node_id = descriptor.hosting_node_id

        # Local short-circuit if the tool is hosted on this same node
        if target_node_id == self.local_node.node_id:
            try:
                res = self.local_node.execute_tool(tool_name, arguments)
                return ToolCallResult(
                    call_id=call_id,
                    success=True,
                    tool_name=tool_name,
                    executing_node=self.local_node.node_id,
                    result=res,
                    round_trip_ms=(time.time() - start_time) * 1000.0
                )
            except Exception as e:
                return ToolCallResult(
                    call_id=call_id,
                    success=False,
                    tool_name=tool_name,
                    executing_node=self.local_node.node_id,
                    error=str(e),
                    round_trip_ms=(time.time() - start_time) * 1000.0
                )

        # Cross-machine mesh call
        packet = self.local_node.create_packet(
            target_node_id=target_node_id,
            packet_type=PacketType.TOOL_CALL,
            payload={
                "call_id": call_id,
                "tool_name": tool_name,
                "arguments": arguments
            }
        )

        response_packet = self.mesh.route_packet(packet)
        resp_payload = response_packet.payload
        round_trip_ms = (time.time() - start_time) * 1000.0

        return ToolCallResult(
            call_id=call_id,
            success=resp_payload.get("success", False),
            tool_name=tool_name,
            executing_node=target_node_id,
            result=resp_payload.get("result"),
            error=resp_payload.get("error"),
            round_trip_ms=round_trip_ms
        )
