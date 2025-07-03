"""Authentication context for PRIMS server.

This module handles user context passed from an authentication proxy
via HTTP headers. PRIMS itself doesn't handle authentication - that's
delegated to the reverse proxy/gateway layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from starlette.requests import Request


@dataclass
class AuthContext:
    """User authentication context passed from auth proxy."""
    
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    session_id: Optional[str] = None
    permissions: list[str] = field(default_factory=list)
    
    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.user_id is not None
    
    def can_execute_code(self) -> bool:
        """Check if user has code execution permission."""
        return "code:execute" in self.permissions
    
    def can_access_session(self, session_id: str) -> bool:
        """Check if user can access a specific session."""
        # Users can only access their own sessions
        return self.session_id == session_id or f"session:{session_id}" in self.permissions


def extract_auth_context(request: Request) -> AuthContext:
    """Extract authentication context from request headers.
    
    Expected headers set by auth proxy:
    - X-User-ID: Authenticated user identifier
    - X-Organization-ID: User's organization
    - X-Session-ID: Current session identifier  
    - X-User-Permissions: Comma-separated permissions
    """
    permissions_header = request.headers.get("x-user-permissions", "")
    permissions = [p.strip() for p in permissions_header.split(",") if p.strip()]
    
    return AuthContext(
        user_id=request.headers.get("x-user-id"),
        organization_id=request.headers.get("x-organization-id"),
        session_id=request.headers.get("x-session-id"),
        permissions=permissions,
    )


def require_auth(context: AuthContext) -> None:
    """Raise exception if user is not authenticated."""
    if not context.is_authenticated:
        raise PermissionError("Authentication required")


def require_permission(context: AuthContext, permission: str) -> None:
    """Raise exception if user lacks required permission."""
    require_auth(context)
    if permission not in context.permissions:
        raise PermissionError(f"Permission required: {permission}")