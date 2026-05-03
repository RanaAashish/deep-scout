import asyncio
from main import run_research  
import sys
import os

# Add app to path if needed (if running from root)
sys.path.append(os.path.join(os.path.dirname(__file__), "."))

from core.logging_config import setup_logging

async def main():
    setup_logging(verbose=True)
    result = await run_research(
        topic="muti-agent-orchestration frameworks in GenAI",
        purpose="learn",
        depth="basic",
        output_format="report",
    )
    print(result)

if __name__ == "__main__":
    asyncio.run(main())