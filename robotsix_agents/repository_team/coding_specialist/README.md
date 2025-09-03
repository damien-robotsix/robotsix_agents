# Coding Specialist Agent

A comprehensive Coding Specialist agent that combines filesystem R/W capabilities with advanced coding expertise and solution validation before implementation.

## Overview

The Coding Specialist agent provides AI assistants with advanced programming capabilities and comprehensive filesystem operations. It leverages the Model Context Protocol (MCP) to communicate with the `mcp/filesystem` Docker container for file operations, while adding expert-level coding knowledge, solution validation, and software engineering best practices.

## Key Features

### Coding Expertise
- **Multi-language Programming**: Expert knowledge in Python, JavaScript/TypeScript, Java, Go, Rust, C++, C#, PHP, Ruby, Swift, Kotlin, Dart, and more
- **Framework Proficiency**: React, Vue.js, Angular, Node.js, Express.js, FastAPI, Django, Flask, Spring Boot, .NET Core, Laravel, Ruby on Rails
- **Solution Validation**: Mandatory validation process before any implementation to ensure quality and safety
- **Code Analysis**: Static analysis, security scanning, performance optimization suggestions
- **Best Practices**: Design patterns, refactoring recommendations, and architectural guidance

### Solution Validation Process
Before implementing any solution, the agent performs:
1. **Requirements Analysis**: Thorough understanding of problem requirements and constraints
2. **Architecture Review**: Evaluation of proposed solution approach and design
3. **Quality Validation**: Code quality, security, and best practices assessment
4. **Risk Assessment**: Identification of potential issues, edge cases, and dependencies
5. **Compatibility Check**: Backward compatibility and testing considerations
6. **Implementation Plan**: Clear summary and approval before proceeding

## Filesystem Capabilities

The Coding Specialist agent retains all filesystem operations from the original filesystem agent, including:

### File Operations
- `read_text_file`: Read complete contents of files as text with optional head/tail line limits
- `read_media_file`: Read image or audio files and return base64 data with MIME type
- `read_multiple_files`: Read multiple files simultaneously with batch processing
- `write_file`: Create new files or overwrite existing ones (with caution)
- `edit_file`: Make selective edits using advanced pattern matching and formatting with dry-run support

### Directory Operations
- `create_directory`: Create new directories with automatic parent directory creation
- `list_directory`: List directory contents with [FILE] or [DIR] prefixes
- `list_directory_with_sizes`: List directory contents with file sizes and sorting options
- `directory_tree`: Get recursive JSON tree structure of directory contents
- `move_file`: Move or rename files and directories

### Search & Discovery
- `search_files`: Recursively search for files/directories using glob patterns with exclude filters
- `get_file_info`: Get detailed file/directory metadata (size, timestamps, permissions)

### Access Control
- `list_allowed_directories`: View all directories the agent can access
- Dynamic directory access control via MCP Roots protocol

## Prerequisites

Before using the Coding Specialist agent, you need to have the required dependencies:

1. **Docker**: Ensure Docker is installed and running on your system

2. **Filesystem MCP Server**: The agent uses the `mcp/filesystem` Docker container for file operations. This container will be automatically pulled when the agent starts.

## Configuration

The Coding Specialist agent can be configured in two ways:

### 1. Global Configuration (coding_specialist.yaml)

The Coding Specialist agent can be configured using the `coding_specialist.yaml` configuration file in the `agent_defaults` directory:

```yaml
# Default allowed directories (can be overridden at runtime)
allowed_directories:
  - "."  # Current working directory

# MCP server configuration
mcp_server:
  command: "docker"
  args: []
  read_timeout_seconds: 120

# Agent behavior settings
reflect_on_tool_use: true
model_client_stream: true

# Security settings
confirm_destructive_operations: true

# File operation limits
max_file_size_mb: 100
max_files_per_operation: 50
```

### 2. Participant Configuration (Recommended)

When using the coding specialist agent as a participant in an orchestrator, you can specify allowed directories directly in the participants list:

```yaml
participants:
  - interaction_memory
  - calendar
  - github
  - coding_specialist[/path/to/allowed/directory1,/path/to/allowed/directory2]
```

This approach is recommended because:
- The allowed directories are determined when adding the agent as a participant
- No global configuration is needed for directory access
- Different orchestrator configurations can use different directory sets
- More flexible and explicit about which directories to access

## Usage

### Creating a Coding Specialist Agent

```python
from robotsix_agents.repository_team.filesystem import create_agent

# Create a Coding Specialist agent (uses current directory)
coding_agent = create_agent()

# Create a Coding Specialist agent for specific working directory
coding_agent = create_agent(working_directory="/path/to/project")
```

