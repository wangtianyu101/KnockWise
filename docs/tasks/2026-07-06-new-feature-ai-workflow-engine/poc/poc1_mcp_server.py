"""POC-1: MCP server 最小 demo

目标：验证能用 10 行代码跑通 MCP server，含 1 个 tool
通过标准：stdio 能被 MCP client (Claude Code / mcp-cli) 调用
"""
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

app = Server("poc-workflow")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="ping",
            description="最简单的 echo 工具，验证 MCP 协议",
            inputSchema={
                "type": "object",
                "properties": {"message": {"type": "string"}},
                "required": ["message"],
            },
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "ping":
        return [TextContent(type="text", text=f"pong: {arguments.get('message', '')}")]
    raise ValueError(f"Unknown tool: {name}")


async def main():
    async with stdio_server() as (read, write):
        await app.run(read, write, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
