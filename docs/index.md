# lockpy

`lockpy` is a Python library for acquiring and releasing distributed locks using DynamoDB.

## Features

- Implemented using `asyncio`
- Can be used as an `asyncio` context manager
- Supports Python versions 3.9 to 3.13

## Installation

Coming soon to PyPI!

## Usage

```python
import asyncio
from lockpy import Lock

async def main():
    async with Lock("my-resource"):
        # critical section
        pass

asyncio.run(main())
```