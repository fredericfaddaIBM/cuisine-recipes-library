#!/usr/bin/env python3
"""
Recipe Library Web Application
Flask-based web interface for recipe management with image processing.
"""

import os
import json
import re
import logging
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, abort
from math import ceil
from werkzeug.utils import secure_filename
from werkzeug.security import safe_join
import frontmatter
import markdown
from PIL import Image

# Import our existing scripts
from scripts.process_images import RecipeProcessor
from scripts.search_recipes import RecipeSearcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = './images'
app.config['RECIPES_FOLDER'] = './recipes'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'heic', 'heif', 'pdf'}

# Initialize processors
processor = RecipeProcessor()
searcher = RecipeSearcher()


def validate_recipe_id(recipe_id: str) -> bool:
    """Validate recipe ID contains only safe characters to prevent path traversal."""
    if not recipe_id:
        return False
    # Check for path traversal attempts
    if '..' in recipe_id or '/' in recipe_id or '\\' in recipe_id:
        return False
    # Allow alphanumeric (including Unicode/accented chars), hyphens, underscores, and numbers
    # This supports French recipe names like "blanquette-de-saumon-écossais-label-rouge-aux-girolles-et-marrons-1"
    return bool(re.match(r'^[\w\-]+$', recipe_id, re.UNICODE))


def validate_filename(filename: str) -> bool:
    """Validate filename contains only safe characters."""
    if not filename:
        return False
    # Only allow alphanumeric, hyphens, underscores, and dots
    return bool(re.match(r'^[a-zA-Z0-9_.-]+$', filename))


def validate_pdf_content(filepath: str) -> bool:
    """
    Validate that uploaded file is actually a PDF.
    This prevents malicious files disguised as PDFs.
    """
    try:
        # Try python-magic first (more reliable)
        try:
            import magic
            mime = magic.from_file(filepath, mime=True)
            if mime != 'application/pdf':
                logger.warning(f"File {filepath} has invalid MIME type for PDF: {mime}")
                return False
        except ImportError:
            # Fallback: check PDF header
            logger.warning("python-magic not installed, using header check for PDF validation")
            with open(filepath, 'rb') as f:
                header = f.read(5)
                if header != b'%PDF-':
                    logger.warning(f"File {filepath} does not have valid PDF header")
                    return False
        
        return True
    except Exception as e:
        logger.error(f"PDF validation failed for {filepath}: {e}")
        return False


def validate_image_content(filepath: str) -> bool:
    """
    Validate that uploaded file is actually an image.
    This prevents malicious files disguised as images.
    """
    try:
        # Try python-magic first (more reliable)
        try:
            import magic
            mime = magic.from_file(filepath, mime=True)
            if not mime.startswith('image/'):
                logger.warning(f"File {filepath} has invalid MIME type: {mime}")
                return False
        except ImportError:
            # Fallback if python-magic not installed
            logger.warning("python-magic not installed, using PIL only for validation")
        
        # Verify image can be opened and is valid
        img = Image.open(filepath)
        img.verify()
        
        # Re-open and re-save to strip any malicious metadata
        img = Image.open(filepath)
        img.save(filepath)
        
        return True
    except Exception as e:
        logger.error(f"Image validation failed for {filepath}: {e}")
        return False


def validate_file_content(filepath: str) -> bool:
    """
    Validate uploaded file content based on extension.
    Supports images and PDFs.
    """
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext == '.pdf':
        return validate_pdf_content(filepath)
    else:
        # Assume it's an image
        return validate_image_content(filepath)


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def get_pagination_args(default_per_page=4):
    """Extract and sanitize pagination parameters from request args/json."""
    data = request.json if request.is_json else request.args

    page = data.get('page', 1)
    per_page = data.get('per_page', default_per_page)

    try:
        page = max(int(page), 1)
    except (TypeError, ValueError):
        page = 1

    allowed_per_page_values = [4, 10, 20, 50, 100]
    try:
        per_page = int(per_page)
        if per_page not in allowed_per_page_values:
            per_page = default_per_page
    except (TypeError, ValueError):
        per_page = default_per_page

    return page, per_page, allowed_per_page_values


