# Test fixtures

`code-conductor-contracts.schema.json` is a snapshot of
[`packages/schemas/schema/contracts.schema.json`](https://github.com/saulpatinojr/Proj-Code_Conductor/blob/main/packages/schemas/schema/contracts.schema.json)
from the sibling Code Conductor repository (Apache-2.0, same owner).

`workflow.py export` must produce documents that validate against it. That is the
shared contract (Code Conductor ADR 0011). Refresh this snapshot whenever Code
Conductor changes the schema, then rerun the test suite.
