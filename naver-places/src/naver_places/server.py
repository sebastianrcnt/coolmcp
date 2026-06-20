from fastmcp import FastMCP

mcp = FastMCP("naver-places")


@mcp.tool
def hello(name: str) -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"


@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


if __name__ == "__main__":
    mcp.run()