@app.route('/')
def index():
    """Home page with upload and search interface."""
    return render_template('index.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """Upload page for images and PDFs."""
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add timestamp to avoid conflicts
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{timestamp}{ext}"
            
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            try:
                # Save file temporarily
                file.save(filepath)
                
                # SECURITY FIX: Validate file content (image or PDF)
                if not validate_file_content(filepath):
                    # Remove invalid file
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    logger.warning(f"Invalid file rejected: {filename}")
                    return jsonify({
                        'success': False,
                        'error': 'Invalid file. File must be a valid image or PDF.'
                    }), 400
                
                # Process the file (image or PDF)
                recipe_path = processor.process_image(filepath)
                if recipe_path:
                    recipe_id = Path(recipe_path).stem
                    return jsonify({
                        'success': True,
                        'message': 'Recipe processed successfully',
                        'recipe_id': recipe_id,
                        'recipe_path': recipe_path
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Failed to process image'
                    }), 500
                    
            except Exception as e:
                # SECURITY FIX: Proper error handling - log details, return generic message
                logger.error(f"Upload failed for {filename}: {e}", exc_info=True)
                # Clean up file if it exists
                if os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                    except Exception:
                        pass
                return jsonify({
                    'success': False,
                    'error': 'An error occurred processing your upload. Please try again.'
                }), 500
        
        return jsonify({'error': 'Invalid file type'}), 400
    
    return render_template('upload.html')


@app.route('/search', methods=['GET', 'POST'])
def search():
    """Search page for recipes."""
    if request.method == 'POST':
        data = request.json
        page, per_page, allowed_per_page_values = get_pagination_args()

        # Extract search parameters
        semantic_query = data.get('semantic_query')
        ingredients = data.get('ingredients', [])
        cuisine = data.get('cuisine', [])
        dietary = data.get('dietary', [])
        meal_type = data.get('meal_type')
        max_time = data.get('max_time')
        difficulty = data.get('difficulty')
        exclude_ingredients = data.get('exclude_ingredients', [])

        # Perform search
        try:
            results = searcher.hybrid_search(
                semantic_query=semantic_query,
                ingredients=ingredients if ingredients else None,
                cuisine=cuisine if cuisine else None,
                dietary=dietary if dietary else None,
                meal_type=meal_type,
                max_time=int(max_time) if max_time else None,
                difficulty=difficulty,
                exclude_ingredients=exclude_ingredients if exclude_ingredients else None,
                limit=1000
            )

            total_results = len(results)
            total_pages = ceil(total_results / per_page) if total_results else 0
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_results = results[start_idx:end_idx]

            # Format results
            formatted_results = []
            for recipe_id, score in paginated_results:
                recipe_file = Path(app.config['RECIPES_FOLDER']) / f"{recipe_id}.md"
                if recipe_file.exists():
                    recipe = searcher._load_recipe(str(recipe_file))
                    if recipe:
                        formatted_results.append({
                            'id': recipe_id,
                            'title': recipe.get('titre', recipe.get('title', recipe_id)),
                            'cuisine': recipe.get('cuisine', 'Unknown'),
                            'time': recipe.get('temps_total', recipe.get('total_time', 'Unknown')),
                            'difficulty': recipe.get('difficulte', recipe.get('difficulty', 'Unknown')),
                            'dietary': recipe.get('tags_dietetiques', recipe.get('dietary_tags', [])),
                            'score': round(score * 100, 1),
                            'image': recipe.get('image_source', '')
                        })

            return jsonify({
                'success': True,
                'results': formatted_results,
                'count': total_results,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total_pages': total_pages,
                    'total_results': total_results,
                    'has_prev': page > 1,
                    'has_next': page < total_pages,
                    'allowed_per_page_values': allowed_per_page_values
                }
            })
        except Exception as e:
            # SECURITY FIX: Proper error handling - log details, return generic message
            logger.error(f"Search failed: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'An error occurred during search. Please try again.'
            }), 500

    _, default_per_page, allowed_per_page_values = get_pagination_args()

    return render_template(
        'search.html',
        default_per_page=default_per_page,
        per_page_options=allowed_per_page_values
    )


