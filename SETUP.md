# Setup Guide

Complete step-by-step setup instructions for the Recipe Converter system.

## Step 1: Verify Ollama Installation

Since you already have Ollama installed, verify it's working:

```bash
ollama --version
```

You should see the Ollama version number.

## Step 2: Install Vision Model

Choose one of these vision models:

### Option A: llama3.2-vision (Recommended)
```bash
ollama pull llama3.2-vision
```
- Size: ~7.9 GB
- Quality: Excellent
- Speed: Good
- Best for: High-quality recipe extraction

### Option B: llava (Lighter Alternative)
```bash
ollama pull llava
```
- Size: ~4.7 GB
- Quality: Good
- Speed: Faster
- Best for: Quick processing, lower memory systems

**Wait for download to complete** (may take 10-30 minutes depending on internet speed)

## Step 3: Install Embedding Model

Choose one of these embedding models:

### Option A: nomic-embed-text (Recommended)
```bash
ollama pull nomic-embed-text
```
- Size: ~274 MB
- Quality: Good
- Speed: Very fast
- Best for: Most users

### Option B: mxbai-embed-large (Higher Accuracy)
```bash
ollama pull mxbai-embed-large
```
- Size: ~669 MB
- Quality: Excellent
- Speed: Fast
- Best for: Better semantic search accuracy

## Step 4: Verify Models

Check that models are installed:

```bash
ollama list
```

You should see both models listed:
```
NAME                    ID              SIZE      MODIFIED
llama3.2-vision:latest  abc123...       7.9 GB    2 minutes ago
nomic-embed-text:latest def456...       274 MB    1 minute ago
```

## Step 5: Install Python Dependencies

```bash
# Navigate to project directory
cd /Users/fredericfadda/ffadev/XX-cuisine-recipes-V1

# Install required packages
pip3 install -r requirements.txt
```

Expected output:
```
Successfully installed ollama-0.x.x Pillow-10.x.x python-frontmatter-1.x.x numpy-1.x.x pyyaml-6.x
```

## Step 6: Verify Python Installation

```bash
python3 -c "import ollama, frontmatter, PIL, numpy, yaml; print('All packages installed successfully!')"
```

Should print: `All packages installed successfully!`

## Step 7: Update Configuration (Optional)

Edit `config.yaml` if you chose different models:

```yaml
models:
  vision: "llava"              # Change if you installed llava instead
  embedding: "mxbai-embed-large"  # Change if you installed this instead
```

## Step 8: Test the System

### Test 1: Check Ollama Connection
```bash
python3 -c "import ollama; print(ollama.list())"
```

Should show your installed models.

### Test 2: Process a Test Image

1. Add a test image to the `images/` directory:
```bash
# Copy a recipe photo to the images directory
cp ~/path/to/recipe-photo.jpg images/test-recipe.jpg
```

2. Process the image:
```bash
python3 scripts/process_images.py images/test-recipe.jpg
```

Expected output:
```
Processing: images/test-recipe.jpg
Image quality score: 85.0
✅ Saved recipe to: recipes/test-recipe.md
✅ Generated embedding for semantic search
```

3. Check the generated recipe:
```bash
cat recipes/test-recipe.md
```

### Test 3: Test Search

```bash
python3 scripts/search_recipes.py --semantic "test"
```

Should show your test recipe in the results.

## Troubleshooting Setup

### Issue: "ollama: command not found"
**Solution:** Ollama is not in your PATH. Try:
```bash
/usr/local/bin/ollama --version
```
Or reinstall Ollama from https://ollama.ai

### Issue: "Model 'llama3.2-vision' not found"
**Solution:** The model isn't installed. Run:
```bash
ollama pull llama3.2-vision
```

### Issue: "No module named 'ollama'"
**Solution:** Python package not installed. Run:
```bash
pip3 install ollama
```

### Issue: "Permission denied" when running scripts
**Solution:** Make scripts executable:
```bash
chmod +x scripts/*.py
```

### Issue: Model download is very slow
**Solution:** 
- Check your internet connection
- Try downloading during off-peak hours
- Consider using the lighter `llava` model instead

### Issue: "Out of memory" error
**Solution:**
- Close other applications
- Use the lighter `llava` model
- Process images one at a time instead of batch mode
- Restart your computer to free up memory

## System Requirements Check

Verify your system meets the requirements:

```bash
# Check available disk space (need ~10 GB)
df -h .

# Check available RAM (need 8 GB minimum, 16 GB recommended)
sysctl hw.memsize

# Check Python version (need 3.8+)
python3 --version
```

## Next Steps

Once setup is complete:

1. **Add your recipe images** to the `images/` directory
2. **Process them** using `python3 scripts/process_images.py --batch`
3. **Search your recipes** using `python3 scripts/search_recipes.py`

See [README.md](README.md) for detailed usage instructions.

## Configuration Tips

### For Better Extraction Quality
```yaml
extraction:
  temperature: 0.1  # Lower = more consistent (default: 0.3)
  max_tokens: 3000  # Higher = more detailed recipes (default: 2000)
```

### For Faster Processing
```yaml
processing:
  generate_embeddings: false  # Skip embeddings initially
  batch_size: 10              # Process more at once
```

### For Better Search Results
```yaml
search:
  similarity_threshold: 0.5   # Lower = more results (default: 0.6)
  default_limit: 20          # Show more results (default: 10)
```

## Estimated Setup Time

- Model downloads: 15-45 minutes (depending on internet speed)
- Python packages: 2-5 minutes
- Testing: 5-10 minutes
- **Total: ~30-60 minutes**

## Getting Help

If you encounter issues:

1. Check this troubleshooting section
2. Verify all models are installed: `ollama list`
3. Check Python packages: `pip3 list | grep -E "ollama|frontmatter|Pillow|numpy"`
4. Review the error messages carefully
5. Check the [README.md](README.md) for usage examples

---

**Ready to start converting your recipes! 🎉**