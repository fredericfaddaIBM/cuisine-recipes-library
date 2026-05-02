# Quick Start Guide

Get up and running in 5 steps!

## 1. Install Ollama Models (15-30 min)

```bash
# Install vision model
ollama pull llama3.2-vision

# Install embedding model
ollama pull nomic-embed-text

# Verify installation
ollama list
```

## 2. Install Python Dependencies (2 min)

```bash
pip3 install -r requirements.txt
```

## 3. Add Your Recipe Images

```bash
# Copy your recipe photos to the images directory
cp ~/Pictures/recipes/*.jpg images/
```

## 4. Process Your Images

```bash
# Process all images at once
python3 scripts/process_images.py --batch
```

This will:
- Extract recipes from images
- Create markdown files in `recipes/`
- Generate embeddings for search

## 5. Search Your Recipes

```bash
# Natural language search
python3 scripts/search_recipes.py --semantic "comfort food"

# Search by ingredient
python3 scripts/search_recipes.py --ingredient chicken

# Search by cuisine
python3 scripts/search_recipes.py --cuisine french italian

# Combined search
python3 scripts/search_recipes.py \
  --semantic "quick dinner" \
  --dietary vegetarian \
  --max-time 30
```

## Common Commands

### Processing
```bash
# Single image
python3 scripts/process_images.py images/recipe.jpg

# Batch processing
python3 scripts/process_images.py --batch
```

### Searching
```bash
# Semantic search
python3 scripts/search_recipes.py --semantic "your query"

# By ingredients
python3 scripts/search_recipes.py --ingredient tomatoes basil

# By cuisine
python3 scripts/search_recipes.py --cuisine italian

# By dietary needs
python3 scripts/search_recipes.py --dietary vegetarian vegan

# By cooking time
python3 scripts/search_recipes.py --max-time 30

# Find similar recipes
python3 scripts/search_recipes.py --similar recipe-name
```

## Need Help?

- **Full documentation**: See [`README.md`](../README.md)
- **Setup issues**: See [`SETUP.md`](./SETUP.md)
- **Configuration**: Edit `config.yaml`

## Tips

1. **Start small**: Process 5-10 images first to test
2. **Check quality**: Review recipes flagged with `needs_review: true`
3. **Adjust config**: Edit `config.yaml` for better results
4. **Use hybrid search**: Combine semantic + filters for best results

---

**That's it! You're ready to convert and search your recipes! 🎉**