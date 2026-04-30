# Recipe Image to Markdown Converter

Convert recipe images from cookbooks into searchable markdown files using local AI models (Ollama).

## Features

- 🖼️ **Image to Recipe Extraction**: Uses vision AI to extract recipes from photos
- 🏷️ **Auto-Tagging**: Automatically categorizes by cuisine, dietary restrictions, meal type
- 🔍 **Semantic Search**: Natural language queries like "comfort food for winter"
- 🎯 **Keyword Search**: Filter by ingredients, cuisine, cooking time, difficulty
- � **Hybrid Search**: Combines semantic understanding with precise filters
- 📊 **Structured Data**: YAML frontmatter for easy parsing and integration
- � **100% Local**: All processing happens on your machine, fully private

## Prerequisites

1. **Ollama** (already installed ✅)
2. **Python 3.8+** (included with macOS)
3. **Vision Model** (to be installed)
4. **Embedding Model** (to be installed)

## Installation

### 1. Install Required Ollama Models

```bash
# Install vision model for recipe extraction (choose one)
ollama run qwen2.5vl
# OR
ollama pull llama3.2-vision    # Recommended (11B params)
# OR
ollama pull llava              # Lighter alternative (7B params)

# Install embedding model for semantic search
ollama pull nomic-embed-text   # Recommended (137M params, fast)
# OR
ollama pull mxbai-embed-large  # More accurate (335M params)
```

### 2. Install Python Dependencies

```bash
# Install required packages
pip3 install -r requirements.txt
```

### 3. Verify Installation

```bash
# Check Ollama models
ollama list

# Should show:
# qwen2.5vl (or llama3.2-vision or llava)
# nomic-embed-text (or mxbai-embed-large)
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

## Project Structure

```
recipe-converter/
├── images/              # Input: Your recipe photos
├── recipes/             # Output: Generated markdown files
├── embeddings/          # Semantic search database
├── scripts/
│   ├── process_images.py    # Image to recipe converter
│   └── search_recipes.py    # Search utility
├── templates/
│   └── recipe_template.md   # Markdown template
├── config.yaml          # Configuration
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Recipe Markdown Format

Each recipe is saved as a markdown file with YAML frontmatter:

```markdown
---
title: "Coq au Vin"
cuisine: "French"
cuisine_tags: [french, european]
meal_type: "Dinner"
meal_tags: [dinner, main_course]
dietary_tags: [gluten-free]
prep_time: "20 minutes"
cook_time: "90 minutes"
total_time: "110 minutes"
servings: 6
difficulty: "Medium"
ingredients:
  - 1 whole chicken, cut into pieces
  - 200g bacon lardons
  - 2 cups red wine
main_ingredients: [chicken, wine, mushrooms]
allergens: []
cooking_method: [braising, stovetop]
---

# Coq au Vin

## Description
A classic French braised chicken dish...

## Ingredients
- 1 whole chicken, cut into pieces
- 200g bacon lardons
...

## Instructions
1. Season chicken pieces with salt and pepper
2. Brown chicken in a large pot
...

## Notes
Best served with crusty bread and a glass of red wine.
```

## Configuration

Edit `config.yaml` to customize:

```yaml
models:
  vision: "llama3.2-vision"      # Vision model for extraction
  embedding: "nomic-embed-text"  # Embedding model for search

processing:
  quality_threshold: 70          # Image quality threshold (0-100)
  use_ocr_fallback: false       # Enable OCR for poor quality images
  generate_embeddings: true      # Generate embeddings during processing

search:
  similarity_threshold: 0.6      # Minimum similarity for semantic search
  default_limit: 10             # Default number of results
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
ollama pull llama3.2-vision
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
3. Try a different vision model (llava vs llama3.2-vision)

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

## Future Enhancements

Potential additions:
- [ ] Web interface for easier searching
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