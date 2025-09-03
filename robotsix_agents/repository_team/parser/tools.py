"""
Repository Parser tools implementation using CocoIndex with PostgreSQL in Docker.

This module provides a solution for parsing repository content using CocoIndex
with PostgreSQL database running in Docker containers, with proper volume management.
"""

import logging
import os
import json
import hashlib
from typing import List, Optional, Dict, Any
from pathlib import Path

import docker  # type: ignore
from docker.models.containers import Container  # type: ignore
import platformdirs
import cocoindex
import time
import psycopg2  # type: ignore

# Import configuration manager
from ...core import load_agent_config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@cocoindex.transform_flow()
def text_to_embedding(
    text: cocoindex.DataSlice[str]
) -> cocoindex.DataSlice[list[float]]:
    """
    Embed the text using a SentenceTransformer model.
    This is a shared logic between indexing and querying, so extract it as a function.
    """
    return text.transform(
        cocoindex.functions.SentenceTransformerEmbed(
            model="sentence-transformers/all-MiniLM-L6-v2"))


@cocoindex.op.function()
def extract_extension(filename: str) -> str:
    """Extract the extension of a filename."""
    return os.path.splitext(filename)[1]


def search(connection_url: str, query: str, top_k: int = 5):
    """Search the repository using vector similarity."""
    # Use the actual table name created by CocoIndex
    table_name = "repositoryembeddingflow__repository_embeddings"
    query_vector = text_to_embedding.eval(query)

    conn = psycopg2.connect(connection_url)
    try:
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT filename, text, embedding <=> %s::vector AS distance
                FROM {table_name} ORDER BY distance LIMIT %s
            """, (query_vector, top_k))
            return [
                {"filename": row[0], "text": row[1], "score": 1.0 - row[2]}
                for row in cur.fetchall()
            ]
    finally:
        conn.close()


def _main():
    """Main function for interactive query in terminal."""
    # Get database connection URL from environment
    connection_url = os.getenv("COCOINDEX_DATABASE_URL")
    if not connection_url:
        print("Error: COCOINDEX_DATABASE_URL environment variable not set")
        return
    
    # Run queries in a loop to demonstrate the query capabilities.
    while True:
        query = input("Enter search query (or Enter to quit): ")
        if query == '':
            break
        # Run the query function with the database connection URL and the query.
        try:
            results = search(connection_url, query)
            print("\nSearch results:")
            for result in results:
                print(f"[{result['score']:.3f}] {result['filename']}")
                print(f"    {result['text']}")
                print("---")
            print()
        except Exception as e:
            print(f"Search error: {e}")


class RepositoryIdManager:
    """Manages repository IDs and their mapping to absolute paths."""
    
    def __init__(self):
        self.data_dir = Path(platformdirs.user_data_dir("robotsix-agents"))
        self.mapping_file = self.data_dir / "repo_mapping.json"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._mapping: Dict[str, str] = {}
        self._load_mapping()
    
    def _load_mapping(self):
        """Load the repository mapping from file."""
        if self.mapping_file.exists():
            try:
                with open(self.mapping_file, 'r') as f:
                    self._mapping = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load repository mapping: {e}")
                self._mapping = {}
        else:
            self._mapping = {}
    
    def _save_mapping(self):
        """Save the repository mapping to file."""
        try:
            with open(self.mapping_file, 'w') as f:
                json.dump(self._mapping, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save repository mapping: {e}")
    
    def get_repo_id(self, repo_path: str) -> str:
        """Get or create a repository ID for the given path."""
        absolute_path = str(Path(repo_path).resolve())
        
        # Check if we already have an ID for this path
        for repo_id, stored_path in self._mapping.items():
            if stored_path == absolute_path:
                return repo_id
        
        # Generate a new ID using a hash of the absolute path
        repo_hash = hashlib.sha256(absolute_path.encode()).hexdigest()
        repo_id = repo_hash[:12]  # Use first 12 characters for readability
        
        # Ensure uniqueness
        counter = 0
        original_id = repo_id
        while repo_id in self._mapping:
            counter += 1
            repo_id = f"{original_id}_{counter}"
        
        # Store the mapping
        self._mapping[repo_id] = absolute_path
        self._save_mapping()
        
        # Ensure the data directory exists for this repo
        repo_data_dir = self.get_data_dir(repo_id)
        repo_data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Created new repository ID '{repo_id}' for path: {absolute_path}")
        return repo_id
    
    def get_data_dir(self, repo_id: str) -> Path:
        """Get the data directory for a repository ID."""
        repo_dir = self.data_dir / repo_id
        repo_dir.mkdir(parents=True, exist_ok=True)
        return repo_dir


class DockerPostgreSQLManager:
    """Manages PostgreSQL Docker containers for repository parsing."""
    
    def __init__(self, repo_id: str):
        self.repo_id = repo_id
        self.container_name = f"cocoindex_pg_{repo_id}"
        self.volume_name = f"cocoindex_data_{repo_id}"
        self.client = docker.from_env()
        
        # Get data directory for this repo
        self.repo_manager = RepositoryIdManager()
        self.data_dir = self.repo_manager.get_data_dir(repo_id)
        self.volume_path = self.data_dir / "postgres_data"
        self.volume_path.mkdir(parents=True, exist_ok=True)
    
    def ensure_container_running(self) -> str:
        """Ensure PostgreSQL container is running and return connection URL."""
        container: Container
        try:
            # Check if container exists
            container = self.client.containers.get(self.container_name)  # type: ignore
            if container.status != "running":
                logger.info(
                    f"Starting existing PostgreSQL container: "
                    f"{self.container_name}"
                )
                container.start()
            else:
                logger.info(
                    f"PostgreSQL container already running: "
                    f"{self.container_name}"
                )
        except docker.errors.NotFound:  # type: ignore
            logger.info(
                f"Creating new PostgreSQL container: {self.container_name}"
            )
            container = self.client.containers.run(  # type: ignore
                "pgvector/pgvector:pg16",
                name=self.container_name,
                detach=True,
                environment={
                    "POSTGRES_USER": "cocoindex",
                    "POSTGRES_PASSWORD": "cocoindex",
                    "POSTGRES_DB": "cocoindex",
                },
                ports={"5432/tcp": None},  # Let Docker assign a random port
                volumes={
                    str(self.volume_path): {
                        "bind": "/var/lib/postgresql/data",
                        "mode": "rw"
                    }
                },
                restart_policy={"Name": "unless-stopped"}
            )
        
        # Get the assigned port
        container.reload()
        port_info = container.attrs['NetworkSettings']['Ports']['5432/tcp']
        if port_info:
            host_port = port_info[0]['HostPort']
        else:
            raise RuntimeError(
                f"Could not determine PostgreSQL port for container "
                f"{self.container_name}"
            )
        
        # Build connection URL
        connection_url = (
            f"postgresql://cocoindex:cocoindex@localhost:{host_port}/cocoindex"
        )
        logger.info(f"PostgreSQL available at: {connection_url}")
        
        # Wait for PostgreSQL to be ready
        self._wait_for_postgres(connection_url)
        
        return connection_url
    
    def _wait_for_postgres(self, connection_url: str, max_attempts: int = 30):
        """Wait for PostgreSQL to be ready to accept connections."""
        logger.info("Waiting for PostgreSQL to be ready...")
        
        for attempt in range(max_attempts):
            try:
                # Try to connect (trust auth, no credentials needed)
                conn = psycopg2.connect(connection_url)
                conn.close()
                logger.info("PostgreSQL is ready!")
                return
            except psycopg2.OperationalError:
                if attempt < max_attempts - 1:
                    time.sleep(1)
                    continue
                else:
                    raise
        
        raise RuntimeError("PostgreSQL failed to become ready within timeout")
    
    def stop_container(self):
        """Stop the PostgreSQL container."""
        try:
            container = self.client.containers.get(self.container_name)  # type: ignore
            if container.status == "running":
                logger.info(f"Stopping PostgreSQL container: {self.container_name}")
                container.stop()
        except docker.errors.NotFound:  # type: ignore
            logger.info(f"Container {self.container_name} not found")
    
    def remove_container(self):
        """Remove the PostgreSQL container and its data."""
        try:
            container = self.client.containers.get(self.container_name)  # type: ignore
            container.remove(force=True)
            logger.info(f"Removed PostgreSQL container: {self.container_name}")
        except docker.errors.NotFound:  # type: ignore
            logger.info(f"Container {self.container_name} not found")
        
        # Optionally remove the volume directory
        if self.volume_path.exists():
            import shutil
            shutil.rmtree(self.volume_path)
            logger.info(f"Removed volume data: {self.volume_path}")


@cocoindex.flow_def(name="RepositoryEmbeddingFlow")
def repository_embedding_flow(
    flow_builder: cocoindex.FlowBuilder, data_scope: cocoindex.DataScope
):
    """CocoIndex flow that embeds repository files into a vector index."""
    
    # Default patterns for common source code files
    included_patterns = [
        "*.py", "*.js", "*.ts", "*.md", "*.json", "*.yaml", "*.yml"
    ]
    
    excluded_patterns = [
        ".git", "**/node_modules", "**/__pycache__", "**/.venv", "**/venv",
        "**/build", "**/dist", "**/.idea", "**/.vscode"
    ]
    
    # Add a data source to read files from the repository directory
    data_scope["documents"] = flow_builder.add_source(
        cocoindex.sources.LocalFile(
            path=".",  # root directory for indexing
            included_patterns=included_patterns,
            excluded_patterns=excluded_patterns
        )
    )

    # Add a collector for data to be exported to the vector index
    doc_embeddings = data_scope.add_collector()

    # Transform data of each document
    with data_scope["documents"].row() as doc:
        # Extract the extension of the filename
        doc["extension"] = doc["filename"].transform(extract_extension)
        
        # Split the document into chunks using the file extension as language
        doc["chunks"] = doc["content"].transform(
            cocoindex.functions.SplitRecursively(),
            language=doc["extension"],
            chunk_size=1000,
            chunk_overlap=300,
        )

        # Transform data of each chunk
        with doc["chunks"].row() as chunk:
            # Embed the chunk using shared transform flow
            chunk["embedding"] = chunk["text"].transform(
                cocoindex.functions.SentenceTransformerEmbed(
                    model="sentence-transformers/all-MiniLM-L6-v2"
                )
            )

            # Collect the chunk into the collector.
            doc_embeddings.collect(
                filename=doc["filename"],
                location=chunk["location"],
                text=chunk["text"],
                embedding=chunk["embedding"],
            )

    # Export collected data to a vector index.
    doc_embeddings.export(
        "repository_embeddings",
        cocoindex.storages.Postgres(),
        primary_key_fields=["filename", "location"],
        vector_indexes=[
            cocoindex.VectorIndexDef(
                field_name="embedding",
                metric=cocoindex.VectorSimilarityMetric.COSINE_SIMILARITY,
            )
        ],
    )


class RepositoryParser:
    """Repository parser using CocoIndex with PostgreSQL in Docker."""

    def __init__(self, repo_path: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the CocoIndex repository parser with PostgreSQL backend.

        Args:
            repo_path: Path to the repository
            config: Configuration dictionary (optional)
        """
        self.repo_path = Path(repo_path).resolve()
        
        # Load agent configuration with defaults
        agent_config = load_agent_config("repository_team")
        self.config = config or {}
        
        # Merge agent config with provided config (provided config takes precedence)
        self.parser_config = agent_config.get("parser", {})
        if "parser" in self.config:
            self.parser_config.update(self.config["parser"])
        
        logger.info(f"Initializing repository parser for: {self.repo_path}")
        
        # Set up repository ID and data management
        self.repo_manager = RepositoryIdManager()
        self.repo_id = self.repo_manager.get_repo_id(str(self.repo_path))
        self.data_dir = self.repo_manager.get_data_dir(self.repo_id)
        
        # Set up PostgreSQL Docker container
        self.db_manager = DockerPostgreSQLManager(self.repo_id)
        
        # Initialize CocoIndex with PostgreSQL
        try:
            # Stop any existing instance
            try:
                cocoindex.stop()
            except Exception:
                pass
            
            # Ensure PostgreSQL container is running
            connection_url = self.db_manager.ensure_container_running()
            
            # Initialize with PostgreSQL settings
            db_spec = cocoindex.DatabaseConnectionSpec(url=connection_url)
            settings = cocoindex.Settings(database=db_spec)
            cocoindex.init(settings)
            
            # Setup the flow to ensure it's up-to-date
            cocoindex.setup_all_flows()
            logger.info("CocoIndex initialized successfully with PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to initialize CocoIndex: {e}")
            raise
        
        # Change to repository directory for CocoIndex to work properly
        self.original_cwd = os.getcwd()
        os.chdir(self.repo_path)

    def index_repository(
        self, allowed_extensions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Index the repository content using CocoIndex integrated pipeline.

        Args:
            allowed_extensions: List of allowed file extensions
                (optional, overrides config)

        Returns:
            Dictionary with indexing results
        """
        logger.info(f"Starting repository indexing: {self.repo_path}")
        
        # Use provided extensions or fall back to configuration
        if allowed_extensions is None:
            configured_extensions = self.parser_config.get("file_extensions", [
                "*.py", "*.js", "*.ts", "*.md", "*.json", "*.yaml", "*.yml"
            ])
            logger.info(
                f"Using configured file extensions: {configured_extensions}"
            )
        else:
            configured_extensions = allowed_extensions
            logger.info(f"Using provided file extensions: {configured_extensions}")

        # Get excluded patterns from configuration
        excluded_patterns = self.parser_config.get("exclude_directories", [
            ".git", "node_modules", "__pycache__", ".venv", "venv",
            "build", "dist", ".idea", ".vscode"
        ])
        # Convert to patterns with ** prefix for recursive exclusion
        excluded_patterns = [
            f"**/{pattern}" if not pattern.startswith("**/") else pattern
            for pattern in excluded_patterns
        ]

        try:
            # Run the CocoIndex flow
            stats = repository_embedding_flow.update()

            logger.info(f"Indexing complete: {stats}")

            return {
                "indexed_files": getattr(stats, "processed_documents", 0),
                "total_chunks": getattr(stats, "total_records", 0),
                "indexing_stats": str(stats),
                "flow_name": "RepositoryEmbeddingFlow",
                "repo_id": self.repo_id,
                "data_dir": str(self.data_dir),
                "configured_extensions": configured_extensions,
                "excluded_patterns": excluded_patterns,
                "parser_config": self.parser_config,
            }

        except Exception as e:
            logger.error(f"Indexing failed: {e}")
            raise

    def search_repository(
        self, query: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search the repository content using CocoIndex.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of search results
        """
        try:
            logger.info(f"Searching for: {query}")
            
            # Get database connection URL
            connection_url = self.db_manager.ensure_container_running()
            
            # Use the search function
            results = search(connection_url, query, limit)
            return results

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def close(self):
        """Close connections and clean up."""
        try:
            cocoindex.stop()
            logger.info("Repository parser connections closed")
        except Exception as e:
            logger.error(f"Error closing connections: {e}")
        
        # Restore original working directory
        if hasattr(self, 'original_cwd'):
            os.chdir(self.original_cwd)
    
    def cleanup_database(self, remove_data: bool = False):
        """Clean up the PostgreSQL container and optionally remove data."""
        if remove_data:
            self.db_manager.remove_container()
        else:
            self.db_manager.stop_container()
    
    def get_connection_info(self) -> Dict[str, str]:
        """Get database connection information."""
        try:
            container = self.db_manager.client.containers.get(
                self.db_manager.container_name
            )  # type: ignore
            container.reload()
            port_info = container.attrs['NetworkSettings']['Ports']['5432/tcp']
            if port_info:
                host_port = port_info[0]['HostPort']
                return {
                    "host": "localhost",
                    "port": host_port,
                    "database": "cocoindex",
                    "container_name": self.db_manager.container_name,
                    "volume_path": str(self.db_manager.volume_path),
                }
        except Exception as e:
            logger.error(f"Error getting connection info: {e}")
        
        return {}


if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # dotenv is optional
    cocoindex.init()
    _main()