@app.route('/recipe/<recipe_id>')
def view_recipe(recipe_id):
    """View a single recipe with markdown and image."""
    # SECURITY FIX: Validate recipe_id to prevent path traversal
    if not validate_recipe_id(recipe_id):
        logger.warning(f"Invalid recipe_id attempted: {recipe_id}")
        abort(400, "Invalid recipe ID")
    
    # SECURITY FIX: Use safe_join to prevent path traversal
    recipe_file = safe_join(app.config['RECIPES_FOLDER'], f"{recipe_id}.md")
    if recipe_file is None or not os.path.exists(recipe_file):
        abort(404, "Recipe not found")
    
    try:
        # Load recipe
        recipe = searcher._load_recipe(recipe_file)
        if not recipe:
            logger.error(f"Failed to load recipe: {recipe_id}")
            abort(500, "Error loading recipe")
        
        # Convert markdown content to HTML
        if recipe.get('content'):
            md = markdown.Markdown(extensions=['extra', 'nl2br', 'sane_lists'])
            recipe['content_html'] = md.convert(recipe['content'])
        else:
            recipe['content_html'] = ''
        
        return render_template('recipe.html', recipe=recipe, recipe_id=recipe_id)
    except Exception as e:
        # SECURITY FIX: Proper error handling
        logger.error(f"Error viewing recipe {recipe_id}: {e}", exc_info=True)
        abort(500, "An error occurred loading the recipe")


@app.route('/recipe/<recipe_id>/edit', methods=['GET', 'POST'])
def edit_recipe(recipe_id):
    """Edit a recipe markdown file."""
    # SECURITY FIX: Validate recipe_id to prevent path traversal
    if not validate_recipe_id(recipe_id):
        logger.warning(f"Invalid recipe_id attempted in edit: {recipe_id}")
        abort(400, "Invalid recipe ID")
    
    # SECURITY FIX: Use safe_join to prevent path traversal
    recipe_file = safe_join(app.config['RECIPES_FOLDER'], f"{recipe_id}.md")
    if recipe_file is None or not os.path.exists(recipe_file):
        abort(404, "Recipe not found")
    
    if request.method == 'POST':
        data = request.json
        
        try:
            # Load existing recipe
            with open(recipe_file, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
            
            # Update metadata
            metadata = data.get('metadata', {})
            for key, value in metadata.items():
                post.metadata[key] = value
            
            # Update content
            if 'content' in data:
                post.content = data['content']
            
            # Save updated recipe
            with open(recipe_file, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(post))
            
            # Regenerate embedding if content changed
            if processor.config['processing']['generate_embeddings']:
                recipe_text = processor._create_recipe_text(dict(post.metadata))
                embedding = processor._generate_embedding(recipe_text)
                if embedding:
                    processor.embeddings_db['recipes'][recipe_id] = embedding
                    processor._save_embeddings()
            
            return jsonify({
                'success': True,
                'message': 'Recipe updated successfully'
            })
        except Exception as e:
            # SECURITY FIX: Proper error handling
            logger.error(f"Error editing recipe {recipe_id}: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'An error occurred updating the recipe. Please try again.'
            }), 500
    
    # GET request - load recipe for editing
    try:
        recipe = searcher._load_recipe(recipe_file)
        if not recipe:
            logger.error(f"Failed to load recipe for editing: {recipe_id}")
            abort(500, "Error loading recipe")
        
        return render_template('edit.html', recipe=recipe, recipe_id=recipe_id)
    except Exception as e:
        # SECURITY FIX: Proper error handling
        logger.error(f"Error loading recipe for edit {recipe_id}: {e}", exc_info=True)
        abort(500, "An error occurred loading the recipe")

@app.route('/recipe/<recipe_id>/delete', methods=['POST'])
def delete_recipe(recipe_id):
    """Delete a recipe and its associated image."""
    # SECURITY: Validate recipe_id to prevent path traversal
    if not validate_recipe_id(recipe_id):
        logger.warning(f"Invalid recipe_id attempted in delete: {recipe_id}")
        return jsonify({
            'success': False,
            'error': 'Invalid recipe ID'
        }), 400
    
    # SECURITY: Use safe_join to prevent path traversal
    recipe_file = safe_join(app.config['RECIPES_FOLDER'], f"{recipe_id}.md")
    if recipe_file is None or not os.path.exists(recipe_file):
        return jsonify({
            'success': False,
            'error': 'Recipe not found'
        }), 404
    
    try:
        # Load recipe to get image filename
        recipe = searcher._load_recipe(recipe_file)
        image_filename = recipe.get('image_source') if recipe else None
        
        # Delete recipe file
        os.remove(recipe_file)
        logger.info(f"Deleted recipe file: {recipe_id}")
        
        # Delete associated image if it exists
        if image_filename:
            image_path = safe_join(app.config['UPLOAD_FOLDER'], image_filename)
            if image_path and os.path.exists(image_path):
                os.remove(image_path)
                logger.info(f"Deleted image file: {image_filename}")
        
        # Remove from embeddings database
        if recipe_id in processor.embeddings_db.get('recipes', {}):
            del processor.embeddings_db['recipes'][recipe_id]
            if recipe_id in processor.embeddings_db.get('metadata', {}):
                del processor.embeddings_db['metadata'][recipe_id]
            processor._save_embeddings()
            logger.info(f"Removed embeddings for recipe: {recipe_id}")
        
        return jsonify({
            'success': True,
            'message': 'Recipe deleted successfully'
        })
        
    except Exception as e:
        # SECURITY FIX: Proper error handling
        logger.error(f"Error deleting recipe {recipe_id}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'An error occurred deleting the recipe. Please try again.'
        }), 500



