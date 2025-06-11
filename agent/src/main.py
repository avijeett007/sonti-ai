"""Main entry point for Knova AI agent worker"""

import os
import asyncio
import logging
from typing import Dict, Any

from livekit.agents import JobContext, WorkerOptions, cli
from dotenv import load_dotenv

from .worker import AgentWorker
from .integrations.livekit import LiveKitManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def entrypoint(ctx: JobContext):
    """Main entrypoint for LiveKit agent"""
    logger.info(f"Agent worker started for room: {ctx.room.name}")
    
    # Get agent configuration from room metadata
    room_metadata = ctx.room.metadata
    agent_config = {}
    
    if room_metadata:
        import json
        try:
            agent_config = json.loads(room_metadata)
        except json.JSONDecodeError:
            logger.error("Invalid room metadata")
    
    # Create and start agent worker
    worker = AgentWorker(ctx, agent_config)
    await worker.start()


def main():
    """Main function to start the agent worker"""
    logger.info("Starting Knova AI agent worker...")
    
    # Configure worker options
    worker_options = WorkerOptions(
        entrypoint_fnc=entrypoint,
        num_idle_processes=1,  # Keep one process ready
        prewarm=True,  # Prewarm workers
    )
    
    # Start the CLI
    cli.run_app(worker_options)


if __name__ == "__main__":
    main()