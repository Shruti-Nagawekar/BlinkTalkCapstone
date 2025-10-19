"""
Tests for sequences loader utility.
"""
import pytest
import json
import tempfile
from pathlib import Path
from core.sequences_loader import SequencesLoader

def test_sequences_loader():
    """Test loading sequences from JSON file."""
    # Create temporary sequences file
    test_data = {
        "$schema_version": "1.0",
        "meta": {
            "units": {
                "short_max_ms": 350,
                "long_min_ms": 351,
                "long_max_ms": 900
            },
            "gaps": {
                "symbol_gap_max_ms": 450,
                "word_gap_min_ms": 1100
            }
        },
        "vocab": [
            {"word": "yes", "pattern": "S S"},
            {"word": "no", "pattern": "L"}
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_data, f)
        temp_file = f.name
    
    try:
        loader = SequencesLoader(temp_file)
        
        # Test vocabulary loading
        vocab = loader.get_vocabulary()
        assert vocab["S S"] == "yes"
        assert vocab["L"] == "no"
        
        # Test metadata loading
        meta = loader.get_meta()
        assert meta["units"]["short_max_ms"] == 350
        assert meta["gaps"]["word_gap_min_ms"] == 1100
        
        # Test pattern lookup
        assert loader.get_word_for_pattern("S S") == "yes"
        assert loader.get_word_for_pattern("L") == "no"
        assert loader.get_word_for_pattern("unknown") is None
        
        # Test pattern/word lists
        patterns = loader.get_all_patterns()
        assert "S S" in patterns
        assert "L" in patterns
        
        words = loader.get_all_words()
        assert "yes" in words
        assert "no" in words
        
    finally:
        Path(temp_file).unlink()

def test_sequences_loader_file_not_found():
    """Test error handling for missing file."""
    with pytest.raises(FileNotFoundError):
        SequencesLoader("nonexistent.json")

def test_sequences_loader_invalid_json():
    """Test error handling for invalid JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("invalid json content")
        temp_file = f.name
    
    try:
        with pytest.raises(ValueError):
            SequencesLoader(temp_file)
    finally:
        Path(temp_file).unlink()

