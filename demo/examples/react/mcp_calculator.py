from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Math", port=8001)


@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers"""
    return a + b


@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers"""
    return a * b


@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide two numbers"""
    return a / b


if __name__ == "__main__":
    mcp.run(transport="stdio")