@app.route('/recipes')
def list_recipes():
    """List all recipes."""
    page, per_page, allowed_per_page_values = get_pagination_args()
    recipes_dir = Path(app.config['RECIPES_FOLDER'])
    recipe_files = list(recipes_dir.glob('*.md'))

    recipes = []
    for recipe_file in recipe_files:
        recipe = searcher._load_recipe(str(recipe_file))
        if recipe:
            recipes.append({
                'id': recipe_file.stem,
                'title': recipe.get('titre', recipe.get('title', recipe_file.stem)),
                'cuisine': recipe.get('cuisine', 'Unknown'),
                'time': recipe.get('temps_total', recipe.get('total_time', 'Unknown')),
                'difficulty': recipe.get('difficulte', recipe.get('difficulty', 'Unknown')),
                'image': recipe.get('image_source', '')
            })

    # Sort by title
    recipes.sort(key=lambda x: x['title'])

    total_recipes = len(recipes)
    total_pages = ceil(total_recipes / per_page) if total_recipes else 0
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_recipes = recipes[start_idx:end_idx]

    return render_template(
        'recipes.html',
        recipes=paginated_recipes,
        total_recipes=total_recipes,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_prev=page > 1,
        has_next=page < total_pages,
        per_page_options=allowed_per_page_values
    )


@app.route('/api/recipes/count')
def recipes_count():
    """Return the total number of recipes."""
    recipes_dir = Path(app.config['RECIPES_FOLDER'])
    total_recipes = len(list(recipes_dir.glob('*.md')))

    return jsonify({
        'success': True,
        'count': total_recipes
    })


@app.route('/images/<filename>')
def serve_image(filename):
    """Serve images from the images directory."""
    # SECURITY FIX: Validate filename to prevent path traversal
    if not validate_filename(filename):
        logger.warning(f"Invalid filename attempted: {filename}")
        abort(400, "Invalid filename")
    
    # SECURITY FIX: Use safe_join to prevent path traversal
    filepath = safe_join(app.config['UPLOAD_FOLDER'], filename)
    if filepath is None or not os.path.exists(filepath):
        abort(404, "Image not found")
    
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        # SECURITY FIX: Proper error handling
        logger.error(f"Error serving image {filename}: {e}", exc_info=True)
        abort(500, "An error occurred serving the image")


@app.route('/api/search-options')
def search_options():
    """Get available search options from existing recipes."""
    recipes_dir = Path(app.config['RECIPES_FOLDER'])
    recipe_files = list(recipes_dir.glob('*.md'))
    
    cuisines = set()
    dietary_tags = set()
    meal_types = set()
    difficulties = set()
    
    for recipe_file in recipe_files:
        recipe = searcher._load_recipe(str(recipe_file))
        if recipe:
            if recipe.get('cuisine'):
                cuisines.add(recipe['cuisine'])
            
            for tag in recipe.get('tags_dietetiques', recipe.get('dietary_tags', [])):
                dietary_tags.add(tag)
            
            if recipe.get('type_repas', recipe.get('meal_type')):
                meal_types.add(recipe.get('type_repas', recipe.get('meal_type')))
            
            if recipe.get('difficulte', recipe.get('difficulty')):
                difficulties.add(recipe.get('difficulte', recipe.get('difficulty')))
    
    return jsonify({
        'cuisines': sorted(list(cuisines)),
        'dietary_tags': sorted(list(dietary_tags)),
        'meal_types': sorted(list(meal_types)),
        'difficulties': sorted(list(difficulties))
    })


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    # Ensure directories exist
    for directory in ['images', 'recipes', 'logs', 'json-extract', 'embeddings']:
        Path(directory).mkdir(exist_ok=True)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

# Made with Bob
