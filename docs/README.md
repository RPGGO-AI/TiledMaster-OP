# TiledMaster Documentation

Welcome to the TiledMaster documentation! This documentation provides detailed guides and references for the TiledMaster framework.

## Project Origins and Vision

TiledMaster emerged from our exploration of procedural Tiled map generation and LLM Agent content creation. During this process, we identified a significant gap in the industry – the lack of a comprehensive Python framework that would allow developers to focus on core artistic assets and algorithms without getting bogged down in the intricacies of the Tiled format.

This project aims to provide students and developers who want to conduct algorithm research and development using Tiled and Python with a tool to quickly implement and validate their algorithmic ideas. We believe that by simplifying technical barriers, more innovative map generation methods will become possible.

Our long-term goal is to build a Model Context Protocol (MCP) project for Tiled maps. While there is still significant work ahead, we have already taken important first steps toward this vision.

## Documentation Directory

### Quick Start

- [Quick Implementation Guide](quick_implementation_guide.md) - Get started quickly with implementing your own custom map generator

### Core Concepts

- [Core Concepts Guide](core_concepts.md) - Detailed explanation of TiledMaster framework's core components and design philosophy

### Reference Manuals

- [API Reference](api_reference.md) - Detailed reference for the framework's APIs and methods

## Framework Introduction

TiledMaster is a flexible tile-based map generation framework designed for procedural map generation. It provides a component-based, element-driven approach to create various types of maps.

Key features include:

- **Element-Driven Design**: Splits map generation into independent elements, each responsible for a specific part of the map
- **Automatic Resource Management**: Simplifies resource loading and processing
- **Highly Customizable**: Create various types of maps by combining different elements
- **Standard Format Export**: Generates maps compatible with the Tiled editor
- **Built-in Algorithm Tools**: Provides noise maps, pathfinding, and other algorithmic tools
- **LLM Agent Friendly**: Designed with consideration for collaboration with large language model agents, making AI-assisted map generation simpler

## How to Use This Documentation

- New users should first read the [Quick Implementation Guide](quick_implementation_guide.md) to understand the basic usage of the framework
- Users who want to understand the framework design in depth should read the [Core Concepts Guide](core_concepts.md)
- Users who need to look up specific APIs can refer to the [API Reference](api_reference.md)

## Examples and Tutorials

Complete example implementations can be found in the `implement` directory of the project:

- `town_impl` - Town map generation example
- `room_impl` - Room map generation example

## Contributing

We welcome community contributions, whether improving documentation, adding new features, optimizing existing algorithms, or sharing map generation cases created using TiledMaster. Please check the CONTRIBUTING.md file to learn how to participate.

## License

TiledMaster is licensed under the MIT License. See the LICENSE file in the project root directory for details. 