# Cuisine Recipes Library

A local recipe extraction and search system using Ollama vision models. Convert cookbook images to searchable markdown files with semantic search capabilities.

## Features

- 🖼️ **Image-to-Recipe Extraction**: Convert recipe photos from cookbooks into structured markdown files
- 🔍 **Semantic Search**: Find recipes by ingredients, cooking methods, or descriptions using AI embeddings
- 🏷️ **Auto-Categorization**: Automatic tagging with cuisine types, dietary restrictions, and meal types
- 🇫🇷 **French Language Support**: All fields and content in French
- 📱 **HEIC Support**: Automatic conversion of Apple HEIC/HEIF images to JPEG
- 📊 **Dual Logging**: Complete audit trail with timestamped logs
- 🔄 **Batch Processing**: Process multiple recipe images at once

## Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) installed locally
- Git (for version control)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/frederic-fadda/cuisine-recipes-library.git
cd cuisine-recipes-library
```

### 2. Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

### 3. Install Ollama Models

```bash
# Vision model for recipe extraction
ollama pull llama3.2-vision

# Embedding model for semantic search
ollama pull nomic-embed-text
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

## Usage

### Extract Recipes from Images

**Single Image:**
```bash
python3 scripts/process_images.py images/recipe.jpg
```

**Multiple Images:**
```bash
python3 scripts/process_images.py images/recipe1.jpg images/recipe2.heic images/recipe3.png
```

**Batch Process Directory:**
```bash
python3 scripts/process_images.py images/*.jpg
```

### Search Recipes

**Semantic Search (AI-powered):**
```bash
python3 scripts/search_recipes.py "saumon fumé" --mode semantic
```

**Keyword Search:**
```bash
python3 scripts/search_recipes.py "saumon" --mode keyword
```

**Hybrid Search (combines both):**
```bash
python3 scripts/search_recipes.py "poisson grillé" --mode hybrid
```

**Filter by Fields:**
```bash
# Search in specific fields
python3 scripts/search_recipes.py "végétarien" --fields tags_dietetiques

# Search in multiple fields
python3 scripts/search_recipes.py "rapide" --fields difficulte temps_preparation
```

## Configuration

Edit `config.yaml` to customize:

```yaml
ollama:
  vision_model: "llama3.2-vision"    # Vision model for extraction
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
  save_json: true                     # Save raw JSON extractions
  auto_embed: true                    # Generate embeddings automatically
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

### Example Search Results

```bash
$ python3 scripts/search_recipes.py "saumon fumé" --mode semantic

Found 3 recipes:

1. Rillettes de Saumon à la Galette de Sarrasin Grillée (Score: 0.89)
   Cuisine: Française | Type: Entrée | Difficulté: Facile
   Ingrédients: saumon fumé, fromage frais, galette de sarrasin
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Author

Frédéric Fadda ([@frederic-fadda](https://github.com/frederic-fadda))

## Acknowledgments

- Built with [Ollama](https://ollama.ai/)
- Vision models: llama3.2-vision
- Embedding models: nomic-embed-text