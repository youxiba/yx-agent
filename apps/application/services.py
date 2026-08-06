from apps.identity.services import ApiKeyService


def create_mcp_api_key(app) -> dict:
    """为应用生成/刷新 MCP 专用 app-key（明文只返回一次）"""
    if app.api_key:
        app.api_key.delete()
    created = ApiKeyService.create(app.user, f"mcp-{app.name}", "application")
    app.api_key_id = created["id"]
    app.save(update_fields=["api_key"])
    return created