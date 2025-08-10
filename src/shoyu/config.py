from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """
    Application configuration settings.

    Attributes:
        DEFAULT_NUM_CIRCUITS (int): Default number of Tor circuits to create for search pooling.
        DEFAULT_MAX_QUERIES_PER_IDENTITY (int): Maximum queries allowed per Tor identity before rotation.
        DEFAULT_MAX_RESULTS (int): Default maximum number of search results to return.
        DEFAULT_SEARCH_TIMEOUT (int): Timeout in seconds for search operations.
        DEFAULT_CONNECT_TIMEOUT (int): Timeout in seconds for establishing network connections.

        TOR_SOCKS_PORT_RANGE (tuple[int, int]): Range of SOCKS proxy ports for Tor circuits.
        TOR_CONTROL_PORT_RANGE (tuple[int, int]): Range of control ports for Tor circuits.
        TOR_CIRCUIT_DIRTY_TIME (int): Time in seconds before Tor circuits are considered "dirty" and rotated.
        TOR_STARTUP_TIMEOUT (int): Timeout in seconds for Tor daemon startup.

        MAX_CONCURRENT_SEARCHES (int): Maximum number of concurrent search operations.
        RATE_LIMIT_DELAY (float): Minimum delay in seconds between search requests for rate limiting.

        MIN_OPERATION_DELAY (float): Minimum randomized delay (seconds) between operations.
        MAX_OPERATION_DELAY (float): Maximum randomized delay (seconds) between operations.

    Environment Variables:
        Reads from .env file if present, allowing override of any setting.

    Usage:
        Use the global `config` instance for accessing settings throughout the application.
    """
    # Default configuration values
    DEFAULT_NUM_CIRCUITS: int = 3
    DEFAULT_MAX_QUERIES_PER_IDENTITY: int = 15
    DEFAULT_MAX_RESULTS: int = 10
    DEFAULT_SEARCH_TIMEOUT: int = 30
    DEFAULT_CONNECT_TIMEOUT: int = 5

    # Tor configuration constants
    TOR_SOCKS_PORT_RANGE: tuple[int, int] = (9050, 9150)
    TOR_CONTROL_PORT_RANGE: tuple[int, int] = (9051, 9151)
    TOR_CIRCUIT_DIRTY_TIME: int = 600  # 10 minutes
    TOR_STARTUP_TIMEOUT: int = 10  # seconds

    # Rate limiting
    MAX_CONCURRENT_SEARCHES: int = 10
    RATE_LIMIT_DELAY: float = 0.5  # seconds between searches

    # Randomized delay between operations (parametrized)
    MIN_OPERATION_DELAY: float = 0.1 # minimum seconds
    MAX_OPERATION_DELAY: float = 1.0  # maximum seconds

    class Config:
        env_file = ".env"

config = Config()
"""
Global configuration instance.

Use this object to access all application settings, e.g.:
    config.DEFAULT_NUM_CIRCUITS
"""
