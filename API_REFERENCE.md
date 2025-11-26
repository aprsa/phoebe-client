# PHOEBE Client API Reference

Complete reference for all client methods and endpoints.

## Table of Contents

- [Session Management](#session-management)
- [PHOEBE Operations](#phoebe-operations)
- [Authentication](#authentication)

---

## Session Management

Methods for managing server-side PHOEBE sessions via `PhoebeClient` or `SessionAPI`.

### `start_session(metadata=None)`

Start a new PHOEBE session on the server.

**Parameters:**
- `metadata` (dict, optional): Optional metadata to attach to the session

**Returns:** `dict` with `session_id` and session details

**Example:**
```python
client = PhoebeClient()
session = client.start_session(metadata={'user': 'scientist1'})
print(session['session_id'])
```

**Server Endpoint:** `POST /dash/start-session`

---

### `end_session()`

End the current PHOEBE session and clean up server resources.

**Parameters:** None

**Returns:** `dict` with success status

**Example:**
```python
client.end_session()
```

**Server Endpoint:** `POST /dash/end-session/{session_id}`

---

### `set_session_id(session_id)`

Manually set the session ID (useful for reconnecting to existing sessions).

**Parameters:**
- `session_id` (str): The session identifier

**Returns:** None

**Example:**
```python
client.set_session_id('existing-session-123')
```

---

### `get_sessions()`

List all active sessions on the server.

**Parameters:** None

**Returns:** `dict` with list of active sessions

**Example:**
```python
sessions = client.get_sessions()
```

**Server Endpoint:** `GET /dash/sessions`

---

### `get_memory_usage()`

Query server memory usage statistics.

**Parameters:** None

**Returns:** `dict` with memory usage details

**Example:**
```python
memory = client.sessions.get_memory_usage()
```

**Server Endpoint:** `GET /dash/session-memory`

---

### `get_port_status()`

Check server port and connection status.

**Parameters:** None

**Returns:** `dict` with port status information

**Example:**
```python
status = client.sessions.get_port_status()
```

**Server Endpoint:** `GET /dash/port-status`

---

## PHOEBE Operations

Methods for interacting with PHOEBE Bundle parameters and computations.

### `attach_parameters(parameters)`

Attach multiple parameters to the Bundle at once.

**Parameters:**
- `parameters` (list[dict]): List of parameter dictionaries to attach

**Returns:** `dict` with operation result

**Example:**
```python
params = [
    {'qualifier': 'teff', 'component': 'primary', 'value': 6000},
    {'qualifier': 'requiv', 'component': 'primary', 'value': 1.0}
]
client.attach_parameters(params)
```

**Server Command:** `attach_parameters`

---

### `get_parameter(qualifier, **kwargs)`

Retrieve a parameter object from the Bundle.

**Parameters:**
- `qualifier` (str): Parameter qualifier (e.g., 'teff', 'period')
- `**kwargs`: Additional filters (context, component, kind, dataset, etc.)

**Returns:** `dict` with parameter details

**Example:**
```python
param = client.get_parameter('teff', component='primary', context='component')
```

**Server Command:** `get_parameter`

---

### `get_value(**kwargs)`

Get the value of a parameter.

**Parameters:**
- `**kwargs`: Parameter identifier - either `uniqueid` or full tag set (qualifier, context, component, etc.)

**Returns:** Parameter value (type varies: float, str, array, etc.)

**Example:**
```python
# By uniqueid
value = client.get_value(uniqueid='abc123')

# By tags
period = client.get_value(qualifier='period', context='component', component='binary')
```

**Server Command:** `get_value`

---

### `set_value(value, **kwargs)`

Set the value of a parameter.

**Parameters:**
- `value`: The new value to set
- `**kwargs`: Parameter identifier - either `uniqueid` or full tag set

**Returns:** `dict` with operation result

**Example:**
```python
# By uniqueid
client.set_value(6000, uniqueid='abc123')

# By tags
client.set_value(1.5, qualifier='period', component='binary', context='component')
```

**Server Command:** `set_value`

---

### `is_parameter_constrained(uniqueid)`

Check if a parameter is constrained.

**Parameters:**
- `uniqueid` (str): The unique identifier of the parameter

**Returns:** `dict` with constraint status

**Example:**
```python
result = client.is_parameter_constrained('abc123')
if result['constrained']:
    print(f"Constrained by: {result['constraint']}")
```

**Server Command:** `is_parameter_constrained`

---

### `update_uniqueid(twig)`

Update the uniqueid for a parameter (useful after Bundle modifications).

**Parameters:**
- `twig` (str): Parameter twig identifier

**Returns:** `dict` with updated uniqueid

**Example:**
```python
result = client.update_uniqueid('teff@primary')
new_id = result['uniqueid']
```

**Server Command:** `update_uniqueid`

---

### `add_dataset(**kwargs)`

Add a dataset to the Bundle.

**Parameters:**
- `**kwargs`: Dataset parameters (kind, dataset, passband, times, etc.)

**Returns:** `dict` with operation result

**Example:**
```python
client.add_dataset(
    kind='lc',
    dataset='lc01',
    passband='Johnson:V',
    times=[0, 0.1, 0.2]
)
```

**Server Command:** `add_dataset`

---

### `remove_dataset(dataset)`

Remove a dataset from the Bundle.

**Parameters:**
- `dataset` (str): Name of the dataset to remove

**Returns:** `dict` with operation result

**Example:**
```python
client.remove_dataset('lc01')
```

**Server Command:** `remove_dataset`

---

### `get_datasets()`

Retrieve list of all datasets in the Bundle.

**Parameters:** None

**Returns:** `dict` with datasets list

**Example:**
```python
datasets = client.get_datasets()
print(datasets['datasets'])
```

**Server Command:** `get_datasets`

---

### `run_compute(**kwargs)`

Execute a forward model computation.

**Parameters:**
- `**kwargs`: Compute options (compute, model, overwrite, etc.)

**Returns:** `dict` with computation results

**Example:**
```python
result = client.run_compute(compute='phoebe01', model='latest')
if result['success']:
    print("Computation successful")
```

**Server Command:** `run_compute`

---

### `run_solver(**kwargs)`

Execute a solver/optimizer (e.g., parameter estimation).

**Parameters:**
- `**kwargs`: Solver options (solver, solution, etc.)

**Returns:** `dict` with solver results

**Example:**
```python
result = client.run_solver(solver='optimizer.scipy')
```

**Server Command:** `run_solver`

---

### `get_bundle()`

Retrieve the current Bundle state.

**Parameters:** None

**Returns:** `dict` with Bundle representation

**Example:**
```python
bundle = client.get_bundle()
```

**Server Command:** `get_bundle`

---

### `load_bundle(bundle)`

Load a Bundle from a serialized string or file path.

**Parameters:**
- `bundle` (str): Serialized Bundle string or file path

**Returns:** `dict` with operation result

**Example:**
```python
with open('my_bundle.phoebe', 'r') as f:
    bundle_str = f.read()
client.load_bundle(bundle_str)
```

**Server Command:** `load_bundle`

---

### `save_bundle()`

Save the current Bundle state.

**Parameters:** None

**Returns:** `dict` with serialized Bundle string

**Example:**
```python
result = client.save_bundle()
if result['success']:
    with open('output.phoebe', 'w') as f:
        f.write(result['result']['bundle'])
```

**Server Command:** `save_bundle`

---

## Authentication

Optional authentication for multi-user scenarios.

### `set_jwt_token(token)`

Set JWT token for user identification (not authorization).

**Parameters:**
- `token` (str): JWT token string

**Returns:** None

**Note:** JWT is used for identification/auditing only. Authorization uses `X-API-Key` from config.

**Example:**
```python
client.sessions.set_jwt_token('eyJ0eXAi...')
client.phoebe.set_jwt_token('eyJ0eXAi...')
```

---

## Context Manager Usage

The client supports context manager protocol for automatic session management:

```python
with PhoebeClient(host='localhost', port=8001) as client:
    client.set_value(1.5, qualifier='period', component='binary')
    period = client.get_value(qualifier='period', component='binary')
    print(f"Period: {period}")
# Session automatically closed on exit
```

---

## Error Handling

All methods may raise:
- `SessionError`: Session management failures (connection, auth, etc.)
- `CommandError`: PHOEBE operation failures
- `ValueError`: Invalid parameters (e.g., missing session_id)

**Example:**
```python
from phoebe_client.exceptions import SessionError, CommandError

try:
    client.set_value(6000, qualifier='teff', component='primary')
except CommandError as e:
    print(f"Command failed: {e}")
except SessionError as e:
    print(f"Session error: {e}")
```

---

## Configuration

Server connection and authentication are configured via `config.toml`:

```toml
[server]
host = "localhost"
port = 8001
timeout = 30

[auth]
api_key = "your-api-key-here"
```

Constructor parameters override config file values:

```python
client = PhoebeClient(host='remote.server.com', port=8080)
```
