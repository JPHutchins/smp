# Simple Management Protocol (SMP)

`smp` implements serialization and deserialization of the Simple Management Protocol.

The SMP specification can be found [here](https://docs.zephyrproject.org/latest/services/device_mgmt/smp_protocol.html).

If you'd like a library that implements the **serial (UART or USB)**, **Bluetooth (BLE)**, and
**UDP** transport layers for SMP, take a look at
[smpclient](https://github.com/intercreate/smpclient).

If you need an SMP CLI application to interact with device firmware, then try
[smpmgr](https://github.com/intercreate/smpmgr).

## Install

`smp` is [distributed by PyPI](https://pypi.org/project/smp/) and can be installed with `uv`, `pip`, and other dependency managers.

## User Documentation

Documentation is in the source code so that it is available to your editor.
An online version is generated and available [here](https://jphutchins.github.io/smp/).

## Development Quickstart

> Assumes that you've already [setup your development environment](#development-environment-setup).

Tasks are defined in [`tasks.py`](tasks.py) and run with [camas](https://github.com/JPHutchins/camas).

1. run `uv sync` when pulling in new changes
2. run `uv run camas fix` to auto-format and apply lint fixes
3. run `uv run camas` to run the default checks
4. run `uv run camas matrix` to check against all supported Python versions
5. add library dependencies with `uv`:
   ```
   uv add <my_new_dependency>
   ```
6. add development dependencies:
   ```
   uv add --group dev <my_dev_dependency>
   ```

## Development Environment Setup

### Install Dependencies

- uv: https://docs.astral.sh/uv/getting-started/installation/

### Create the venv

```
uv sync
```

### Verify Your Setup

```
uv run camas
```

### Enable the githooks

```
git config core.hooksPath .githooks
```