### Basic Example

```python
from robotsix_agents.repository_team.filesystem import create_agent

def main():
    # Create the Coding Specialist agent for a project directory
    agent = create_agent(working_directory="/home/user/projects/myapp")
    
    # Use the agent to analyze and improve code
    result = agent.run(
        task="Analyze the main.py file and suggest improvements"
    )
    print(result.messages[-1])

if __name__ == "__main__":
    main()
```

### Usage with Orchestrator

When using the coding specialist agent with an orchestrator, specify the directories in the participant configuration:

```yaml
# config.yaml
agents:
  orchestrator:
    participants:
      - interaction_memory
      - calendar
      - github
      - coding_specialist[/home/projects/robotsix_agents_ws,/home/documents]
```

This automatically passes the allowed directories to the coding specialist agent when it's created as a participant.

## Safety Features

The Coding Specialist agent includes several safety features:

1. **Directory Access Control**: Operations are restricted to explicitly allowed directories only.

2. **Confirmation for Destructive Operations**: The agent will ask for confirmation before performing potentially dangerous operations like overwriting important files.

3. **File Size Limits**: Configurable limits on file sizes and batch operation counts to prevent resource exhaustion.

4. **Dry Run Support**: The `edit_file` tool supports dry-run mode to preview changes before applying them.

5. **Comprehensive Error Handling**: Clear error messages and fallback options when operations fail.

6. **Logging**: Detailed logging of filesystem operations for debugging and auditing.

## Directory Access Control

The Coding Specialist agent uses a flexible directory access control system:

### Method 1: Command-line Arguments (Default)
Directories are specified when creating the agent and passed to the MCP server.

### Method 2: MCP Roots Protocol (Advanced)
For MCP clients that support the Roots protocol, directories can be dynamically updated at runtime without server restart.

**Important**: The agent requires at least one allowed directory to operate. Use the `list_allowed_directories` tool to see current accessible directories.

## Architecture

The Coding Specialist agent follows the robotsix_agents pattern:

- `agent.py`: Main agent implementation with MCP workbench integration and coding expertise
- `__init__.py`: Module exports
- `coding_specialist.yaml`: Default configuration file
- `README.md`: This documentation

The agent uses the `McpWorkbench` from `autogen_ext.tools.mcp` to communicate with the filesystem MCP server via the Model Context Protocol, while providing advanced coding capabilities and solution validation.

## Troubleshooting

### "docker: command not found" or Docker connection errors

This error occurs when Docker is not installed or not running. Ensure:
1. Docker is installed and running on your system
2. Your user has permission to run Docker commands
3. The `mcp/filesystem` Docker image can be pulled from the registry

### "Permission denied" on file operations

This error occurs when the agent doesn't have permission to access the requested files/directories. Ensure:
1. The directories are included in the allowed_directories list
2. Your user has the necessary filesystem permissions
3. The paths exist and are accessible

### "No allowed directories specified"

This error occurs when the agent is created without any allowed directories. Either:
1. Specify directories in the agent configuration
2. Pass allowed_directories when creating the agent
3. Configure the participant with directory parameters

### File size or operation limits exceeded

If you encounter limits on file operations:
1. Check the `max_file_size_mb` setting in the configuration
2. Verify the `max_files_per_operation` limit
3. Adjust these settings in your filesystem.yaml configuration

## Development

To test the Coding Specialist agent implementation:

```bash
cd /path/to/robotsix_agents_ws
python test_coding_specialist_agent.py
```

This will verify that the MCP connection works, the filesystem MCP server is properly configured, and the coding specialist capabilities are functional.

## Example Operations

### Code Analysis and Review
```python
# Analyze code quality and suggest improvements
result = agent.run(task="Analyze the main.py file and suggest performance optimizations")

# Review security vulnerabilities
result = agent.run(task="Review the authentication.py module for security issues")

# Validate solution before implementation
result = agent.run(task="I want to add a user authentication system. Please validate the approach before implementation.")
```

### Code Implementation with Validation
```python
# Implement new feature with validation
result = agent.run(task="Create a REST API endpoint for user registration with proper validation")

# Refactor existing code
result = agent.run(task="Refactor the database connection code to use connection pooling")

# Fix bugs with analysis
result = agent.run(task="Debug and fix the memory leak in the data processing module")
```

### Filesystem Operations for Code Management
```python
# Analyze project structure
result = agent.run(task="Analyze the project structure and suggest improvements")

# Search for code patterns
result = agent.run(task="Find all Python files with deprecated function usage")

# Create development environment
result = agent.run(task="Set up a proper project structure with tests and documentation")