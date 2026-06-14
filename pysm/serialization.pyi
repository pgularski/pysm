from typing import Any, Dict, Optional

from .pysm import StateMachine

SNAPSHOT_VERSION: int

def snapshot(machine: StateMachine,
             metadata: Optional[Any] = ...) -> Dict[str, Any]: ...
def restore(machine: StateMachine, data: Dict[str, Any]) -> StateMachine: ...
