"""
Test script for PRISM agent system
Validates agent initialization, execution, and coordination
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.agents import (
    AgentRegistry,
    AgentCoordinator,
    PersonalFileAgent,
    PersonalWebAgent,
    PersonalProductivityAgent,
    AgentCapability
)
from loguru import logger


async def test_agent_initialization():
    """Test agent initialization and registration"""
    print("\n" + "="*60)
    print("TEST 1: Agent Initialization")
    print("="*60)
    
    registry = AgentRegistry()
    
    # Create agents
    file_agent = PersonalFileAgent()
    web_agent = PersonalWebAgent()
    productivity_agent = PersonalProductivityAgent()
    
    # Register agents
    print("Registering agents...")
    success1 = await registry.register(file_agent)
    success2 = await registry.register(web_agent)
    success3 = await registry.register(productivity_agent)
    
    print(f"File Agent: {'✓' if success1 else '✗'}")
    print(f"Web Agent: {'✓' if success2 else '✗'}")
    print(f"Productivity Agent: {'✓' if success3 else '✗'}")
    
    # Check registry stats
    stats = registry.get_statistics()
    print(f"\nRegistry Stats:")
    print(f"  Total Agents: {stats['total_agents']}")
    print(f"  Healthy Agents: {stats['healthy_agents']}")
    
    return registry


async def test_agent_execution(registry):
    """Test direct agent execution"""
    print("\n" + "="*60)
    print("TEST 2: Direct Agent Execution")
    print("="*60)
    
    # Test File Agent
    print("\n[File Agent] Organizing downloads...")
    file_agent = registry.get_agent("PersonalFileAgent")
    response = await file_agent._safe_execute("organize downloads")
    print(f"Status: {response.status.value}")
    print(f"Message: {response.message}")
    
    # Test Web Agent
    print("\n[Web Agent] Research Python...")
    web_agent = registry.get_agent("PersonalWebAgent")
    response = await web_agent._safe_execute("research Python")
    print(f"Status: {response.status.value}")
    print(f"Message: {response.message}")
    if response.data:
        print(f"Data: {response.data}")
    
    # Test Productivity Agent
    print("\n[Productivity Agent] Start focus session...")
    productivity_agent = registry.get_agent("PersonalProductivityAgent")
    response = await productivity_agent._safe_execute("start focus session for 25 minutes")
    print(f"Status: {response.status.value}")
    print(f"Message: {response.message}")


async def test_agent_coordinator(registry):
    """Test agent coordination"""
    print("\n" + "="*60)
    print("TEST 3: Agent Coordinator")
    print("="*60)
    
    coordinator = AgentCoordinator(registry)
    
    # Test different task types
    test_tasks = [
        "search for files named test",
        "organize my downloads folder",
        "research artificial intelligence",
        "start a focus session",
        "suggest a break"
    ]
    
    for task in test_tasks:
        print(f"\n[Task] {task}")
        response = await coordinator.execute_task(task)
        print(f"  Agent: {response.agent_name}")
        print(f"  Status: {response.status.value}")
        print(f"  Message: {response.message}")


async def test_agent_health():
    """Test agent health checks"""
    print("\n" + "="*60)
    print("TEST 4: Agent Health Checks")
    print("="*60)
    
    registry = AgentRegistry()
    
    # Create and register agents
    agents = [
        PersonalFileAgent(),
        PersonalWebAgent(),
        PersonalProductivityAgent()
    ]
    
    for agent in agents:
        await registry.register(agent)
    
    # Health check all agents
    health = await registry.health_check_all()
    
    for agent_name, health_data in health.items():
        print(f"\n{agent_name}:")
        print(f"  Status: {health_data.get('status')}")
        print(f"  Healthy: {'✓' if health_data.get('healthy') else '✗'}")
        print(f"  Executions: {health_data.get('execution_count', 0)}")
        print(f"  Capabilities: {', '.join(health_data.get('capabilities', []))}")
    
    return registry


async def main():
    """Run all tests"""
    logger.info("Starting PRISM Agent System Tests")
    
    try:
        # Test 1: Initialization
        registry = await test_agent_initialization()
        
        # Test 2: Direct execution
        await test_agent_execution(registry)
        
        # Test 3: Coordination
        await test_agent_coordinator(registry)
        
        # Test 4: Health checks
        registry = await test_agent_health()
        
        # Cleanup
        print("\n" + "="*60)
        print("Shutting down agents...")
        await registry.shutdown_all()
        print("✓ All agents shut down")
        
        print("\n" + "="*60)
        print("✓ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        logger.exception("Test failure")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
