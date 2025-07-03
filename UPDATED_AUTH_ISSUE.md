# Authentication Support via Proxy Integration

## Issue Summary

**Goal**: Enable secure, authenticated access to PRIMS while maintaining its core design principle of "one tool, one job."

**Approach**: Implement minimal authentication context support in PRIMS, with comprehensive documentation and examples for deploying behind authentication proxies/gateways.

## Problem Statement

Currently, PRIMS has **no authentication mechanism**, making it unsuitable for production deployments where:
- Multiple users need isolated access
- Organizations require access control and audit trails  
- Rate limiting and quotas are necessary
- Compliance requires authenticated API access

## Design Philosophy

PRIMS should **NOT implement authentication directly** because:

1. **Single Responsibility**: PRIMS excels at secure Python code execution - that's its job
2. **Avoid Bloat**: Authentication logic would complicate the codebase unnecessarily
3. **Industry Standards**: Authentication proxies are the proven pattern for microservices
4. **Flexibility**: Users can choose their preferred auth providers (OAuth, SAML, API keys)
5. **Reusability**: Same auth infrastructure can protect multiple services

## Proposed Solution

### Phase 1: Header-Based User Context (PRIMS Changes)

Add minimal support for reading user context from HTTP headers set by authentication proxies:

```python
# New: server/auth_context.py
@dataclass
class AuthContext:
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    session_id: Optional[str] = None
    permissions: list[str] = field(default_factory=list)

def extract_auth_context(request: Request) -> AuthContext:
    """Extract user context from proxy-set headers."""
    return AuthContext(
        user_id=request.headers.get("x-user-id"),
        organization_id=request.headers.get("x-organization-id"), 
        session_id=request.headers.get("x-session-id"),
        permissions=request.headers.get("x-user-permissions", "").split(",")
    )
```

### Phase 2: Update Tools for User Isolation

Modify MCP tools to use authentication context:

```python
# Updated: server/tools/run_code.py
@mcp.tool
async def run_code(code: str, requirements: list[str] = None, files: list[dict] = None, session_id: str = None):
    """Execute Python code with user authentication context."""
    # Extract user context from request headers
    auth_context = extract_auth_context_from_request()
    
    # Basic permission check
    if auth_context.user_id and "code:execute" not in auth_context.permissions:
        raise PermissionError("Code execution not permitted")
    
    # User-isolated session management
    user_session_id = f"{auth_context.user_id}_{session_id}" if auth_context.user_id else session_id
    
    return await run_code_impl(code, requirements, files, user_session_id)
```

### Phase 3: Authentication Proxy Examples

Provide comprehensive documentation and examples for common authentication patterns:

#### Example 1: Nginx + API Key Auth
```nginx
server {
    listen 443 ssl;
    server_name prims.company.com;
    
    location / {
        # Validate API key
        auth_request /auth;
        
        # Extract user context from auth service response
        auth_request_set $user_id $upstream_http_x_user_id;
        auth_request_set $permissions $upstream_http_x_permissions;
        
        # Forward to PRIMS with user headers
        proxy_pass http://prims:9000;
        proxy_set_header X-User-ID $user_id;
        proxy_set_header X-User-Permissions $permissions;
        proxy_set_header X-Session-ID $user_id;
    }
    
    location = /auth {
        internal;
        proxy_pass http://auth-service:8080/validate;
        proxy_set_header Authorization $http_authorization;
    }
}
```

#### Example 2: Docker Compose + OAuth2 Proxy
```yaml
version: '3.8'
services:
  oauth2-proxy:
    image: quay.io/oauth2-proxy/oauth2-proxy:latest
    environment:
      - OAUTH2_PROXY_UPSTREAM=http://prims:9000
      - OAUTH2_PROXY_CLIENT_ID=${GOOGLE_CLIENT_ID}
      - OAUTH2_PROXY_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
      - OAUTH2_PROXY_EMAIL_DOMAINS=company.com
      - OAUTH2_PROXY_SET_XAUTHREQUEST=true
    ports:
      - "4180:4180"
    
  prims:
    build: .
    environment:
      - PRIMCS_AUTH_ENABLED=true
    expose:
      - "9000"
```

#### Example 3: Kubernetes + Istio
```yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: prims-auth
spec:
  selector:
    matchLabels:
      app: prims
  rules:
  - when:
    - key: request.headers[authorization]
      values: ["Bearer *"]
```

#### Example 4: AWS API Gateway + Cognito
```yaml
Resources:
  PrimsApi:
    Type: AWS::ApiGateway::RestApi
    Properties:
      Name: PRIMS-API
      
  PrimsAuthorizer:
    Type: AWS::ApiGateway::Authorizer
    Properties:
      Type: COGNITO_USER_POOLS
      ProviderARNs:
        - !GetAtt UserPool.Arn
```

## Implementation Checklist

### PRIMS Core Changes (Minimal)
- [ ] Add `server/auth_context.py` module
- [ ] Update `server/main.py` artifact endpoint for user isolation
- [ ] Modify `server/tools/run_code.py` to use auth context
- [ ] Update `server/tools/workspace_inspect.py` for user sessions
- [ ] Add user-based session isolation to sandbox runner
- [ ] Implement basic permission checking framework

### Documentation & Examples
- [ ] Create `docs/authentication.md` guide
- [ ] Add `examples/nginx-auth/` configuration
- [ ] Add `examples/oauth2-proxy/` Docker setup
- [ ] Add `examples/kubernetes-auth/` manifests  
- [ ] Add `examples/aws-api-gateway/` CloudFormation
- [ ] Create authentication troubleshooting guide
- [ ] Update main README with security considerations

### Testing
- [ ] Unit tests for auth context extraction
- [ ] Integration tests with mock auth headers
- [ ] Example proxy configurations validation
- [ ] Security testing for header injection prevention

## Security Considerations

### What PRIMS Will Handle
- ✅ Extract user context from trusted proxy headers
- ✅ Basic permission validation (`code:execute`, etc.)
- ✅ User session isolation
- ✅ Prevent cross-user artifact access

### What Authentication Proxy Handles
- 🔐 Token/credential validation
- 🔐 OAuth flows and redirects
- 🔐 Rate limiting and quotas
- 🔐 Audit logging and monitoring
- 🔐 Session management
- 🔐 Multi-factor authentication

## Benefits of This Approach

1. **PRIMS Stays Simple**: Core codebase focused on Python execution
2. **Maximum Flexibility**: Users choose their preferred auth solution
3. **Industry Standard**: Follows microservices best practices
4. **Better Security**: Specialized auth components vs. custom implementation
5. **Easier Operations**: Independent scaling and updates
6. **Reduced Risk**: Less attack surface in PRIMS itself

## Expected Code Changes

- **New files**: `server/auth_context.py`, documentation, examples
- **Modified files**: 4-5 existing modules for header reading
- **Total LOC added**: ~200 lines in PRIMS core + comprehensive docs
- **Authentication logic**: 0 lines (handled by proxy)

## Timeline

- **Week 1**: Core auth context support in PRIMS
- **Week 2**: Documentation and basic examples (nginx, docker)
- **Week 3**: Advanced examples (k8s, cloud) and testing
- **Week 4**: Security review and final documentation

## Success Criteria

- [ ] PRIMS can extract user context from standard headers
- [ ] User sessions are properly isolated
- [ ] At least 3 working authentication proxy examples
- [ ] Zero authentication logic in PRIMS codebase
- [ ] Production deployment guide completed
- [ ] Security review passed

---

**Priority**: High (Required for production use)
**Effort**: Medium (1 month)
**Dependencies**: None
**Breaking Changes**: None (additive only)