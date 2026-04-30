#!/usr/bin/env python3
"""
Recipe Library Web Application
Flask-based web interface for recipe management with image processing.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename
import frontmatter
import markdown

# Import our existing scripts
from scripts.process_images import RecipeProcessor
from scripts.search_recipes import RecipeSearcher

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = './images'
app.config['RECIPES_FOLDER'] = './recipes'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'heic', 'heif'}

# Initialize processors
processor = RecipeProcessor()
searcher = RecipeSearcher()


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    """Home page with upload and search interface."""
    return render_template('index.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """Upload page for images."""
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
            file.save(filepath)
            
            # Process the image
            try:
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
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        return jsonify({'error': 'Invalid file type'}), 400
    
    return render_template('upload.html')


@app.route('/search', methods=['GET', 'POST'])
def search():
    """Search page for recipes."""
    if request.method == 'POST':
        data = request.json
        
        # Extract search parameters
        semantic_query = data.get('semantic_query')
        ingredients = data.get('ingredients', [])
        cuisine = data.get('cuisine', [])
        dietary = data.get('dietary', [])
        meal_type = data.get('meal_type')
        max_time = data.get('max_time')
        difficulty = data.get('difficulty')
        exclude_ingredients = data.get('exclude_ingredients', [])
        limit = data.get('limit', 10)
        
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
                limit=limit
            )
            
            # Format results
            formatted_results = []
            for recipe_id, score in results:
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
                'count': len(formatted_results)
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    return render_template('search.html')


@app.route('/recipe/<recipe_id>')
def view_recipe(recipe_id):
    """View a single recipe with markdown and image."""
    recipe_file = Path(app.config['RECIPES_FOLDER']) / f"{recipe_id}.md"
    
    if not recipe_file.exists():
        return "Recipe not found", 404
    
    # Load recipe
    recipe = searcher._load_recipe(str(recipe_file))
    if not recipe:
        return "Error loading recipe", 500
    
    # Convert markdown content to HTML
    if recipe.get('content'):
        md = markdown.Markdown(extensions=['extra', 'nl2br', 'sane_lists'])
        recipe['content_html'] = md.convert(recipe['content'])
    else:
        recipe['content_html'] = ''
    
    return render_template('recipe.html', recipe=recipe, recipe_id=recipe_id)


@app.route('/recipe/<recipe_id>/edit', methods=['GET', 'POST'])
def edit_recipe(recipe_id):
    """Edit a recipe markdown file."""
    recipe_file = Path(app.config['RECIPES_FOLDER']) / f"{recipe_id}.md"
    
    if not recipe_file.exists():
        return "Recipe not found", 404
    
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
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # GET request - load recipe for editing
    recipe = searcher._load_recipe(str(recipe_file))
    if not recipe:
        return "Error loading recipe", 500
    
    return render_template('edit.html', recipe=recipe, recipe_id=recipe_id)


@app.route('/recipes')
def list_recipes():
    """List all recipes."""
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
    
    return render_template('recipes.html', recipes=recipes)


@app.route('/images/<filename>')
def serve_image(filename):
    """Serve images from the images directory."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


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
