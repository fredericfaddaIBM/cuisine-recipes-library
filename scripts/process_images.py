#!/usr/bin/env python3
"""
Recipe Image Processor
Converts recipe images to structured markdown files using Ollama vision models.
"""

import os
import sys
import json
import yaml
import base64
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import frontmatter
from PIL import Image
import ollama

# Register HEIF/HEIC support
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF_SUPPORT = True
except ImportError:
    HEIF_SUPPORT = False
    print("⚠️  pillow-heif not installed. HEIC/HEIF images will be converted to JPEG.")


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


class RecipeProcessor:
    """Process recipe images and convert to markdown files."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the processor with configuration."""
        self.config = self._load_config(config_path)
        self.vision_model = self.config['models']['vision']
        self.embedding_model = self.config['models']['embedding']
        self.embeddings_db = self._load_embeddings()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _load_embeddings(self) -> Dict:
        """Load existing embeddings database."""
        embeddings_path = Path(self.config['directories']['embeddings']) / 'embeddings.json'
        if embeddings_path.exists():
            with open(embeddings_path, 'r') as f:
                return json.load(f)
        return {'recipes': {}, 'metadata': {}}
    
    def _save_embeddings(self):
        """Save embeddings database to file."""
        embeddings_path = Path(self.config['directories']['embeddings']) / 'embeddings.json'
        with open(embeddings_path, 'w') as f:
            json.dump(self.embeddings_db, f, indent=2)
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 for Ollama."""
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def _check_image_quality(self, image_path: str) -> Tuple[bool, float]:
        """Check if image quality is sufficient for processing."""
        try:
            img = Image.open(image_path)
            # Simple quality check based on resolution and format
            width, height = img.size
            pixels = width * height
            
            # Consider quality good if resolution is reasonable
            quality_score = min(100, (pixels / 1000000) * 100)  # Normalize to 100
            threshold = self.config['processing']['quality_threshold']
            
            return quality_score >= threshold, quality_score
        except Exception as e:
            print(f"Error checking image quality: {e}")
            return False, 0.0
    
    def _create_extraction_prompt(self) -> str:
        """Create the prompt for recipe extraction."""
        return """Tu es un assistant d'extraction de recettes. Analyse cette image et extrais UNIQUEMENT les informations visibles EN FRANÇAIS.

CRITIQUE: Réponds UNIQUEMENT avec du JSON valide. Pas de texte avant ou après. Commence par { et termine par }.

Structure JSON (TOUT EN FRANÇAIS):
{
  "titre": "Nom exact de la recette",
  "description": "Description courte (1 phrase max)",
  "cuisine": "Type de cuisine",
  "tags_cuisine": ["française"],
  "type_repas": "Dîner",
  "tags_repas": ["dîner", "plat_principal"],
  "tags_dietetiques": [],
  "type_regime": ["omnivore"],
  "temps_preparation": "XX minutes",
  "temps_cuisson": "XX minutes",
  "temps_total": "XX minutes",
  "portions": 4,
  "difficulte": "Facile/Moyen/Difficile",
  "ingredients": ["ingrédient avec quantité exacte"],
  "ingredients_principaux": ["ingrédient1", "ingrédient2"],
  "allergenes": [],
  "saison": [],
  "methode_cuisson": ["four"],
  "instructions": ["Étape 1 concise", "Étape 2 concise"],
  "notes": "Conseils courts",
  "confiance": 0.9
}

