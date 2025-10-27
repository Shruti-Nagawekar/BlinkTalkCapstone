"""
Vocabulary API endpoints for BlinkTalk system.
Returns available vocabulary from sequences_v1.json.
"""
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from core.sequences_loader import SequencesLoader

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/vocabulary", tags=["vocabulary"])

# Global loader instance
_loader = None

def get_loader() -> SequencesLoader:
    """Get or create the global sequences loader instance."""
    global _loader
    if _loader is None:
        _loader = SequencesLoader()
    return _loader

class VocabularyItem(BaseModel):
    """Model for a vocabulary item."""
    word: str
    pattern: str

class VocabularyResponse(BaseModel):
    """Response model for vocabulary operations."""
    items: List[VocabularyItem]
    count: int

class VocabularyWordListResponse(BaseModel):
    """Response model for word list."""
    words: List[str]

class VocabularyPatternListResponse(BaseModel):
    """Response model for pattern list."""
    patterns: List[str]

class VocabularySearchResponse(BaseModel):
    """Response model for vocabulary search."""
    found: bool
    word: str | None = None
    pattern: str | None = None

@router.get("", response_model=VocabularyResponse)
async def get_vocabulary():
    """
    Get the complete vocabulary list.
    
    Returns all available words and their corresponding blink patterns
    from sequences_v1.json.
    
    Returns:
        Vocabulary response with all vocabulary items and count
        
    Raises:
        HTTPException: If vocabulary cannot be loaded
    """
    try:
        loader = get_loader()
        vocab = loader.get_vocabulary()
        
        items = [
            VocabularyItem(word=word, pattern=pattern)
            for pattern, word in vocab.items()
        ]
        
        # Sort by word alphabetically
        items.sort(key=lambda x: x.word)
        
        logger.info(f"Returning vocabulary with {len(items)} items")
        
        return VocabularyResponse(
            items=items,
            count=len(items)
        )
        
    except FileNotFoundError as e:
        logger.error(f"Vocabulary file not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vocabulary file not found"
        )
    except Exception as e:
        logger.error(f"Error loading vocabulary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error loading vocabulary"
        )

@router.get("/words", response_model=VocabularyWordListResponse)
async def get_words():
    """
    Get list of all available words.
    
    Returns:
        List of all vocabulary words, sorted alphabetically
        
    Raises:
        HTTPException: If vocabulary cannot be loaded
    """
    try:
        loader = get_loader()
        words = loader.get_all_words()
        words.sort()
        
        logger.info(f"Returning {len(words)} vocabulary words")
        
        return VocabularyWordListResponse(words=words)
        
    except Exception as e:
        logger.error(f"Error getting words list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error getting words list"
        )

@router.get("/patterns", response_model=VocabularyPatternListResponse)
async def get_patterns():
    """
    Get list of all available patterns.
    
    Returns:
        List of all vocabulary patterns
        
    Raises:
        HTTPException: If vocabulary cannot be loaded
    """
    try:
        loader = get_loader()
        patterns = loader.get_all_patterns()
        
        logger.info(f"Returning {len(patterns)} vocabulary patterns")
        
        return VocabularyPatternListResponse(patterns=patterns)
        
    except Exception as e:
        logger.error(f"Error getting patterns list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error getting patterns list"
        )

@router.get("/search/{word}")
async def search_word(word: str) -> VocabularySearchResponse:
    """
    Search for a word in the vocabulary.
    
    Args:
        word: The word to search for
        
    Returns:
        Vocabulary search response indicating if word exists and its pattern
        
    Raises:
        HTTPException: If vocabulary cannot be loaded
    """
    try:
        loader = get_loader()
        vocab = loader.get_vocabulary()
        
        # Find the pattern for the word (reverse lookup)
        pattern = None
        for p, w in vocab.items():
            if w == word:
                pattern = p
                break
        
        if pattern:
            logger.info(f"Found word '{word}' with pattern '{pattern}'")
            return VocabularySearchResponse(found=True, word=word, pattern=pattern)
        else:
            logger.info(f"Word '{word}' not found in vocabulary")
            return VocabularySearchResponse(found=False, word=None, pattern=None)
        
    except Exception as e:
        logger.error(f"Error searching for word '{word}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error searching for word"
        )

@router.get("/pattern/{pattern}")
async def get_word_for_pattern(pattern: str) -> Dict[str, Any]:
    """
    Get the word for a specific pattern.
    
    Args:
        pattern: The blink pattern (e.g., "S L")
        
    Returns:
        Dictionary with pattern and word information
        
    Raises:
        HTTPException: If pattern not found or vocabulary cannot be loaded
    """
    try:
        loader = get_loader()
        word = loader.get_word_for_pattern(pattern)
        
        if word:
            logger.info(f"Pattern '{pattern}' maps to word '{word}'")
            return {
                "pattern": pattern,
                "word": word,
                "found": True
            }
        else:
            logger.warning(f"Pattern '{pattern}' not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pattern '{pattern}' not found in vocabulary"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting word for pattern '{pattern}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error getting word for pattern"
        )

@router.get("/count")
async def get_vocabulary_count() -> Dict[str, int]:
    """
    Get vocabulary statistics.
    
    Returns:
        Dictionary with vocabulary count information
    """
    try:
        loader = get_loader()
        vocab = loader.get_vocabulary()
        
        return {
            "total_words": len(vocab),
            "total_patterns": len(vocab)
        }
        
    except Exception as e:
        logger.error(f"Error getting vocabulary count: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error getting vocabulary count"
        )

@router.post("/reload")
async def reload_vocabulary() -> Dict[str, Any]:
    """
    Reload vocabulary from sequences_v1.json.
    
    Useful for updating vocabulary without restarting the server.
    
    Returns:
        Confirmation message
    """
    try:
        loader = get_loader()
        loader.reload()
        
        logger.info("Vocabulary reloaded successfully")
        
        return {
            "message": "Vocabulary reloaded successfully",
            "count": len(loader.get_vocabulary())
        }
        
    except FileNotFoundError as e:
        logger.error(f"Vocabulary file not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vocabulary file not found"
        )
    except Exception as e:
        logger.error(f"Error reloading vocabulary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reloading vocabulary: {str(e)}"
        )

