# Recipe Library - Podman Setup

This guide explains how to run the Recipe Library web application using Podman with access to your local Ollama installation.

## Prerequisites

1. **Podman** installed on your system
2. **podman-compose** installed (`pip3 install podman-compose`)
3. **Ollama** running locally on your machine
4. Required Ollama models pulled:
   ```bash
   ollama pull qwen2.5vl
   ollama pull nomic-embed-text
   ```

## Quick Start

### 1. Install podman-compose (if not already installed)

```bash
pip3 install podman-compose
```

### 2. Build and Start the Container

```bash
# Using the startup script (auto-detects Podman)
./start-docker.sh

# Or manually with podman-compose
podman-compose up --build
```

The web application will be available at: **http://localhost:5000**

### 3. Stop the Container

```bash
# Stop the container
podman-compose down
```

## Podman-Specific Configuration

### Host Networking

Podman uses `host.containers.internal` instead of Docker's `host.docker.internal` to access the host machine. This is already configured in `docker-compose.yml`:

```yaml
environment:
  - OLLAMA_HOST=http://host.containers.internal:11434
extra_hosts:
  - "host.containers.internal:host-gateway"
```

### SELinux Volume Labels

If you're using SELinux (common on Fedora, RHEL, CentOS), the volumes are mounted with the `:Z` flag to properly label them:

```yaml
volumes:
  - ./images:/app/images:Z
  - ./recipes:/app/recipes:Z
```

This ensures the container can read and write to these directories.

## Differences from Docker

### 1. Command Differences

| Docker | Podman |
|--------|--------|
| `docker-compose` | `podman-compose` |
| `docker` | `podman` |
| `host.docker.internal` | `host.containers.internal` |

### 2. Rootless by Default

Podman runs rootless by default, which is more secure. No special configuration needed.

### 3. No Daemon

Podman doesn't require a daemon to be running, unlike Docker. It's a daemonless container engine.

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

## Troubleshooting

### Container Can't Connect to Ollama

**Problem**: Error connecting to Ollama from container

**Solutions**:

1. Ensure Ollama is running: `ollama list`
2. Check Ollama is accessible: `curl http://localhost:11434/api/tags`
3. Verify host networking:
   ```bash
   # Test from within the container
   podman exec -it <container-id> curl http://host.containers.internal:11434/api/tags
   ```

### SELinux Permission Issues

**Problem**: Container can't access mounted volumes

**Solutions**:

1. The `:Z` flag should handle this automatically
2. If issues persist, temporarily disable SELinux enforcement:
   ```bash
   sudo setenforce 0
   ```
3. Or set proper SELinux context:
   ```bash
   sudo chcon -Rt svirt_sandbox_file_t images/ recipes/ logs/ json-extract/ embeddings/
   ```

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

### podman-compose Not Found

**Problem**: `podman-compose` command not found

**Solution**: Install it via pip:
```bash
pip3 install podman-compose
```

## Podman Commands

### View Running Containers

```bash
podman ps
```

### View Logs

```bash
# Follow logs in real-time
podman-compose logs -f

# View specific service logs
podman-compose logs web
```

### Stop and Remove Containers

```bash
podman-compose down
```

### Rebuild Container

```bash
podman-compose up --build
```

### Access Container Shell

```bash
# Get container ID
podman ps

# Access shell
podman exec -it <container-id> /bin/bash
```

## Rootless Podman Considerations

### Port Binding

Rootless Podman can bind to ports > 1024 without issues. For ports < 1024, you may need to adjust:

```bash
# Allow binding to privileged ports
echo "net.ipv4.ip_unprivileged_port_start=80" | sudo tee /etc/sysctl.d/podman-privileged-ports.conf
sudo sysctl --system
```

### Volume Permissions

Rootless Podman maps UIDs differently. If you encounter permission issues:

```bash
# Ensure directories are owned by your user
chown -R $USER:$USER images recipes logs json-extract embeddings
chmod -R 755 images recipes logs json-extract embeddings
```

## Performance

Podman performance is generally comparable to Docker:

- **Processing Time**: 30-60 seconds per image
- **Search Speed**: < 1 second for semantic search
- **Container Startup**: 5-10 seconds

## Systemd Integration (Optional)

Run the container as a systemd service:

```bash
# Generate systemd unit file
cd /path/to/cuisine-recipes-library
podman-compose up -d
podman generate systemd --new --files --name recipe-library-web

# Move to systemd directory
mkdir -p ~/.config/systemd/user/
mv container-recipe-library-web.service ~/.config/systemd/user/

# Enable and start
systemctl --user enable container-recipe-library-web
systemctl --user start container-recipe-library-web

# Check status
systemctl --user status container-recipe-library-web
```

## Updating

To update the application:

```bash
# Pull latest changes
git pull

# Rebuild and restart
podman-compose down
podman-compose up --build
```

## Health Check

The application includes a health check endpoint:
- URL: http://localhost:5000/health
- Returns: `{"status": "healthy"}`

Podman will automatically restart the container if health checks fail.

## Comparison: Podman vs Docker

| Feature | Podman | Docker |
|---------|--------|--------|
| Daemon | No daemon required | Requires Docker daemon |
| Root | Rootless by default | Requires root or group membership |
| Security | More secure (rootless) | Requires daemon with root |
| Compatibility | OCI-compliant | OCI-compliant |
| Systemd | Native integration | Requires additional setup |
| Host Access | `host.containers.internal` | `host.docker.internal` |

## Support

For issues or questions:
1. Check the logs: `podman-compose logs`
2. Verify Ollama is running: `ollama list`
3. Check SELinux status: `getenforce`
4. Review volume permissions: `ls -la images/ recipes/`
5. See main [README.md](README.md) for general usage information

---

**Built with Flask, Podman, and Ollama** 🍳