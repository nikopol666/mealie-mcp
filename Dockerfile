# Multi-stage Docker build for Mealie MCP Server
FROM python:3.12-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.12-slim

# Create non-root user for security
RUN groupadd -r mcp && useradd -r -g mcp mcp

# Set working directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/mcp/.local

# Copy application source code
COPY src/ ./src/
COPY requirements.txt .

# Set ownership and permissions
RUN chown -R mcp:mcp /app

# Switch to non-root user
USER mcp

# Add local packages to PATH
ENV PATH="/home/mcp/.local/bin:${PATH}"
ENV PYTHONPATH="/app/src"

# Environment variables with defaults
ENV MEALIE_BASE_URL="http://mealie:9000" \
    MCP_SERVER_NAME="Mealie MCP Server" \
    MCP_PORT=8080 \
    MCP_HOST="0.0.0.0" \
    LOG_LEVEL="INFO" \
    REQUEST_TIMEOUT=30 \
    MAX_RETRIES=3

# Expose the MCP server port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/health', timeout=5).raise_for_status()" || exit 1

# Run the MCP server
CMD ["python", "src/main.py", "--transport", "streamable-http"]
