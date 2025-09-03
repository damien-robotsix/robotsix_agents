# Repository Parser with Docker PostgreSQL

This implementation provides repository parsing using CocoIndex with PostgreSQL running in Docker containers.

## Features

- **PostgreSQL with pgvector**: Uses `pgvector/pgvector:pg16` Docker image for vector storage support
- **Unique Repository IDs**: Each repository gets a unique ID based on its absolute path
- **Isolated Data Storage**: Data stored in `~/.local/share/robotsix-agents/{repo_id}` using platformdirs
- **Container Management**: Automatic PostgreSQL container lifecycle management
- **Backward Compatibility**: Maintains the same API as the original SQLite implementation

## Architecture

### Components

1. **RepositoryIdManager**: Maps absolute repository paths to unique IDs
   - Stores mapping in `~/.local/share/robotsix-agents/repo_mapping.json`
   - Creates data directories for each repository

2. **DockerPostgreSQLManager**: Manages PostgreSQL containers
   - Container naming: `cocoindex_pg_{repo_id}`
   - Volume mounting: Local data directory to `/var/lib/postgresql/data`
   - Health checks: Waits for PostgreSQL to be ready before proceeding

3. **RepositoryParser**: Main parser class with PostgreSQL backend
   - Uses CocoIndex flows for embedding and indexing
   - Automatic container startup and connection management
   - Maintains working directory context

### Data Storage Structure

```
~/.local/share/robotsix-agents/
├── repo_mapping.json              # Maps repo IDs to absolute paths
├── {repo_id_1}/
│   └── postgres_data/             # PostgreSQL data volume
├── {repo_id_2}/
│   └── postgres_data/             # PostgreSQL data volume
└── ...
```

## Usage

```python
from robotsix_agents.repository_team.parser.tools import RepositoryParser

# Initialize parser (automatically creates PostgreSQL container)
parser = RepositoryParser("/path/to/repository")

# Get repository statistics
stats = parser.get_repository_stats()

# Index repository content
result = parser.index_repository()

# Search repository (placeholder implementation)
results = parser.search_repository("query", limit=10)

# Get connection info
conn_info = parser.get_connection_info()

# Clean up
parser.close()

# Optional: Remove container and data
parser.cleanup_database(remove_data=True)
```

## Dependencies

- `docker>=7.0.0`: Docker container management
- `psycopg2-binary>=2.9.0`: PostgreSQL connectivity
- `platformdirs>=4.4.0`: Cross-platform data directory management
- `cocoindex[embeddings]`: Core indexing functionality

## Container Configuration

- **Image**: `pgvector/pgvector:pg16`
- **Database**: `cocoindex`
- **User**: `cocoindex` / `cocoindex`
- **Port**: Dynamically assigned by Docker
- **Restart Policy**: `unless-stopped`

## Testing

Run the test scripts to verify functionality:

```bash
# Test all components
python robotsix_agents/test_docker_postgres_parser.py

# Test backward compatibility
python robotsix_agents/test_minimal_parser.py
```

Both tests should pass successfully, demonstrating:
- Repository ID management
- Docker container lifecycle
- PostgreSQL connectivity
- CocoIndex integration
- File indexing and processing