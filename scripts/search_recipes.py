#!/usr/bin/env python3
"""
Recipe Search Utility
Search recipes using keyword, semantic, or hybrid search.
"""

import os
import sys
import json
import yaml
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import numpy as np
import frontmatter
import ollama


class DualLogger:
    """Logger that writes to both console and file."""
    
    def __init__(self, script_name: str):
        """Initialize dual logger."""
        # Create logs directory
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        # Create log filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H-%M')
        log_file = log_dir / f"{script_name}_{timestamp}.log"
        
        # Setup logging
        self.logger = logging.getLogger(script_name)
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # File handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.log_file = log_file
        self.start_time = datetime.now()
        
        # Log start message
        self.info("="*60)
        self.info(f"Script: {script_name}")
        self.info(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.info(f"Log file: {log_file}")
        self.info("="*60)
    
    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message."""
        self.logger.error(message)
    
    def finalize(self):
        """Log end message with duration."""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        self.info("="*60)
        self.info(f"Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.info(f"Duration: {duration}")
        self.info("="*60)


class RecipeSearcher:
    """Search recipes using multiple methods."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the searcher with configuration."""
        self.config = self._load_config(config_path)
        self.embedding_model = self.config['models']['embedding']
        self.recipes_dir = Path(self.config['directories']['recipes'])
        self.embeddings_db = self._load_embeddings()
        self.recipes_cache = {}
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _load_embeddings(self) -> Dict:
        """Load embeddings database."""
        embeddings_path = Path(self.config['directories']['embeddings']) / 'embeddings.json'
        if embeddings_path.exists():
            with open(embeddings_path, 'r') as f:
                return json.load(f)
        return {'recipes': {}, 'metadata': {}}
    
    def _load_recipe(self, filepath: str) -> Optional[Dict]:
        """Load a recipe markdown file."""
        if filepath in self.recipes_cache:
            return self.recipes_cache[filepath]
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
                recipe = dict(post.metadata)
                recipe['content'] = post.content
                recipe['filepath'] = filepath
                self.recipes_cache[filepath] = recipe
                return recipe
        except Exception as e:
            print(f"Error loading recipe {filepath}: {e}")
            return None
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text."""
        try:
            response = ollama.embeddings(
                model=self.embedding_model,
                prompt=text
            )
            return response['embedding']
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def semantic_search(self, query: str, limit: int = 10) -> List[Tuple[str, float]]:
        """Search recipes using semantic similarity."""
        if not self.embeddings_db['recipes']:
            print("No embeddings found. Run process_images.py first.")
            return []
        
        # Generate query embedding
        query_embedding = self._generate_embedding(query)
        if not query_embedding:
            return []
        
        # Calculate similarities
        similarities = []
        for recipe_id, recipe_embedding in self.embeddings_db['recipes'].items():
            similarity = self._cosine_similarity(query_embedding, recipe_embedding)
            similarities.append((recipe_id, similarity))
        
        # Sort by similarity and filter by threshold
        threshold = self.config['search']['similarity_threshold']
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        results = [
            (recipe_id, score) 
            for recipe_id, score in similarities 
            if score >= threshold
        ][:limit]
        
        return results
    
    def keyword_search(
        self,
        ingredients: Optional[List[str]] = None,
        cuisine: Optional[List[str]] = None,
        dietary: Optional[List[str]] = None,
        meal_type: Optional[str] = None,
        max_time: Optional[int] = None,
        difficulty: Optional[str] = None,
        exclude_ingredients: Optional[List[str]] = None
    ) -> List[str]:
        """Search recipes using keyword filters (supports French field names)."""
        results = []
        
        # Get all recipe files
        recipe_files = list(self.recipes_dir.glob('*.md'))
        
        for recipe_file in recipe_files:
            recipe = self._load_recipe(str(recipe_file))
            if not recipe:
                continue
            
            # Apply filters
            matches = True
            
            # Ingredient filter
            if ingredients:
                recipe_ingredients = ' '.join(recipe.get('ingredients', [])).lower()
                if not all(ing.lower() in recipe_ingredients for ing in ingredients):
                    matches = False
            
            # Exclude ingredients
            if exclude_ingredients:
                recipe_ingredients = ' '.join(recipe.get('ingredients', [])).lower()
                if any(ing.lower() in recipe_ingredients for ing in exclude_ingredients):
                    matches = False
            
            # Cuisine filter (support both French and English keys)
            if cuisine:
                recipe_cuisines = [recipe.get('cuisine', '').lower()] + \
                                [c.lower() for c in recipe.get('tags_cuisine', recipe.get('cuisine_tags', []))]
                if not any(c.lower() in recipe_cuisines for c in cuisine):
                    matches = False
            
            # Dietary filter (support both French and English keys)
            if dietary:
                recipe_dietary = [d.lower() for d in recipe.get('tags_dietetiques', recipe.get('dietary_tags', []))]
                if not all(d.lower() in recipe_dietary for d in dietary):
                    matches = False
            
            # Meal type filter (support both French and English keys)
            if meal_type:
                recipe_meals = [recipe.get('type_repas', recipe.get('meal_type', '')).lower()] + \
                              [m.lower() for m in recipe.get('tags_repas', recipe.get('meal_tags', []))]
                if meal_type.lower() not in recipe_meals:
                    matches = False
            
            # Time filter (support both French and English keys)
            if max_time:
                total_time = recipe.get('temps_total', recipe.get('total_time', ''))
                # Extract minutes from time string
                if total_time:
                    try:
                        minutes = int(''.join(filter(str.isdigit, total_time)))
                        if minutes > max_time:
                            matches = False
                    except ValueError:
                        pass
            
            # Difficulty filter (support both French and English keys)
            if difficulty:
                recipe_difficulty = recipe.get('difficulte', recipe.get('difficulty', '')).lower()
                if recipe_difficulty != difficulty.lower():
                    matches = False
            
            if matches:
                results.append(recipe_file.stem)
        
        return results
    
    def hybrid_search(
        self,
        semantic_query: Optional[str] = None,
        ingredients: Optional[List[str]] = None,
        cuisine: Optional[List[str]] = None,
        dietary: Optional[List[str]] = None,
        meal_type: Optional[str] = None,
        max_time: Optional[int] = None,
        difficulty: Optional[str] = None,
        exclude_ingredients: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Tuple[str, float]]:
        """Combine semantic and keyword search."""
        # Start with keyword search if filters provided
        keyword_results = set()
        if any([ingredients, cuisine, dietary, meal_type, max_time, difficulty, exclude_ingredients]):
            keyword_results = set(self.keyword_search(
                ingredients=ingredients,
                cuisine=cuisine,
                dietary=dietary,
                meal_type=meal_type,
                max_time=max_time,
                difficulty=difficulty,
                exclude_ingredients=exclude_ingredients
            ))
        
        # Perform semantic search if query provided
        if semantic_query:
            semantic_results = self.semantic_search(semantic_query, limit=limit * 2)
            
            # If we have keyword filters, intersect results
            if keyword_results:
                filtered_results = [
                    (recipe_id, score)
                    for recipe_id, score in semantic_results
                    if recipe_id in keyword_results
                ]
                return filtered_results[:limit]
            else:
                return semantic_results[:limit]
        
        # If only keyword search, return those results with score 1.0
        return [(recipe_id, 1.0) for recipe_id in list(keyword_results)[:limit]]
    
    def find_similar(self, recipe_id: str, limit: int = 5) -> List[Tuple[str, float]]:
        """Find recipes similar to a given recipe."""
        if recipe_id not in self.embeddings_db['recipes']:
            print(f"Recipe '{recipe_id}' not found in embeddings database.")
            return []
        
        recipe_embedding = self.embeddings_db['recipes'][recipe_id]
        
        # Calculate similarities with all other recipes
        similarities = []
        for other_id, other_embedding in self.embeddings_db['recipes'].items():
            if other_id != recipe_id:
                similarity = self._cosine_similarity(recipe_embedding, other_embedding)
                similarities.append((other_id, similarity))
        
        # Sort and return top results
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]
    
    def display_results(self, results: List[Tuple[str, float]], show_details: bool = False):
        """Display search results in a formatted way."""
        if not results:
            print("No recipes found matching your criteria.")
            return
        
        print(f"\nFound {len(results)} recipe(s):\n")
        
        for i, (recipe_id, score) in enumerate(results, 1):
            # Get recipe metadata
            metadata = self.embeddings_db['metadata'].get(recipe_id, {})
            filepath = metadata.get('filepath', '')
            
            if not filepath:
                # Try to find the file
                recipe_file = self.recipes_dir / f"{recipe_id}.md"
                if recipe_file.exists():
                    filepath = str(recipe_file)
            
            recipe = self._load_recipe(filepath) if filepath else None
            
            if recipe:
                # Support both French and English field names
                title = recipe.get('titre', recipe.get('title', recipe_id))
                cuisine = recipe.get('cuisine', 'Inconnu')
                time = recipe.get('temps_total', recipe.get('total_time', 'Inconnu'))
                difficulty = recipe.get('difficulte', recipe.get('difficulty', 'Inconnu'))
                dietary = ', '.join(recipe.get('tags_dietetiques', recipe.get('dietary_tags', []))) or 'Aucun'
                
                print(f"{i}. {title}")
                print(f"   Cuisine: {cuisine} | Temps: {time} | Difficulté: {difficulty}")
                print(f"   Diététique: {dietary}")
                print(f"   Similarité: {score:.2%}")
                
                if show_details:
                    main_ing = recipe.get('ingredients_principaux', recipe.get('main_ingredients', []))
                    print(f"   Ingrédients: {', '.join(main_ing)}")
                    print(f"   Fichier: {filepath}")
                
                print()
            else:
                print(f"{i}. {recipe_id} (Score: {score:.2%})")
                print()


def main():
    """Main entry point for the script."""
    # Initialize logger
    logger = DualLogger('search_recipes')
    
    try:
        parser = argparse.ArgumentParser(
            description='Search recipes using keyword, semantic, or hybrid search',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Exemples:
  # Recherche sémantique
  python search_recipes.py --semantic "plat réconfortant pour l'hiver"
  
  # Recherche par mots-clés
  python search_recipes.py --ingredient poulet tomates --cuisine italienne
  
  # Hybrid search
  python search_recipes.py --semantic "quick healthy meal" --dietary vegetarian --max-time 30
  
  # Find similar recipes
  python search_recipes.py --similar coq-au-vin
            """
        )
        
        # Search type
        parser.add_argument('--semantic', type=str, help='Semantic search query')
        parser.add_argument('--similar', type=str, help='Find recipes similar to this one (recipe ID)')
        
        # Keyword filters
        parser.add_argument('--ingredient', nargs='+', help='Required ingredients')
        parser.add_argument('--exclude', nargs='+', help='Ingredients to exclude')
        parser.add_argument('--cuisine', nargs='+', help='Cuisine types')
        parser.add_argument('--dietary', nargs='+', help='Dietary requirements')
        parser.add_argument('--meal', type=str, help='Meal type (breakfast, lunch, dinner, etc.)')
        parser.add_argument('--max-time', type=int, help='Maximum cooking time in minutes')
        parser.add_argument('--difficulty', type=str, choices=['easy', 'medium', 'hard'], help='Difficulty level')
        
        # Options
        parser.add_argument('--limit', type=int, default=10, help='Number of results to return')
        parser.add_argument('--details', action='store_true', help='Show detailed information')
        parser.add_argument('--config', default='config.yaml', help='Path to config file')
        
        args = parser.parse_args()
        
        searcher = RecipeSearcher(args.config)
        
        # Find similar recipes
        if args.similar:
            logger.info(f"Finding recipes similar to: {args.similar}")
            results = searcher.find_similar(args.similar, limit=args.limit)
            logger.info(f"\nRecipes similar to '{args.similar}':")
            searcher.display_results(results, show_details=args.details)
            logger.finalize()
            return
        
        # Hybrid search (semantic + keyword)
        if args.semantic or any([args.ingredient, args.cuisine, args.dietary, args.meal, args.max_time, args.difficulty]):
            logger.info("Performing search...")
            results = searcher.hybrid_search(
                semantic_query=args.semantic,
                ingredients=args.ingredient,
                cuisine=args.cuisine,
                dietary=args.dietary,
                meal_type=args.meal,
                max_time=args.max_time,
                difficulty=args.difficulty,
                exclude_ingredients=args.exclude,
                limit=args.limit
            )
            
            logger.info(f"\nSearch completed. Found {len(results)} result(s).")
            searcher.display_results(results, show_details=args.details)
            logger.finalize()
        else:
            parser.print_help()
            logger.finalize()
            
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Search interrupted by user")
        logger.finalize()
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        logger.finalize()
        sys.exit(1)


if __name__ == '__main__':
    main()
