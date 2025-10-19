"""
Utility for loading and managing sequences vocabulary.
"""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

class SequencesLoader:
    """Loads and manages the sequences vocabulary from JSON."""
    
    def __init__(self, sequences_file: str = "sequences_v1.json"):
        """Initialize with path to sequences file."""
        self.sequences_file = Path(sequences_file)
        self.data = {}
        self.vocab = {}
        self.meta = {}
        self._load()
    
    def _load(self) -> None:
        """Load sequences from JSON file."""
        try:
            with open(self.sequences_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            # Extract vocabulary as pattern -> word mapping
            self.vocab = {}
            for item in self.data.get('vocab', []):
                pattern = item.get('pattern', '')
                word = item.get('word', '')
                if pattern and word:
                    self.vocab[pattern] = word
            
            # Extract metadata
            self.meta = self.data.get('meta', {})
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Sequences file not found: {self.sequences_file}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in sequences file: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading sequences: {e}")
    
    def get_vocabulary(self) -> Dict[str, str]:
        """Get vocabulary as pattern -> word mapping."""
        return self.vocab.copy()
    
    def get_meta(self) -> Dict[str, Any]:
        """Get metadata including timing thresholds."""
        return self.meta.copy()
    
    def get_word_for_pattern(self, pattern: str) -> Optional[str]:
        """Get word for a specific pattern."""
        return self.vocab.get(pattern)
    
    def get_all_patterns(self) -> List[str]:
        """Get all available patterns."""
        return list(self.vocab.keys())
    
    def get_all_words(self) -> List[str]:
        """Get all available words."""
        return list(self.vocab.values())
    
    def reload(self) -> None:
        """Reload sequences from file."""
        self._load()

