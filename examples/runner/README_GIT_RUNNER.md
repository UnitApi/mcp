# UnitMCP Git Runner

UnitMCP Git Runner is an extension to the UnitMCP Runner that allows you to clone, configure, and run applications directly from Git repositories. It supports various application types including shell scripts, Node.js, Python, PHP, and static HTML.

## Features

- **Git Repository Integration**: Clone and run applications directly from Git repositories
- **Automatic Application Type Detection**: Automatically detect the type of application in the repository
- **Dependency Installation**: Install dependencies for different application types
- **Environment Variable Configuration**: Configure environment variables from .env files or interactively
- **Intelligent Log Analysis**: Monitor logs and provide intelligent suggestions for troubleshooting
- **UnitMCP Integration**: Seamlessly integrate with UnitMCP for client-server applications
- **CI/CD System Detection**: Detect and use CI/CD configurations from GitHub, GitLab, etc.

## Usage

### Basic Usage

```bash
# Clone and run a Git repository
python git_runner.py https://github.com/username/repo.git

# Clone a specific branch
python git_runner.py https://github.com/username/repo.git --branch develop

# Clone to a specific directory
python git_runner.py https://github.com/username/repo.git --target-dir /path/to/directory

# Run in non-interactive mode
python git_runner.py https://github.com/username/repo.git --non-interactive

# Set log level
python git_runner.py https://github.com/username/repo.git --log-level DEBUG
```

### UnitMCP Integration

```bash
# Run with UnitMCP integration
python git_runner_integration.py https://github.com/username/repo.git

# Specify server host and port
python git_runner_integration.py https://github.com/username/repo.git --server-host localhost --server-port 8888

# Run only the server or client
python git_runner_integration.py https://github.com/username/repo.git --mode server
python git_runner_integration.py https://github.com/username/repo.git --mode client

# Run in simulation mode
python git_runner_integration.py https://github.com/username/repo.git --simulation
```

## Supported Application Types

### Node.js

The Git Runner can detect and run Node.js applications. It will:

1. Detect the application based on the presence of `package.json`, `yarn.lock`, or `.js` files
2. Install dependencies using npm, yarn, or pnpm
3. Run the application using the start script in package.json or by finding a common entry point

### Python

The Git Runner can detect and run Python applications. It will:

1. Detect the application based on the presence of `requirements.txt`, `setup.py`, `pyproject.toml`, or `.py` files
2. Create a virtual environment and install dependencies
3. Run the application by finding a common entry point or using framework-specific commands (Flask, Django)

### PHP

The Git Runner can detect and run PHP applications. It will:

1. Detect the application based on the presence of `composer.json` or `.php` files
2. Install dependencies using Composer
3. Run the application using the PHP built-in server or framework-specific commands (Laravel, Symfony)

### Shell Scripts

The Git Runner can detect and run shell script applications. It will:

1. Detect the application based on the presence of `.sh` files
2. Make scripts executable
3. Run the application by finding a common entry point

### Static HTML

The Git Runner can detect and run static HTML applications. It will:

1. Detect the application based on the presence of `index.html` or `.html` files
2. Run the application using a simple HTTP server

## Environment Variables

The Git Runner can load environment variables from `.env` files or prompt the user to enter them interactively. If a `.env.example` file is found, it will use it as a template for the environment variables.

## Log Analysis

The Git Runner monitors the application logs and provides intelligent suggestions for troubleshooting common issues, such as:

- Missing dependencies
- Port conflicts
- Permission issues
- File not found errors
- Database connection issues

## UnitMCP Integration

The Git Runner can integrate with UnitMCP to run client-server applications. It will:

1. Detect UnitMCP configuration in the repository
2. Create a UnitMCP runner with the appropriate configuration
3. Run the application with UnitMCP functionality

## Examples

### Running a Node.js Application

```bash
python git_runner.py https://github.com/username/nodejs-app.git
```

This will:
1. Clone the repository
2. Detect that it's a Node.js application
3. Install dependencies using npm
4. Run the application using the start script in package.json

### Running a Python Application with UnitMCP

```bash
python git_runner_integration.py https://github.com/username/python-app.git
```

This will:
1. Clone the repository
2. Detect that it's a Python application
3. Install dependencies using pip
4. Detect UnitMCP configuration
5. Run the application with UnitMCP functionality

### Running a PHP Application in Simulation Mode

```bash
python git_runner.py https://github.com/username/php-app.git --simulation
```

This will:
1. Clone the repository
2. Detect that it's a PHP application
3. Install dependencies using Composer
4. Run the application in simulation mode

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
