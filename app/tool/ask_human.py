from app.tool import BaseTool
import asyncio
import os
import httpx
import json
from app.logger import logger
from fastapi import FastAPI, Request
import uvicorn

class AskHuman(BaseTool):
    """Add a tool to ask human for help."""

    name: str = "ask_human"
    description: str = "Use this tool to ask human for help."
    parameters: str = {
        "type": "object",
        "properties": {
            "inquire": {
                "type": "string",
                "description": "The question you want to ask human.",
            }
        },
        "required": ["inquire"],
    }

    async def execute(self, inquire: str) -> str:
        logger.warning("------- ASKING A HUMAN FOR HELP: ---------")
        logger.warning(inquire.strip())
        logger.warning("------------------------------------------")

        webhook_url = "http://vm.local:30002/webhook/human"
        response = None

        async with httpx.AsyncClient() as client:

            # Send the inquiry
            await client.post(webhook_url, json={"inquire": inquire})

            app = FastAPI()

            got_response = asyncio.Event()

            @app.post("/")
            async def callback(request: Request):
                data = await request.json()
                logger.success("✅ received: ", data)
                nonlocal response
                response = data.get("msg").strip()
                got_response.set()

                return {}

            config = uvicorn.Config(app, host="0.0.0.0", port=8001, log_level="error")
            server = uvicorn.Server(config)

            # start the HTTP server in the background
            server_task = asyncio.create_task(server.serve())

            # loop until the callback flips our event
            while not got_response.is_set():
                logger.warning("Waiting for answer")
                await asyncio.sleep(30)

            # once we got it, shut down the server
            server.should_exit = True
            await server_task

            logger.success("------------ USER ANSWERED: --------------")
            logger.success(response)
            logger.success("------------------------------------------")

            return response
