# Recipe Library - Docker/Podman Setup

This guide explains how to run the Recipe Library web application in a container with access to your local Ollama installation.

> **Note**: This guide covers both Docker and Podman. For Podman-specific details, see [README-PODMAN.md](README-PODMAN.md).

## Prerequisites

1. **Docker/Podman** and **docker-compose/podman-compose** installed on your system
2. **Ollama** running locally on your machine
3. Required Ollama models pulled:
   ```bash
   ollama pull qwen2.5vl
   ollama pull nomic-embed-text
   ```

### For Podman Users

Install podman-compose:
```bash
pip3 install podman-compose
```

## Quick Start

### 1. Build and Start the Container

```bash
# Using the startup script (auto-detects Docker or Podman)
./start-docker.sh

# Or manually:
# For Docker:
docker-compose up --build

# For Podman:
podman-compose up --build
```

The web application will be available at: **http://localhost:5000**

### 2. Stop the Container

```bash
# For Docker:
docker-compose down

# For Podman:
podman-compose down
```

## How It Works

### Ollama Connection

The container connects to your local Ollama installation using special hostnames:
- **Docker**: `host.docker.internal`
- **Podman**: `host.containers.internal`

The connection is configured in `docker-compose.yml`:
```yaml
environment:
  # Works for both Docker and Podman
  - OLLAMA_HOST=http://host.containers.internal:11434
extra_hosts:
  - "host.containers.internal:host-gateway"
```

> **Note**: `host.containers.internal` works for both Docker (with recent versions) and Podman.

### Persistent Directories

The following directories are mounted as volumes, so data persists outside the container:

- `./images` - Uploaded recipe images
- `./recipes` - Generated markdown recipe files
- `./logs` - Application logs
- `./json-extract` - Raw JSON extractions from images
- `./embeddings` - Vector embeddings for semantic search

These directories are created automatically if they don't exist.

> **Podman Note**: Volumes are mounted with `:Z` flag for SELinux compatibility.

## Using the Web Application

### 1. Upload Recipe Images

1. Navigate to **Upload** page
2. Drag and drop or select a recipe image
3. Click "Upload and Process"
4. The AI will extract recipe details and create a markdown file

### 2. Search Recipes

1. Navigate to **Search** page
2. Use semantic search (natural language) or filters:
   - **Semantic**: "comfort food for winter"
   - **Ingredients**: chicken, tomatoes
   - **Cuisine**: French, Italian, etc.
   - **Dietary**: vegetarian, vegan, etc.
   - **Meal Type**: breakfast, lunch, dinner
   - **Max Time**: cooking time in minutes
   - **Difficulty**: easy, medium, hard

### 3. View and Edit Recipes

1. Click on any recipe to view details
2. See the markdown content and original image side-by-side
3. Click "Edit Recipe" to modify the content
4. Changes are saved and embeddings are regenerated

### 4. Browse All Recipes

Navigate to **All Recipes** to see your complete recipe library.

## Configuration

Edit `config.yaml` to customize:

- **Models**: Change vision or embedding models
- **Processing**: Adjust quality thresholds, batch sizes
- **Search**: Modify similarity thresholds
- **Validation**: Set confidence thresholds for manual review

## Troubleshooting

### Container Can't Connect to Ollama

**Problem**: Error connecting to Ollama from container

**Solutions**:
1. Ensure Ollama is running: `ollama list`
2. Check Ollama is accessible: `curl http://localhost:11434/api/tags`
3. For Docker on Linux, you may need to use your machine's IP address instead of `host.containers.internal`
4. For Podman, `host.containers.internal` should work automatically

### Port Already in Use

**Problem**: Port 5000 is already in use

**Solution**: Change the port in `docker-compose.yml`:
```yaml
ports:
  - "8080:5000"  # Use port 8080 instead
```

### Models Not Found

**Problem**: Ollama models not available

**Solution**: Pull the required models:
```bash
ollama pull qwen2.5vl
ollama pull nomic-embed-text
```

### Permission Issues with Volumes

**Problem**: Container can't write to mounted directories

**Solution**: Ensure directories have proper permissions:
```bash
chmod -R 755 images recipes logs json-extract embeddings
```

## Development Mode

To run in development mode with auto-reload:

1. Edit `docker-compose.yml` and change:
   ```yaml
   environment:
     - FLASK_ENV=development
   ```

2. Restart the container:
   ```bash
   docker-compose down
   docker-compose up
   ```

## Production Deployment

For production use:

1. Keep `FLASK_ENV=production` (default)
2. The app runs with Gunicorn (2 workers, 300s timeout)
3. Consider adding a reverse proxy (nginx) for SSL/TLS
4. Set up proper backup for persistent directories

## Logs

View container logs:
```bash
# For Docker:
docker-compose logs -f

# For Podman:
podman-compose logs -f
```

Application logs are also saved in the `./logs` directory.

## Updating

To update the application:

```bash
# Pull latest changes
git pull

# Rebuild and restart
# For Docker:
docker-compose down
docker-compose up --build

# For Podman:
podman-compose down
podman-compose up --build
```

## Health Check

The application includes a health check endpoint:
- URL: http://localhost:5000/health
- Returns: `{"status": "healthy"}`

Docker will automatically restart the container if health checks fail.

## Support

For issues or questions:
1. Check the logs: `docker-compose logs` or `podman-compose logs`
2. Verify Ollama is running: `ollama list`
3. For Podman-specific issues, see [README-PODMAN.md](README-PODMAN.md)
4. Check the main [README.md](README.md) for general usage information