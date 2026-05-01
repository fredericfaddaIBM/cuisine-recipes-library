# Cuisine Recipes Library
**Recipe Image to Markdown Converter**

A local recipe extraction and search system using Ollama vision models. Convert cookbook images to searchable markdown files with semantic search capabilities.

## Features

- 🖼️ **Image-to-Recipe Extraction**: Uses vision AI to convert recipe photos from cookbooks into structured markdown files
- 🏷️ **Auto-Categorization**: Automatic tagging with cuisine types, dietary restrictions, and meal types
- 🔍 **Semantic Search**: Find recipes by ingredients, cooking methods, or descriptions using AI embeddings
- 🎯 **Keyword Search**: Filter by ingredients, cuisine, cooking time, difficulty
- � **Hybrid Search**: Combines semantic understanding with precise filters
- 🇫🇷 **French Language Support**: All fields and content in French
- 📱 **HEIC Support**: Automatic conversion of Apple HEIC/HEIF images to JPEG
- 📊 **Dual Logging**: Complete audit trail with timestamped logs
- 🔄 **Batch Processing**: Process multiple recipe images at once
- 📊 **Structured Data**: YAML frontmatter for easy parsing and integration
- � **100% Local**: All processing happens on your machine, fully private

## Prerequisites

1. **Ollama** [Ollama](https://ollama.ai/) installed locally
2. **Python 3.8+** (included with macOS)
3. **Vision Model** (to be installed)
4. **Embedding Model** (to be installed)


## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/fredericfaddaIBM/cuisine-recipes-library
cd cuisine-recipes-library
```

### 2. Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

### 3. Install Ollama Models

```bash
# Install vision model for recipe extraction (choose one)
ollama pull qwen2.5vl           # Recommended (text extraction efficiency)
# OR
ollama pull llama3.2-vision    # (11B params)
# OR
ollama pull llava              # Lighter alternative (7B params)

# Install embedding model for semantic search
ollama pull nomic-embed-text   # Recommended (137M params, fast)
# OR
ollama pull mxbai-embed-large  # More accurate (335M params)
```

### 4. Verify Installation

```bash
# Check Ollama models
ollama list

# Should show:
# qwen2.5vl (or llama3.2-vision or llava)
# nomic-embed-text (or mxbai-embed-large)
```

## Project Structure

```
cuisine-recipes-library/
├── config.yaml              # Configuration file
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore rules
├── images/                 # Place recipe images here
├── recipes/                # Extracted markdown recipes
├── embeddings/             # Vector embeddings for search
├── json-extract/           # Raw JSON extractions (debug)
├── logs/                   # Script execution logs
├── scripts/
│   ├── process_images.py   # Recipe extraction script
│   └── search_recipes.py   # Recipe search utility
└── templates/
    └── recipe_template.md  # Markdown template
```

## Quick Start

### 1. Add Recipe Images

Place your recipe photos in the `images/` directory:

```bash
cp ~/Pictures/recipe-photos/*.jpg images/
```

Supported formats: JPG, JPEG, PNG, HEIC

### 2. Process Images

**Process a single image:**
```bash
python3 scripts/process_images.py images/coq-au-vin.jpg
```

**Process all images (batch mode):**
```bash
python3 scripts/process_images.py --batch
```

This will:
- Extract recipe data from images
- Create markdown files in `recipes/`
- Generate embeddings for semantic search
- Flag low-confidence extractions for review

### 3. Search Recipes

**Semantic search (natural language):**
```bash
python3 scripts/search_recipes.py --semantic "comfort food for winter"
python3 scripts/search_recipes.py --semantic "quick weeknight dinner"
python3 scripts/search_recipes.py --semantic "impressive but easy for guests"
```

**Keyword search (filters):**
```bash
# By ingredient
python3 scripts/search_recipes.py --ingredient chicken tomatoes

# By cuisine
python3 scripts/search_recipes.py --cuisine french italian

# By dietary requirements
python3 scripts/search_recipes.py --dietary vegetarian gluten-free

# By cooking time
python3 scripts/search_recipes.py --max-time 30

# Exclude ingredients
python3 scripts/search_recipes.py --ingredient chicken --exclude mushrooms
```

**Hybrid search (combine semantic + filters):**
```bash
python3 scripts/search_recipes.py \
  --semantic "healthy protein-rich meal" \
  --dietary vegetarian \
  --max-time 30 \
  --limit 5
```

**Find similar recipes:**
```bash
python3 scripts/search_recipes.py --similar coq-au-vin
```

## Configuration

Edit `config.yaml` to customize:

```yaml
ollama:
  vision_model: "qwen2.5vl"    # Vision model for extraction
  embedding_model: "nomic-embed-text" # Embedding model for search
  base_url: "http://localhost:11434"
  max_tokens: 4000                    # Max tokens for extraction
  temperature: 0.2                    # Lower = more consistent

directories:
  images: "images"
  recipes: "recipes"
  embeddings: "embeddings"
  json_extract: "json-extract"
  logs: "logs"

processing:
  save_json: true                     # Save raw JSON extractions - TODO (currently true)
  auto_embed: true                    # Generate embeddings automatically - TODO (currently true)
  quality_threshold: 70               # Image quality threshold (0-100)
  use_ocr_fallback: false             # Enable OCR for poor quality images
  generate_embeddings: true           # Generate embeddings during processing

search:
  similarity_threshold: 0.6           # Minimum similarity for semantic search
  default_limit: 10                   # Default number of results
```

## Recipe Format

Extracted recipes include:

- **Metadata**: Title, cuisine type, meal type, dietary tags
- **Timing**: Preparation time, cooking time
- **Details**: Servings, difficulty level
- **Ingredients**: Main ingredients list
- **Allergens**: Automatic allergen detection
- **Instructions**: Step-by-step cooking method
- **Cooking Method**: Grilling, baking, frying, etc.

## Logs

All script executions are logged to `logs/` directory with format:
- `process_images_YYYYMMdd_HH-MM.log`
- `search_recipes_YYYYMMdd_HH-MM.log`

Logs include:
- Start/end timestamps
- Execution duration
- Processing details
- Error messages

## Troubleshooting

### JSON Parsing Errors
If extraction produces malformed JSON:
- The script automatically attempts to repair truncated JSON
- Check `json-extract/` directory for raw output
- Increase `max_tokens` in `config.yaml` if recipes are being cut off

### HEIC Image Errors
If HEIC images fail to process:
```bash
pip3 install --upgrade pillow-heif
```

### Embedding Context Length
If recipes are too long for embeddings:
- The script automatically truncates to 30,000 characters
- Falls back to 2,000 characters if still too long
- Consider using a model with larger context window

### Ollama Connection Issues
Ensure Ollama is running:
```bash
ollama serve
```

## Examples

### Example Recipe Output

```markdown
---
titre: Rillettes de Saumon à la Galette de Sarrasin Grillée
tags_cuisine: [Française]
type_repas: [Entrée]
tags_dietetiques: [Poisson]
temps_preparation: 15 min
temps_cuisson: 5 min
portions: 4
difficulte: Facile
ingredients_principaux: [saumon fumé, fromage frais, galette de sarrasin]
allergenes: [poisson, gluten, produits laitiers]
methode_cuisson: Grillage
---

# Rillettes de Saumon à la Galette de Sarrasin Grillée

## Ingrédients
- 200g de saumon fumé
- 150g de fromage frais
...
```

## Search Examples

### By Concept
```bash
# Find comfort food
python3 scripts/search_recipes.py --semantic "comfort food"

# Find light summer meals
python3 scripts/search_recipes.py --semantic "light summer meal"

# Find recipes for meal prep
python3 scripts/search_recipes.py --semantic "meal prep batch cooking"
```

### By Ingredients
```bash
# What can I make with chicken and rice?
python3 scripts/search_recipes.py --ingredient chicken rice

# Recipes with tomatoes but no cheese
python3 scripts/search_recipes.py --ingredient tomatoes --exclude cheese
```

### By Cuisine & Diet
```bash
# French vegetarian recipes
python3 scripts/search_recipes.py --cuisine french --dietary vegetarian

# Asian vegan recipes under 30 minutes
python3 scripts/search_recipes.py \
  --cuisine chinese japanese thai \
  --dietary vegan \
  --max-time 30
```

### Combined Searches
```bash
# Quick healthy Italian dinner
python3 scripts/search_recipes.py \
  --semantic "healthy quick dinner" \
  --cuisine italian \
  --max-time 30

# Easy impressive French recipes
python3 scripts/search_recipes.py \
  --semantic "impressive but easy" \
  --cuisine french \
  --difficulty easy
```

## Tips & Best Practices

### Image Quality
- Use well-lit, clear photos
- Ensure text is readable
- Avoid extreme angles or distortion
- Higher resolution = better extraction

### Batch Processing
- Process 5-10 images at a time to monitor quality
- Review flagged recipes (low confidence scores)
- Re-process failed images with better photos

### Manual Review
Recipes flagged with `needs_review: true` should be manually checked:
```bash
# Find recipes needing review
grep -r "needs_review: true" recipes/
```

### Improving Search Results
- Use natural language for semantic search
- Combine semantic + keyword filters for best results
- Adjust `similarity_threshold` in config.yaml if needed

## Performance

### Processing Time
- Single image: 30-60 seconds
- Batch (50 images): ~45 minutes
- Batch (200 images): ~3 hours

### Search Speed
- Semantic search: < 1 second
- Keyword search: < 100ms
- Hybrid search: < 1 second

### Storage
- Recipe markdown: ~2-5 KB each
- Embeddings: ~3 KB per recipe
- Total for 200 recipes: ~1-2 MB

## Troubleshooting

### "Model not found" error
```bash
# Install the required model
ollama pull qwen2.5vl
ollama pull nomic-embed-text
```

### "No embeddings found" error
```bash
# Process images first to generate embeddings
python3 scripts/process_images.py --batch
```

### Low extraction quality
1. Check image quality (lighting, focus, resolution)
2. Enable OCR fallback in config.yaml:
   ```yaml
   processing:
     use_ocr_fallback: true
   ```
3. Try a different vision model (qwen2.5vl vs llama3.2-vision)

### Python import errors
```bash
# Reinstall dependencies
pip3 install -r requirements.txt
```

## Advanced Usage

### Custom Configuration
```bash
# Use custom config file
python3 scripts/process_images.py --config my-config.yaml
python3 scripts/search_recipes.py --config my-config.yaml
```

### Detailed Search Results
```bash
# Show full recipe details in search results
python3 scripts/search_recipes.py --semantic "pasta" --details
```

### Export Search Results
```bash
# Save search results to file
python3 scripts/search_recipes.py --semantic "italian" > italian-recipes.txt
```

## Web Application (Docker/Podman)

A web interface is now available! Run the application in a container with access to your local Ollama installation.

### Quick Start

```bash
# Start the web application (auto-detects Docker or Podman)
./start-docker.sh

# Or manually:
# For Docker:
docker-compose up --build

# For Podman:
podman-compose up --build
```

The web application will be available at: **http://localhost:26574**

### Features

- 📤 **Upload Images**: Drag and drop recipe images for automatic processing
- ✏️ **Edit Recipes**: Modify markdown files directly in the browser
- 🔍 **Advanced Search**: Use semantic search with multiple filter options
- 👁️ **Side-by-Side View**: See markdown and original image together
- 🔄 **Auto-Processing**: Uploads trigger automatic text extraction and embedding generation

### Documentation

- [README-DOCKER.md](README-DOCKER.md) - Docker/Podman setup guide
- [README-PODMAN.md](README-PODMAN.md) - Podman-specific details

## Future Enhancements

Potential additions:
- [x] Web interface for easier searching
- [ ] Recipe recommendations based on cooking history
- [ ] Nutritional information extraction
- [ ] Shopping list generation
- [ ] Recipe scaling (adjust servings)
- [ ] Export to other formats (PDF, JSON)

## License

This project is for personal use. Recipe content belongs to the original cookbook authors.

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Verify Ollama models are installed: `ollama list`
3. Check Python dependencies: `pip3 list`
4. Review config.yaml settings

---

**Happy Cooking! 👨‍🍳**

## Author

Frédéric Fadda ([@frederic-fadda](https://github.com/fredericfaddaIBM))

## Acknowledgments

- Built with [Ollama](https://ollama.ai/) and [Bob](https://bob.ibm.com/)
- Vision model: qwen2.5vl
- Embedding model: nomic-embed-text