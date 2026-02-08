from mcp.server.fastmcp import FastMCP

# ----------------------------------
# MCP Server (ASYNC)
# ----------------------------------
mcp = FastMCP("calculator-mcp-async")

# ----------------------------------
# ADD
# ----------------------------------
@mcp.tool()
async def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


# ----------------------------------
# SUBTRACT
# ----------------------------------
@mcp.tool()
async def sub(a: int, b: int) -> int:
    """Subtract b from a"""
    return a - b


# ----------------------------------
# MULTIPLY
# ----------------------------------
@mcp.tool()
async def mul(a: int, b: int) -> int:
    """Multiply two numbers"""
    return a * b


# ----------------------------------
# DIVIDE
# ----------------------------------
@mcp.tool()
async def div(a: int, b: int) -> int:
    """Integer division of a by b"""
    if b == 0:
        raise ValueError("Division by zero is not allowed")
    return a // b


# ----------------------------------
# MODULUS
# ----------------------------------
@mcp.tool()
async def mod(a: int, b: int) -> int:
    """Modulus of a by b"""
    if b == 0:
        raise ValueError("Modulo by zero is not allowed")
    return a % b


# ----------------------------------
# ENTRYPOINT (STDIO – OFFLINE)
# ----------------------------------
if __name__ == "__main__":
    mcp.run()
