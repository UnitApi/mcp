# UnitMCP Architecture

This directory contains architectural documentation for the UnitMCP project.

## Overview

UnitMCP is designed with a modular, layered architecture that separates concerns and provides clear interfaces between components. The architecture is designed to be extensible, allowing for the addition of new hardware devices, communication protocols, and integration with various LLM systems.

## Architecture Diagrams

The `diagrams` directory contains visual representations of the UnitMCP architecture:

- [System Architecture](diagrams/architecture.svg) - High-level system architecture
- [Component Graph](diagrams/graph.svg) - Component dependencies and relationships
- [Project Structure](diagrams/project.svg) - Project directory structure and organization

## Component Descriptions

The `descriptions` directory contains detailed descriptions of key architectural components:

- [DSL Integration](descriptions/DSL_INTEGRATION.md) - Domain-Specific Language integration for hardware configuration

## Core Components

### Hardware Abstraction Layer

The Hardware Abstraction Layer (HAL) provides a unified interface for interacting with hardware devices, regardless of the underlying platform. This layer includes:

- Device interfaces
- Platform-specific implementations
- Device factories
- Mock implementations for testing

### Communication Layer

The Communication Layer handles communication between components and with external systems. This includes:

- HTTP/REST API
- WebSocket support
- Serial communication
- Bluetooth communication
- Inter-process communication

### Domain-Specific Language (DSL)

The DSL system provides a declarative way to configure and control hardware devices. This includes:

- YAML configuration parsing
- DSL to hardware mapping
- DSL execution engine
- DSL validation

### LLM Integration

The LLM Integration components provide integration with Large Language Models for natural language hardware control. This includes:

- Claude integration
- Ollama integration
- OpenAI integration
- Prompt management
- Response parsing

### Plugin System

The Plugin System allows for extending UnitMCP with custom functionality. This includes:

- Plugin interfaces
- Plugin discovery
- Plugin lifecycle management
- Plugin configuration

### Security Layer

The Security Layer provides security features for UnitMCP. This includes:

- Authentication
- Authorization
- Encryption
- Secure communication

## Design Principles

UnitMCP follows these key design principles:

1. **Modularity**: Components are designed to be modular and reusable
2. **Separation of Concerns**: Clear separation between different layers and components
3. **Extensibility**: Easy to extend with new hardware devices and functionality
4. **Testability**: Components are designed to be easily testable
5. **Configurability**: Highly configurable through DSL and configuration files
6. **Security**: Security is built into the architecture from the ground up

## Deployment Architecture

UnitMCP can be deployed in various configurations:

- **Standalone**: Running on a single device (e.g., Raspberry Pi)
- **Client-Server**: Running with a server component and multiple clients
- **Distributed**: Running across multiple devices in a distributed configuration
- **Cloud-Connected**: Running with cloud integration for remote control and monitoring

## Future Architecture

Planned architectural enhancements include:

- **Microservices Architecture**: Breaking down components into microservices
- **Event-Driven Architecture**: Moving to an event-driven architecture for better scalability
- **Edge Computing Support**: Enhanced support for edge computing deployments
- **Federated Learning**: Integration with federated learning for improved LLM performance
