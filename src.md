mcp-hardware/
├── pyproject.toml
├── setup.py
├── README.md
├── LICENSE
├── requirements.txt
├── .gitignore
├── build.sh
│
├── examples/
│   ├── __init__.py
│   ├── ollama_integration.py
│   ├── rpi_control.py
│   ├── voice_assistant.py
│   ├── shell_cli_demo.py
│   ├── pipeline_demo.py
│   └── integrated_demo.py
│
├── src/
│   └── unitmcp/
│       ├── __init__.py
│       │
│       ├── client/
│       │   ├── __init__.py
│       │   ├── client.py
│       │   └── shell.py
│       │
│       ├── server/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── gpio.py
│       │   ├── input.py
│       │   ├── audio.py
│       │   └── camera.py
│       │
│       ├── pipeline/
│       │   ├── __init__.py
│       │   └── pipeline.py
│       │
│       ├── protocols/
│       │   ├── __init__.py
│       │   └── mcp.py
│       │
│       ├── security/
│       │   ├── __init__.py
│       │   └── permissions.py
│       │
│       └── utils/
│           ├── __init__.py
│           └── logger.py
│
└── tests/
    ├── __init__.py
    ├── test_server.py
    └── test_client.py
