# register is called from server.main, so import here is enough
from . import (
    mount_file,  # noqa: F401
    persist_artifact,  # noqa: F401
    workspace_inspect,  # noqa: F401
)
