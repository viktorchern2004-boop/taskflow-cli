"""MCP stdio server for TaskFlow Obsidian knowledge base."""
from mcp.server.mcpserver import MCPServer
from mcp_vault.vault import get_note as read_note
from mcp_vault.vault import ingest_note as write_note
from mcp_vault.vault import search_notes as find_notes

mcp = MCPServer("taskflow-vault")

@mcp.tool()
def get_note(title: str) -> dict:
    """Read one vault note by its unique title."""
    return read_note(title)

@mcp.tool()
def search_notes(query: str, limit: int = 5) -> list[dict]:
    """Search vault notes. Semantic retrieval will replace the internals in PR7."""
    return find_notes(query, limit)

@mcp.tool()
def ingest_note(title: str, type: str, content: str, links: list[str] | None = None) -> dict:
    """Create or update an MCP-owned note in the vault's feature branch."""
    return write_note(title, type, content, links)

if __name__ == "__main__":
    mcp.run(transport="stdio")