RÈGLES STRICTES:
- Copie EXACTEMENT le texte visible, N'INVENTE RIEN
- Instructions: MAX 10-15 étapes, CONCISES (1 phrase par étape)
- Si une étape est longue, cinde la en plusieurs étapes
- NE RÉPÈTE JAMAIS le même texte
- Si info manquante: utilise "Inconnu" ou []
- Confiance: 0.9 si clair, 0.5 si flou, 0.0 si illisible
- Tout en français (végétarien, pas vegetarian)
"""
    
    def _repair_json(self, json_str: str) -> str:
        """Attempt to repair malformed JSON."""
        import re
        
        # Fix common issues
        # 1. Remove trailing commas before closing braces/brackets
        json_str = json_str.replace(',]', ']').replace(',}', '}')
        
        # 2. Find the last complete field before truncation
        # Look for the last properly closed string value
        last_complete_field = json_str.rfind('",')
        if last_complete_field == -1:
            last_complete_field = json_str.rfind('"]')
        
        if last_complete_field > 0:
            # Truncate to last complete field
            json_str = json_str[:last_complete_field + 1]
            
            # Close any open arrays
            open_brackets = json_str.count('[') - json_str.count(']')
            json_str += ']' * open_brackets
            
            # Close the main object
            json_str += '\n}'
        else:
            # Fallback: try to close unclosed strings
            quote_count = json_str.count('"')
            if quote_count % 2 != 0:
                last_brace = json_str.rfind('}')
                if last_brace > 0:
                    json_str = json_str[:last_brace] + '"' + json_str[last_brace:]
        
        return json_str
    
    def _convert_heic_to_jpeg(self, image_path: str) -> str:
        """Convert HEIC/HEIF image to JPEG format."""
        try:
            img = Image.open(image_path)
            
            # Create JPEG path
            jpeg_path = str(Path(image_path).with_suffix('.jpg'))
            
            # Convert and save as JPEG
            if img.mode in ('RGBA', 'LA', 'P'):
                # Convert to RGB for JPEG
                img = img.convert('RGB')
            
            img.save(jpeg_path, 'JPEG', quality=95)
            print(f"✅ Converted HEIC to JPEG: {jpeg_path}")
            
            return jpeg_path
            
        except Exception as e:
            print(f"❌ Error converting HEIC: {e}")
            return image_path
    
    def extract_recipe(self, image_path: str) -> Optional[Dict]:
        """Extract recipe data from image using vision model."""
        print(f"Processing: {image_path}")
        
        # Convert HEIC to JPEG if needed
        original_path = image_path
        if image_path.lower().endswith(('.heic', '.heif')):
            if not HEIF_SUPPORT:
                print("⚠️  HEIC format detected but pillow-heif not installed")
                print("   Install with: pip3 install pillow-heif")
                return None
            image_path = self._convert_heic_to_jpeg(image_path)
        
        # Check image quality
        is_good_quality, quality_score = self._check_image_quality(image_path)
        print(f"Image quality score: {quality_score:.1f}")
        
        # Retry logic
        max_retries = self.config['extraction'].get('max_retries', 2)
        
        for attempt in range(max_retries + 1):
            if attempt > 0:
                print(f"Retry attempt {attempt}/{max_retries}...")
            
            try:
                # Call Ollama vision model with JSON format enforcement
                response = ollama.chat(
                    model=self.vision_model,
                    messages=[{
                        'role': 'user',
                        'content': self._create_extraction_prompt(),
                        'images': [image_path]
                    }],
                    format='json',  # Force JSON output
                    options={
                        'temperature': self.config['extraction']['temperature'] + (attempt * 0.1),  # Slightly increase temp on retry
                        'num_predict': self.config['extraction']['max_tokens'] + (attempt * 500)  # Allow more tokens on retry
                    }
                )
                
                # Parse JSON response
                content = response['message']['content']
                
                # Extract JSON from response with multiple strategies
                json_content = None
                
                # Strategy 1: Look for JSON in markdown code blocks
                if '```json' in content:
                    json_content = content.split('```json')[1].split('```')[0].strip()
                elif '```' in content:
                    json_content = content.split('```')[1].split('```')[0].strip()
                
                # Strategy 2: Look for JSON object starting with {
                if not json_content:
                    # Find the first { and last }
                    start_idx = content.find('{')
                    end_idx = content.rfind('}')
                    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                        json_content = content[start_idx:end_idx + 1]
                
                # Strategy 3: Try the entire content as-is
                if not json_content:
                    json_content = content
                
                if not json_content:
                    print(f"❌ Could not find JSON in response")
                    print(f"Response content: {content[:500]}...")
                    continue
                
                # Try to parse the JSON
                try:
                    recipe_data = json.loads(json_content)
                except json.JSONDecodeError as e:
                    # Try to repair the JSON
                    print(f"⚠️  Malformed JSON, attempting repair...")
                    repaired_json = self._repair_json(json_content)
                    
                    try:
                        recipe_data = json.loads(repaired_json)
                        print(f"✅ JSON repaired successfully")
                    except json.JSONDecodeError as e2:
                        if attempt < max_retries:
                            print(f"❌ JSON repair failed: {e2}")
                            print(f"Attempted to parse: {json_content[:300]}...")
                            continue
                        else:
                            print(f"❌ Final attempt failed: {e2}")
                            print(f"Attempted to parse: {json_content[:300]}...")
                            return None
                
                # Successfully parsed JSON
                # Add metadata
                recipe_data['image_source'] = os.path.basename(image_path)
                recipe_data['date_added'] = datetime.now().isoformat()
                recipe_data['quality_score'] = quality_score
                
                # Flag for review if confidence is low
                confidence = recipe_data.get('confiance', recipe_data.get('confidence', 0.0))
                threshold = self.config['validation']['manual_review_threshold']
                recipe_data['needs_review'] = confidence < threshold
                
                if recipe_data['needs_review']:
                    print(f"⚠️  Low confidence ({confidence:.2f}), flagged for review")
                
                # Save raw JSON extraction for debugging/review
                self._save_json_extraction(recipe_data, image_path)
                
                return recipe_data
                
            except Exception as e:
                if attempt < max_retries:
                    print(f"❌ Error on attempt {attempt + 1}: {e}")
                    continue
                else:
                    print(f"❌ Final attempt failed with error: {e}")
                    return None
        
        return None
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text."""
        try:
            # Truncate text to fit embedding model context window
            # nomic-embed-text: 8192 tokens (~32k chars)
            # mxbai-embed-large: 512 tokens (~2k chars)
            max_chars = 30000  # Safe limit for most models
            
            if len(text) > max_chars:
                # Prioritize title, description, and main ingredients
                text = text[:max_chars]
                print(f"⚠️  Text truncated to {max_chars} chars for embedding")
            
            response = ollama.embeddings(
                model=self.embedding_model,
                prompt=text
            )
            return response['embedding']
        except Exception as e:
            print(f"Error generating embedding: {e}")
            # Try with shorter text
            if len(text) > 2000:
                print(f"Retrying with shorter text...")
                try:
                    short_text = text[:2000]
                    response = ollama.embeddings(
                        model=self.embedding_model,
                        prompt=short_text
                    )
                    return response['embedding']
                except Exception as e2:
                    print(f"Retry failed: {e2}")
            return []
    
    def _save_json_extraction(self, recipe_data: Dict, image_path: str):
        """Save raw JSON extraction for debugging and review."""
        try:
            # Create safe filename from title
            title = recipe_data.get('titre', recipe_data.get('title', 'sans-titre'))
            filename = "".join(c if c.isalnum() or c in (' ', '-') else '_' for c in title)
            filename = filename.replace(' ', '-').lower()
            
            # Save to json-extract directory
            json_dir = Path('json-extract')
            json_dir.mkdir(exist_ok=True)
            
            json_path = json_dir / f"{filename}.json"
            
            # Ensure unique filename
            counter = 1
            while json_path.exists():
                json_path = json_dir / f"{filename}-{counter}.json"
                counter += 1
            
            # Save JSON with pretty formatting
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(recipe_data, f, ensure_ascii=False, indent=2)
            
            print(f"📄 JSON saved to: {json_path}")
            
        except Exception as e:
            print(f"⚠️  Could not save JSON extraction: {e}")
    
    def _create_recipe_text(self, recipe_data: Dict) -> str:
        """Create searchable text from recipe data."""
        parts = [
            recipe_data.get('titre', recipe_data.get('title', '')),
            recipe_data.get('description', ''),
            recipe_data.get('cuisine', ''),
            ' '.join(recipe_data.get('tags_cuisine', recipe_data.get('cuisine_tags', []))),
            ' '.join(recipe_data.get('tags_dietetiques', recipe_data.get('dietary_tags', []))),
            ' '.join(recipe_data.get('ingredients', [])),
            ' '.join(recipe_data.get('instructions', [])),
            recipe_data.get('notes', '')
        ]
        return ' '.join(filter(None, parts))
    
    def save_recipe(self, recipe_data: Dict, output_dir: str = None) -> str:
        """Save recipe data as markdown file with frontmatter."""
        if output_dir is None:
            output_dir = self.config['directories']['recipes']
        
        # Create safe filename from title (handle both French and English keys)
        title = recipe_data.get('titre', recipe_data.get('title', 'sans-titre'))
        filename = "".join(c if c.isalnum() or c in (' ', '-') else '_' for c in title)
        filename = filename.replace(' ', '-').lower()
        filepath = Path(output_dir) / f"{filename}.md"
        
        # Ensure unique filename
        counter = 1
        while filepath.exists():
            filepath = Path(output_dir) / f"{filename}-{counter}.md"
            counter += 1
        
        # Prepare frontmatter (map French keys to French field names)
        metadata = {
            'titre': recipe_data.get('titre', recipe_data.get('title', '')),
            'cuisine': recipe_data.get('cuisine', ''),
            'tags_cuisine': recipe_data.get('tags_cuisine', recipe_data.get('cuisine_tags', [])),
            'type_repas': recipe_data.get('type_repas', recipe_data.get('meal_type', '')),
            'tags_repas': recipe_data.get('tags_repas', recipe_data.get('meal_tags', [])),
            'tags_dietetiques': recipe_data.get('tags_dietetiques', recipe_data.get('dietary_tags', [])),
            'type_regime': recipe_data.get('type_regime', recipe_data.get('diet_type', [])),
            'temps_preparation': recipe_data.get('temps_preparation', recipe_data.get('prep_time', '')),
            'temps_cuisson': recipe_data.get('temps_cuisson', recipe_data.get('cook_time', '')),
            'temps_total': recipe_data.get('temps_total', recipe_data.get('total_time', '')),
            'portions': recipe_data.get('portions', recipe_data.get('servings', 0)),
            'difficulte': recipe_data.get('difficulte', recipe_data.get('difficulty', '')),
            'ingredients': recipe_data.get('ingredients', []),
            'ingredients_principaux': recipe_data.get('ingredients_principaux', recipe_data.get('main_ingredients', [])),
            'allergenes': recipe_data.get('allergenes', recipe_data.get('allergens', [])),
            'saison': recipe_data.get('saison', recipe_data.get('season', [])),
            'methode_cuisson': recipe_data.get('methode_cuisson', recipe_data.get('cooking_method', [])),
            'source': recipe_data.get('source', ''),
            'date_ajout': recipe_data.get('date_added', ''),
            'image_source': recipe_data.get('image_source', ''),
            'score_confiance': recipe_data.get('confiance', recipe_data.get('confidence', 0.0)),
            'necessite_revision': recipe_data.get('needs_review', False)
        }
        
        # Create markdown content in French
        content_parts = [
            f"# {metadata['titre']}",
            "",
            "## Description",
            recipe_data.get('description', ''),
            "",
            "## Ingrédients",
        ]
        
        for ingredient in recipe_data.get('ingredients', []):
            content_parts.append(f"- {ingredient}")
        
        content_parts.extend([
            "",
            "## Instructions",
        ])
        
        for i, instruction in enumerate(recipe_data.get('instructions', []), 1):
            content_parts.append(f"{i}. {instruction}")
        
        if recipe_data.get('notes'):
            content_parts.extend([
                "",
                "## Notes",
                recipe_data.get('notes', '')
            ])
        
        content = '\n'.join(content_parts)
        
        # Create post with frontmatter
        post = frontmatter.Post(content, **metadata)
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))
        
        print(f"✅ Saved recipe to: {filepath}")
        
        # Generate and store embedding if enabled
        if self.config['processing']['generate_embeddings']:
            recipe_text = self._create_recipe_text(recipe_data)
            embedding = self._generate_embedding(recipe_text)
            
            if embedding:
                recipe_id = filepath.stem
                self.embeddings_db['recipes'][recipe_id] = embedding
                self.embeddings_db['metadata'][recipe_id] = {
                    'title': recipe_data.get('title', ''),
                    'filepath': str(filepath),
                    'date_added': recipe_data.get('date_added', '')
                }
                self._save_embeddings()
                print(f"✅ Generated embedding for semantic search")
        
        return str(filepath)
    
    def process_image(self, image_path: str) -> Optional[str]:
        """Process a single image and save as recipe."""
        recipe_data = self.extract_recipe(image_path)
        
        if recipe_data:
            return self.save_recipe(recipe_data)
        return None
    
    def process_batch(self, image_dir: str = None) -> List[str]:
        """Process all images in a directory."""
        if image_dir is None:
            image_dir = self.config['directories']['images']
        
        image_dir = Path(image_dir)
        image_extensions = {'.jpg', '.jpeg', '.png', '.heic', '.heif'}
        
        # Find all image files
        image_files = [
            f for f in image_dir.iterdir()
            if f.suffix.lower() in image_extensions
        ]
        
        if not image_files:
            print(f"No images found in {image_dir}")
            return []
        
        print(f"Found {len(image_files)} images to process")
        
        processed_files = []
        failed_files = []
        
        for i, image_path in enumerate(image_files, 1):
            print(f"\n[{i}/{len(image_files)}] Processing {image_path.name}")
            
            try:
                result = self.process_image(str(image_path))
                if result:
                    processed_files.append(result)
                else:
                    failed_files.append(str(image_path))
            except Exception as e:
                print(f"❌ Failed to process {image_path.name}: {e}")
                failed_files.append(str(image_path))
        
        # Print summary
        print("\n" + "="*60)
        print(f"Processing complete!")
        print(f"✅ Successfully processed: {len(processed_files)}")
        print(f"❌ Failed: {len(failed_files)}")
        
        if failed_files:
            print("\nFailed files:")
            for f in failed_files:
                print(f"  - {f}")
        
        return processed_files


def main():
    """Main entry point for the script."""
    import argparse
    
    # Initialize logger
    logger = DualLogger('process_images')
    
    try:
        parser = argparse.ArgumentParser(description='Process recipe images to markdown')
        parser.add_argument('image', nargs='?', help='Single image file to process')
        parser.add_argument('--batch', action='store_true', help='Process all images in images/ directory')
        parser.add_argument('--config', default='config.yaml', help='Path to config file')
        
        args = parser.parse_args()
        
        processor = RecipeProcessor(args.config)
        
        if args.batch:
            logger.info("Starting batch processing...")
            processor.process_batch()
        elif args.image:
            logger.info(f"Processing single image: {args.image}")
            processor.process_image(args.image)
        else:
            logger.info("Usage:")
            logger.info("  Process single image: python process_images.py path/to/image.jpg")
            logger.info("  Process batch:        python process_images.py --batch")
            sys.exit(1)
        
        # Log completion
        logger.finalize()
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Process interrupted by user")
        logger.finalize()
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        logger.finalize()
        sys.exit(1)


if __name__ == '__main__':
    main()

# Made with Bob
