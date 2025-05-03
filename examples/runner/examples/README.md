# UnitMCP Git Runner Examples

This directory contains examples demonstrating how to use the UnitMCP Git Runner to clone, configure, and run applications from Git repositories.

## Available Examples

### run_git_example.py

This example demonstrates how to use the Git Runner to clone and run applications from Git repositories.

#### Usage

Run a simple example (static HTML site):
```bash
python run_git_example.py --example simple
```

Run an example with UnitMCP integration:
```bash
python run_git_example.py --example unitmcp
```

## Creating Your Own Examples

You can create your own examples by following these steps:

1. Import the Git Runner and/or Git Runner Integration:
```python
from examples.runner.git_runner import GitRunner
from examples.runner.git_runner_integration import GitRunnerIntegration
```

2. Create and run the Git Runner:
```python
runner = GitRunner(
    git_url="https://github.com/username/repo.git",
    target_dir="/path/to/directory",
    branch="main",
    interactive=True,
    auto_start=True,
    log_level="INFO"
)

exit_code = await runner.run()
```

3. Or create and run the Git Runner Integration:
```python
integration = GitRunnerIntegration(
    git_url="https://github.com/username/repo.git",
    target_dir="/path/to/directory",
    branch="main",
    interactive=True,
    auto_start=True,
    log_level="INFO",
    server_host="localhost",
    server_port=8888,
    mode="both",
    simulation=False
)

exit_code = await integration.run()
```

## Additional Resources

For more information about the UnitMCP Git Runner, see the [Git Runner Documentation](../README_GIT_RUNNER.md).
