"""
Comprehensive Unit Test Suite for Agent-Mesh.
"""

import unittest
from agent_mesh.models import NodeRole, PacketType
from agent_mesh.node import NodeIdentity
from agent_mesh.mesh import AgentMeshNetwork
from agent_mesh.proxy import TransparentMCPProxy


class TestAgentMesh(unittest.TestCase):

    def setUp(self):
        self.mesh = AgentMeshNetwork(network_name="test-mesh")
        self.node_client = NodeIdentity("client_node", role=NodeRole.DEVELOPER_DESKTOP)
        self.node_server = NodeIdentity("server_node", role=NodeRole.GPU_RIG)

        # Register server-side tool
        self.node_server.register_tool(
            name="multiply_vectors",
            description="Multiplies two numbers",
            input_schema={"type": "object"},
            handler=lambda args: args.get("a", 0) * args.get("b", 0)
        )

        self.mesh.join(self.node_client)
        self.mesh.join(self.node_server)
        self.proxy = TransparentMCPProxy(self.node_client, self.mesh)

    def test_node_identity_and_virtual_ip(self):
        """Test cryptographic key derivation and Tailscale CGNAT IP assignment."""
        self.assertTrue(self.node_client.virtual_ip.startswith("100.64."))
        self.assertTrue(self.node_server.virtual_ip.startswith("100.64."))
        self.assertEqual(len(self.node_client.public_key), 32)

    def test_mesh_peer_discovery_and_catalog(self):
        """Test peer discovery and global tool registration."""
        peers = self.mesh.list_peers()
        self.assertEqual(len(peers), 2)

        tools = self.mesh.list_global_tools()
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0].name, "multiply_vectors")
        self.assertEqual(tools[0].hosting_node_id, self.node_server.node_id)

    def test_transparent_cross_machine_tool_invocation(self):
        """Test executing remote tool across encrypted mesh proxy."""
        result = self.proxy.call_tool("multiply_vectors", {"a": 7, "b": 6})
        self.assertTrue(result.success)
        self.assertEqual(result.result, 42)
        self.assertEqual(result.executing_node, self.node_server.node_id)
        self.assertGreater(result.round_trip_ms, 0.0)

    def test_unknown_tool_handling(self):
        """Test graceful error handling when tool does not exist."""
        result = self.proxy.call_tool("non_existent_tool", {})
        self.assertFalse(result.success)
        self.assertIn("not discovered anywhere", result.error)

    def test_node_leave_and_catalog_cleanup(self):
        """Test that disconnecting a node removes its tools from the mesh catalog."""
        self.mesh.leave(self.node_server.node_id)
        tools = self.mesh.list_global_tools()
        self.assertEqual(len(tools), 0)

        # Invocation should now fail
        res = self.proxy.call_tool("multiply_vectors", {"a": 2, "b": 2})
        self.assertFalse(res.success)


if __name__ == "__main__":
    unittest.main()
