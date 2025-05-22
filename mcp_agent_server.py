from dotenv import load_dotenv
import os
load_dotenv()
os.environ["ANONYMIZED_TELEMETRY"] = "false"

import asyncio
from typing import List
from fastmcp import FastMCP
import uvicorn

from app.agent.manus import Manus
from app.logger import logger
import socket

host_ip = os.getenv("HOST")
host_port = int(os.getenv("PORT"))
dns_check = os.getenv("DNS_CHECK")

#https://gofastmcp.com/servers/fastmcp
#https://github.com/jlowin/fastmcp
mcp = FastMCP("Manus")

@mcp.tool()
async def super_agent_tool(prompt: str) -> str:
    """
    Ask the super researcher Manus Agent to do web research and various hard tasks,
    including asking humans for more instructions.
    """

    logger.info("Instantiating Manus Agent")
    agent = await Manus.create()

    logger.success("------------MISSION RECEIVED---------------")
    logger.success(prompt.strip())
    logger.success("-------------------------------------------")


    try:
        if not prompt.strip():
            logger.warning("Empty prompt provided.")
            return

        logger.info("Processing your request...")

        response = await agent.run(prompt)

        logger.info("Request processing completed.")
    except KeyboardInterrupt:
        logger.warning("Operation interrupted.")
        await agent.cleanup()

    finally:
        # Ensure agent resources are cleaned up before exiting
        await agent.cleanup()


    logger.success("\n\n----------- FINAL RESPONSE ----------------")
    print(f"\033[32m\n{response}\033[0m\n")

    return response


# http_app = mcp.http_app() #modern http streamable version, wait n8n update to update this too
sse_app = mcp.sse_app() #legacy will be discontinued soon but still working sse version

if __name__ == "__main__":

    print("\033[32m###########################################################################\033[0m")
    print("\033[32m######################## MCP Agent Server Started at: #####################\033[0m")
    # Print the local network address
    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect((dns_check, 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    print(f"\033[32m########################\033[0m http://{get_local_ip()}:{host_port}/sse  \033[32m#####################\033[0m")
    print("\033[32m###########################################################################\033[0m")

    try:
        uvicorn.run(sse_app, host=host_ip, port=host_port)
    except KeyboardInterrupt:
        print("\n\033[31mGraceful shutdown requested. Exiting...\033[0m")
        uvicorn.stop()
        agent.cleanup()
