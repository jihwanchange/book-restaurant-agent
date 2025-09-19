#!/usr/bin/env python3
"""
Set up Qdrant vector database and create embeddings for restaurant search.
Uses Hugging Face sentence-transformers for generating embeddings.
"""

import json
import logging
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import numpy as np
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RestaurantVectorDB:
    def __init__(self,
                 host: str = "localhost",
                 port: int = 6333,
                 model_name: str = "all-MiniLM-L6-v2"):
        """Initialize Qdrant client and embedding model."""

        # Initialize Qdrant client (will use in-memory if server not available)
        try:
            self.client = QdrantClient(host=host, port=port)
            logger.info(f"Connected to Qdrant server at {host}:{port}")
        except Exception as e:
            logger.info(f"Cannot connect to Qdrant server: {e}")
            logger.info("Using in-memory Qdrant client")
            self.client = QdrantClient(":memory:")

        # Initialize embedding model (force CPU to avoid GPU compatibility issues)
        logger.info(f"Loading embedding model: {model_name}")
        import torch
        device = "cpu"  # Force CPU usage
        self.model = SentenceTransformer(model_name, device=device)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"Embedding dimension: {self.embedding_dim}")
        logger.info(f"Using device: {device}")

        self.collection_name = "restaurants"

    def create_collection(self):
        """Create Qdrant collection for restaurants."""
        try:
            # Delete existing collection if it exists
            try:
                self.client.delete_collection(self.collection_name)
                logger.info("Deleted existing collection")
            except:
                pass

            # Create new collection
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created collection '{self.collection_name}'")

        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            raise

    def generate_embeddings(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Generate embeddings for a list of texts."""
        logger.info(f"Generating embeddings for {len(texts)} texts")

        embeddings = []
        for i in tqdm(range(0, len(texts), batch_size), desc="Generating embeddings"):
            batch = texts[i:i + batch_size]
            batch_embeddings = self.model.encode(batch, convert_to_numpy=True)
            embeddings.extend(batch_embeddings)

        return np.array(embeddings)

    def index_restaurants(self, restaurants_file: str):
        """Index restaurants from JSON file into Qdrant."""

        # Load restaurants
        with open(restaurants_file, 'r', encoding='utf-8') as f:
            restaurants = json.load(f)

        logger.info(f"Loading {len(restaurants)} restaurants")

        # Prepare texts for embedding
        texts = []
        for restaurant in restaurants:
            # Use the enhanced description for embedding
            text = restaurant.get('description', '') or restaurant.get('search_text', '')
            if not text:
                # Fallback: create basic text from name and categories
                name = restaurant.get('name', '')
                categories = ', '.join(restaurant.get('categories', []))
                text = f"{name} {categories}"
            texts.append(text)

        # Generate embeddings
        embeddings = self.generate_embeddings(texts)

        # Prepare points for Qdrant
        points = []
        for i, (restaurant, embedding) in enumerate(zip(restaurants, embeddings)):
            point = PointStruct(
                id=i,
                vector=embedding.tolist(),
                payload={
                    "restaurant_id": restaurant.get('id', f'rest_{i}'),
                    "name": restaurant.get('name', ''),
                    "categories": restaurant.get('categories', []),
                    "city": restaurant.get('city', ''),
                    "state": restaurant.get('state', ''),
                    "stars": restaurant.get('stars', 0),
                    "review_count": restaurant.get('review_count', 0),
                    "description": restaurant.get('description', ''),
                    "search_text": restaurant.get('search_text', ''),
                    "location": restaurant.get('location', {}),
                    "ambiences": restaurant.get('ambiences', []),
                    "good_for_meals": restaurant.get('good_for_meals', []),
                    "good_for_kids": restaurant.get('good_for_kids', False),
                    "dogs_allowed": restaurant.get('dogs_allowed', False),
                    "address": restaurant.get('address', ''),
                }
            )
            points.append(point)

        # Upload to Qdrant
        logger.info("Uploading points to Qdrant...")
        self.client.upload_points(
            collection_name=self.collection_name,
            points=points
        )

        logger.info(f"Successfully indexed {len(points)} restaurants")

        # Print collection info
        collection_info = self.client.get_collection(self.collection_name)
        logger.info(f"Collection info: {collection_info}")

    def search_restaurants(self,
                          query: str,
                          limit: int = 5,
                          score_threshold: float = 0.3) -> List[Dict]:
        """Search for restaurants using semantic similarity."""

        # Generate query embedding
        query_embedding = self.model.encode([query], convert_to_numpy=True)[0]

        # Search in Qdrant
        search_results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding.tolist(),
            limit=limit,
            score_threshold=score_threshold
        )

        # Format results
        results = []
        for result in search_results:
            results.append({
                "score": result.score,
                "restaurant": result.payload
            })

        return results

def main():
    """Main function to set up Qdrant and index restaurants."""

    # Initialize vector DB
    vector_db = RestaurantVectorDB()

    # Create collection
    vector_db.create_collection()

    # Index restaurants with smart filtering
    restaurants_file = "yelp/restaurants_smart_enhanced.json"
    vector_db.index_restaurants(restaurants_file)

    # Test search
    logger.info("\n=== Testing search functionality ===")
    test_queries = [
        "Italian restaurant for dinner",
        "Coffee shop with wifi",
        "Family-friendly breakfast place",
        "Trendy bar for drinks",
        "Asian food delivery"
    ]

    for query in test_queries:
        logger.info(f"\nQuery: '{query}'")
        results = vector_db.search_restaurants(query, limit=3)

        for i, result in enumerate(results, 1):
            restaurant = result['restaurant']
            logger.info(f"  {i}. {restaurant['name']} ({result['score']:.3f})")
            logger.info(f"     Categories: {', '.join(restaurant['categories'])}")
            logger.info(f"     Location: {restaurant['city']}, {restaurant['state']}")

    logger.info("\n=== Setup completed successfully! ===")

if __name__ == "__main__":
    main()