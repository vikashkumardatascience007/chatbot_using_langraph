import asyncio
import json
import subprocess
import sys

async def main():
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "mcp-client-and-server-langgraph/calculator_mcp_server.py",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
    )

    try:
        # INIT
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "0.1"}
            }
        }

        proc.stdin.write((json.dumps(init_request) + "\n").encode())
        await proc.stdin.drain()
        print(await proc.stdout.readline())

        # TOOL CALL
        tool_call = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "add",
                "arguments": {"a": 3, "b": 4}
            }
        }

        proc.stdin.write((json.dumps(tool_call) + "\n").encode())
        await proc.stdin.drain()
        print(await proc.stdout.readline())

    finally:
        # ✅ CLEAN SHUTDOWN (IMPORTANT)
        if proc.stdin:
            proc.stdin.close()

        await proc.wait()

asyncio.run(main())
