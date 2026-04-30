# Docker Web Application - Setup Summary

## What Was Created

A complete web application for the Recipe Library with Docker containerization that connects to your local Ollama installation.

## Files Created

### Core Application
- **`app.py`** - Flask web application with all routes and API endpoints
- **`Dockerfile`** - Container configuration for the web app
- **`docker-compose.yml`** - Docker Compose configuration with volume mounts and Ollama connection
- **`.dockerignore`** - Excludes unnecessary files from Docker build

### HTML Templates (in `templates/`)
- **`base.html`** - Base template with navigation
- **`index.html`** - Home page with feature cards
- **`upload.html`** - Image upload interface with drag-and-drop
- **`search.html`** - Advanced search with semantic and filter options
- **`recipe.html`** - Recipe viewer with side-by-side markdown and image
- **`edit.html`** - Recipe editor for modifying markdown files
- **`recipes.html`** - List view of all recipes

### Static Assets
- **`static/css/style.css`** - Complete styling for the web interface
- **`static/js/main.js`** - JavaScript utilities

### Documentation & Scripts
- **`README-DOCKER.md`** - Comprehensive Docker setup guide
- **`start-docker.sh`** - Convenient startup script
- **`DOCKER-SETUP-SUMMARY.md`** - This file

### Updated Files
- **`requirements.txt`** - Added Flask, Gunicorn, and Werkzeug
- **`README.md`** - Added Docker/Web Application section

## Key Features

### 1. Upload Images
- Drag-and-drop interface
- Automatic processing with Ollama vision model
- Real-time progress feedback
- Generates markdown and embeddings automatically

### 2. Search Recipes
- **Semantic Search**: Natural language queries ("comfort food for winter")
- **Multi-select Filters**:
  - Ingredients (include/exclude)
  - Cuisine types
  - Dietary tags
  - Meal types
  - Max cooking time
  - Difficulty level
- **Hybrid Search**: Combines semantic + filters

### 3. View Recipes
- Side-by-side layout: markdown content + original image
- Full recipe metadata display
- Confidence scores and review flags

### 4. Edit Recipes
- In-browser markdown editor
- Update metadata fields
- Auto-regenerates embeddings on save

## Persistent Directories

These directories are mounted as volumes (data persists outside container):
- `./images` - Uploaded recipe images
- `./recipes` - Generated markdown files
- `./logs` - Application logs
- `./json-extract` - Raw JSON extractions
- `./embeddings` - Vector embeddings database

## Ollama Connection

The Docker container connects to Ollama running on your host machine using:
- `OLLAMA_HOST=http://host.docker.internal:11434`
- `extra_hosts: host.docker.internal:host-gateway`

This allows the containerized app to access your local Ollama installation seamlessly.

## How to Use

### Start the Application

```bash
# Option 1: Use the startup script
./start-docker.sh

# Option 2: Use Docker Compose directly
docker-compose up --build
```

### Access the Web Interface

Open your browser to: **http://localhost:5000**

### Stop the Application

Press `Ctrl+C` in the terminal, or:

```bash
docker-compose down
```

## Workflow

1. **Upload** a recipe image through the web interface
2. AI **extracts** recipe details and creates markdown file
3. **Embeddings** are generated automatically for semantic search
4. **Search** for recipes using natural language or filters
5. **View** recipes with markdown and original image side-by-side
6. **Edit** recipes directly in the browser if needed

## Technical Stack

- **Backend**: Flask + Gunicorn
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **AI**: Ollama (qwen2.5vl for vision, nomic-embed-text for embeddings)
- **Container**: Docker + Docker Compose
- **Storage**: File-based (markdown files + JSON embeddings)

## Architecture

```
┌─────────────────────────────────────────┐
│         Web Browser (localhost:5000)     │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│      Docker Container (Flask App)        │
│  ┌────────────────────────────────────┐ │
│  │  Flask Routes & API Endpoints      │ │
│  │  - Upload, Search, View, Edit      │ │
│  └────────────┬───────────────────────┘ │
│               │                          │
│  ┌────────────▼───────────────────────┐ │
│  │  Python Scripts                    │ │
│  │  - process_images.py               │ │
│  │  - search_recipes.py               │ │
│  └────────────┬───────────────────────┘ │
└───────────────┼──────────────────────────┘
                │
                │ HTTP (host.docker.internal:11434)
                │
┌───────────────▼──────────────────────────┐
│   Ollama (Running on Host Machine)       │
│   - qwen2.5vl (vision model)             │
│   - nomic-embed-text (embedding model)   │
└──────────────────────────────────────────┘

Persistent Volumes (Host Machine):
├── images/        (uploaded images)
├── recipes/       (markdown files)
├── logs/          (application logs)
├── json-extract/  (raw extractions)
└── embeddings/    (vector database)
```

## Configuration

Edit `config.yaml` to customize:
- Models (vision and embedding)
- Processing options (quality threshold, batch size)
- Search settings (similarity threshold)
- Validation rules (confidence thresholds)

## Troubleshooting

### Can't connect to Ollama
- Ensure Ollama is running: `ollama list`
- Check connection: `curl http://localhost:11434/api/tags`

### Port 5000 already in use
Edit `docker-compose.yml` and change the port mapping:
```yaml
ports:
  - "8080:5000"  # Use port 8080 instead
```

### Permission issues
Ensure directories have proper permissions:
```bash
chmod -R 755 images recipes logs json-extract embeddings
```

## Next Steps

1. Start the application: `./start-docker.sh`
2. Open http://localhost:5000 in your browser
3. Upload your first recipe image
4. Try searching with semantic queries
5. Edit and refine recipes as needed

## Support

- See [README-DOCKER.md](README-DOCKER.md) for detailed documentation
- See [README.md](README.md) for general usage information
- Check logs in `./logs/` directory for debugging

---

**Built with Flask, Docker, and Ollama** 🍳