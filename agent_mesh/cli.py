"""
Command Line Interface for Agent-Mesh.
Provides interactive distributed 3-node demo, peer status, and tool invocations.
"""

import argparse
import sys
import time
from .models import NodeRole
from .node import NodeIdentity
from .mesh import AgentMeshNetwork
from .proxy import TransparentMCPProxy


def run_demo() -> None:
    print("=" * 76)
    print("  🌐 AGENT-MESH: ZERO-CONFIG P2P OVERLAY FOR DISTRIBUTED AGENT SWARMS")
    print("=" * 76)

    # 1. Initialize Network
    mesh = AgentMeshNetwork(network_name="swarm-mesh-alpha")
    print("Initializing Encrypted P2P WireGuard-Style Mesh Overlay...")

    # Node 1: MacBook Pro (Local agent client)
    macbook = NodeIdentity("MacBook-M3-Max", role=NodeRole.DEVELOPER_DESKTOP, physical_endpoint="192.168.1.42:9000")
    # Register local tool
    macbook.register_tool(
        name="local_fs_read",
        description="Read local workspace files",
        input_schema={"type": "object", "properties": {"path": {"type": "string"}}},
        handler=lambda args: f"Contents of {args.get('path')}: 42 lines read."
    )

    # Node 2: GPU Lambda Rig (High compute)
    gpu_rig = NodeIdentity("GPU-Rig-8xH100", role=NodeRole.GPU_RIG, physical_endpoint="198.51.100.12:9000")
    # Register GPU inference tools
    gpu_rig.register_tool(
        name="run_vllm_inference",
        description="Run local DeepSeek-R1 inference on 8x H100 SXM5",
        input_schema={"type": "object", "properties": {"prompt": {"type": "string"}}},
        handler=lambda args: {
            "output": f"DeepSeek-R1 chain-of-thought: verified theorem for '{args.get('prompt')}'",
            "tokens_generated": 384,
            "vram_used_gb": 48.2
        }
    )

    # Node 3: Cloud Kubernetes Cluster (Enterprise data layer)
    cloud_k8s = NodeIdentity("Cloud-Prod-K8s", role=NodeRole.CLOUD_CLUSTER, physical_endpoint="10.240.0.8:9000")
    # Register enterprise DB tool
    cloud_k8s.register_tool(
        name="query_customer_db",
        description="Query production read-replica PostgreSQL",
        input_schema={"type": "object", "properties": {"customer_id": {"type": "string"}}},
        handler=lambda args: {
            "customer_id": args.get("customer_id"),
            "tier": "Enterprise Gold",
            "annual_arr": "$420,000",
            "sla_tier": "99.99%"
        }
    )

    # Connect Nodes to Mesh
    p1 = mesh.join(macbook)
    p2 = mesh.join(gpu_rig)
    p3 = mesh.join(cloud_k8s)

    print("✓ 3 Distributed Nodes connected to mesh with mutual cryptographic authentication:")
    print(f"  • {macbook.name:18} | Virtual IP: {macbook.virtual_ip:14} | Key: {macbook.public_key[:12]}...")
    print(f"  • {gpu_rig.name:18} | Virtual IP: {gpu_rig.virtual_ip:14} | Key: {gpu_rig.public_key[:12]}...")
    print(f"  • {cloud_k8s.name:18} | Virtual IP: {cloud_k8s.virtual_ip:14} | Key: {cloud_k8s.public_key[:12]}...")

    # Create Transparent MCP Proxy on MacBook
    proxy = TransparentMCPProxy(macbook, mesh)

    print("\n" + "-" * 76)
    print("GLOBAL CROSS-MACHINE MCP TOOL CATALOG (Exposed to MacBook Agent Loop)")
    print("-" * 76)
    for tool in proxy.get_available_mcp_tools():
        print(f"  [+] {tool['name']:22} -> Endpoint: {tool['mesh_endpoint']}")

    # Step 1: MacBook Agent calls remote GPU Rig
    print("\n" + "-" * 76)
    print("[1/2] MacBook Agent invokes remote tool: 'run_vllm_inference' on GPU Rig")
    print("-" * 76)
    call1 = proxy.call_tool("run_vllm_inference", {"prompt": "Prove P != NP via circuit lower bounds"})
    print(f"• Success         : {call1.success}")
    print(f"• Executing Node  : {call1.executing_node}")
    print(f"• Round-trip Time : {call1.round_trip_ms:.3f} ms (P2P WireGuard tunnel)")
    print(f"• Response Result : {call1.result}")

    # Step 2: MacBook Agent calls remote Cloud K8s Cluster
    print("\n" + "-" * 76)
    print("[2/2] MacBook Agent invokes remote tool: 'query_customer_db' on Cloud K8s")
    print("-" * 76)
    call2 = proxy.call_tool("query_customer_db", {"customer_id": "cust_enterprise_99"})
    print(f"• Success         : {call2.success}")
    print(f"• Executing Node  : {call2.executing_node}")
    print(f"• Round-trip Time : {call2.round_trip_ms:.3f} ms (P2P WireGuard tunnel)")
    print(f"• Response Result : {call2.result}")

    print("\n" + "=" * 76)
    print("  VERDICT: ZERO PORT FORWARDING. ZERO REVERSE SSH. SEAMLESS MCP MESH.")
    print("=" * 76)


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent-Mesh P2P Distributed Swarm Overlay")
    subparsers = parser.add_subparsers(dest="command")

    demo_parser = subparsers.add_parser("demo", help="Run 3-node distributed mesh demo")

    args = parser.parse_args()

    if args.command == "demo" or len(sys.argv) == 1:
        run_demo()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
