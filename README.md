# Clue Access

Makes your life easier when programming analysis using Cluetooth data.

## Setup

### Connect to skateboard

You **must have** access to the `skateboard.sysnet.ucsd.edu` server.

Proxy jump from `trolley`, using the following configuration in your `~/.ssh/config` file:

```bash
Host trolley
  HostName trolley.sysnet.ucsd.edu
  User <trolley username>
  Port 222

Host skateboard
  HostName skateboard.sysnet.ucsd.edu
  User <skateboard username>
  ProxyJump trolley
  LocalForward 5432 localhost:5432 # Postgres
```

Then, connect to the server:

```bash
ssh skateboard
```

Or, use a one-liner:

```bash
ssh -J <trolley username>@trolley.sysnet.ucsd.edu:222 <skateboard username>@skateboard.sysnet.ucsd.edu -L 5432:localhost:5432
```

### Install the Python package (3.12+ required)

Install the package using `pip` (must be 3.12+)

```bash
pip install git+https://github.com/Microwave-WYB/clue_access.git
```

To check database connection, you can run in the command line:

```bash
clue_access
```

If you see the following output, you are good to go:

```bash
Successfully connected to the database
```

## Usage

Hello world example:

```python
from sqlmodel import select
from clue_access import QTDevice, run_in_session

statement = select(QTDevice).where(QTDevice.name == "QT 2013036").limit(100) # Select 100 QT devices with name "QT 2013036"
devices = run_in_session(lambda session: session.exec(statement).all()) # Execute the statement and get the result
for device in devices:
    print(device)
```

Or, equivalently:

```python
from sqlmodel import select, Session
from clue_access import QTDevice, run_in_session

def query(session: Session) -> list[QTDevice]:
    statement = select(QTDevice).where(QTDevice.name == "QT 2013036").limit(100) # Select 100 QT devices with name "QT 2013036"
    return list(session.exec(statement).all())

for device in run_in_session(query):
    print(device)
```

You may also use the classical `with` statement:

```python
from sqlmodel import select, Session
from clue_access import QTDevice, get_engine

with Session(get_engine()) as session:
    statement = select(QTDevice).where(QTDevice.name == "QT 2013036").limit(100) # Select 100 QT devices with name "QT 2013036"
    devices = list(session.exec(statement).all())
    for device in devices:
        print(device)
```

Refer to [SQLModel](https://sqlmodel.tiangolo.com/) for documentation on how to use the SQLModel package.

Ask your favorite LLM for help if you need it.

You can find example notebook in [demo.ipynb](/demo.ipynb).
