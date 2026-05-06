"""Configuration settings for the Mealie MCP server."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    # Mealie connection settings
    mealie_base_url: str = Field(
        default="http://localhost:9000",
        description="Base URL of the Mealie instance"
    )
    mealie_api_token: str = Field(
        description="API token for Mealie authentication"
    )
    
    # MCP server settings
    mcp_server_name: str = Field(
        default="Mealie MCP Server",
        description="Name of the MCP server"
    )
    mcp_port: int = Field(
        default=8080,
        description="Port for the MCP server to listen on"
    )
    mcp_host: str = Field(
        default="0.0.0.0",
        description="Host for the MCP server to bind to"
    )
    
    # Request settings
    request_timeout: int = Field(
        default=30,
        description="HTTP request timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retries for failed requests"
    )
    
    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
# Global settings instance
settings = Settings()
