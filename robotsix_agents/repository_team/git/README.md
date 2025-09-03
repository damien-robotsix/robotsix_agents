# Git Agent

A comprehensive Git agent that uses a Docker-based MCP Git server to interact with local Git repositories programmatically.

## Overview

The Git agent provides AI assistants with the ability to perform comprehensive Git operations on local repositories. It leverages the Model Context Protocol (MCP) to communicate with a containerized git MCP server (`mcp/git`), which exposes Git functionality through a standardized interface.

## Features

The Git agent can perform a wide range of Git operations including:

### Repository & Staging
- `git_init`: Initialize a new repository
- `git_clone`: Clone remote repositories
- `git_add`: Stage changes for commit
- `git_status`: Check the status of the working directory
- `git_clean`: Remove untracked files (requires force flag)

### Committing & History
- `git_commit`: Create new commits with conventional messages
- `git_log`: View commit history with filtering options
- `git_diff`: Show changes between commits, branches, or the working tree
- `git_show`: Inspect Git objects like commits and tags

### Branching & Merging
- `git_branch`: List, create, delete, and rename branches
- `git_checkout`: Switch between branches or commits
- `git_merge`: Merge branches together
- `git_rebase`: Re-apply commits on top of another base
- `git_cherry_pick`: Apply specific commits from other branches

### Remote Operations
- `git_remote`: Manage remote repository connections
- `git_fetch`: Download objects and refs from a remote
- `git_pull`: Fetch and integrate with another repository
- `git_push`: Update remote refs with local changes

### Advanced Workflows
- `git_tag`: Create, list, or delete tags
- `git_stash`: Temporarily store modified files
- `git_worktree`: Manage multiple working trees attached to a single repository
- `git_set_working_dir`: Set a persistent working directory for a session
- `git_wrapup_instructions`: Get a standard workflow for finalizing changes

## Prerequisites

Before using the Git agent, you need to have the required dependencies:

1. **Docker**: Download and install from [https://docker.com/](https://docker.com/)

2. **Git MCP Server Docker Image**: Ensure the `mcp/git` Docker image is available:
   ```bash
   docker pull mcp/git
   ```
   
   Or build it locally if you have the source.

## Configuration

The Git agent can be configured in two ways:

### 1. Global Configuration (git.yaml)

The Git agent can be configured using the `git.yaml` configuration file in the `agent_defaults` directory:

```yaml
# Optional working directory for Git operations
# If not specified, the agent will use the current working directory
working_directory: "/path/to/your/repo"

# System message for the Git agent
system_message: |
  You are a helpful Git assistant that can interact with local Git repositories.
  You can perform various Git operations including status checks, branching,
  staging, committing, pushing, pulling, diffing, logging, and more.
  Always be precise and careful with Git operations, especially destructive ones.
  Ask for confirmation before performing potentially dangerous operations like
  git reset --hard or git clean -f.

# Git-specific configuration options
git_config:
  # Whether to sign commits (requires GPG/SSH setup)
  sign_commits: false
```

### 2. Participant Configuration (Recommended)

When using the git agent as a participant in an orchestrator, you can specify the repository directory directly in the participants list:

```yaml
participants:
  - interaction_memory
  - calendar
  - github
  - git[/path/to/specific/repository]
```

This approach is recommended because:
- The repository directory is determined when adding the agent as a participant
- No global configuration is needed for the working directory
- Different orchestrator configurations can use different repositories
- More flexible and explicit about which repository to work with

The participant parameter takes precedence over any `working_directory` specified in the git.yaml configuration file.

## Usage

### Creating a Git Agent

```python
from robotsix_agents.repository_team.git import create_agent

# Create a Git agent instance (uses current directory or config working_directory)
git_agent = create_agent()

# Create a Git agent for a specific repository
git_agent = create_agent(repository_directory="/path/to/specific/repo")
```

### Basic Example

```python
from robotsix_agents.repository_team.git import create_agent

def main():
    # Create the Git agent for a specific repository
    agent = create_agent(repository_directory="/path/to/your/repo")
    
    # Use the agent to check Git status
    result = agent.run(task="Check the status of the current repository")
    print(result.messages[-1])

if __name__ == "__main__":
    main()
```

### Usage with Orchestrator

When using the git agent with an orchestrator, specify the repository in the participant configuration:

```yaml
# config.yaml
agents:
  orchestrator:
    participants:
      - interaction_memory
      - calendar
      - github
      - git[/home/projects/Robotsix/robotsix_agents_ws/robotsix_agents]
```

This automatically passes the repository directory to the git agent when it's created as a participant.

## Safety Features

The Git agent includes several safety features:

1. **Confirmation for Destructive Operations**: The agent will ask for confirmation before performing potentially dangerous operations like `git reset --hard` or `git clean -f`.

2. **Working Directory Management**: You can set a specific working directory to ensure operations are performed in the correct repository.

3. **Comprehensive Error Handling**: Clear error messages and fallback options when dependencies are missing.

4. **Logging**: Detailed logging of Git operations for debugging and auditing.

## Architecture

The Git agent follows the robotsix_agents pattern:

- `agent.py`: Main agent implementation with MCP workbench integration
- `__init__.py`: Module exports
- `git.yaml`: Default configuration file

The agent uses the `McpWorkbench` from `autogen_ext.tools.mcp` to communicate with the Docker-based git MCP server via the Model Context Protocol.

## Troubleshooting

### "docker: command not found"

This error occurs when Docker is not installed or not in PATH. Install Docker from [https://docker.com/](https://docker.com/).

### "Unable to find image 'mcp/git:latest'"

This error occurs when the `mcp/git` Docker image is not available locally. Pull it with:
```bash
docker pull mcp/git
```

### "Permission denied while trying to connect to Docker daemon"

This error occurs when your user doesn't have permission to access Docker. Either:
1. Add your user to the docker group: `sudo usermod -aG docker $USER` (requires logout/login)
2. Run with sudo (not recommended for production)

### Permission Errors

If you encounter permission errors when performing Git operations, ensure:
1. You have the necessary permissions to read/write to the repository
2. The working directory is correctly set
3. Git user configuration is properly set up

## Development

To test the Git agent implementation:

```bash
cd /path/to/robotsix_agents_ws
python test_git_agent.py
```

This will verify that the MCP connection works and the Docker-based git MCP server is properly configured.