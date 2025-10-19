"""
Unit tests for the sequence engine.
"""
import pytest
import tempfile
import json
from pathlib import Path
from core.sequence_engine import SequenceEngine


@pytest.fixture
def temp_sequences_file():
    """Create a temporary sequences file for testing."""
    sequences_data = {
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
            },
            "notes": "Test sequences"
        },
        "vocab": [
            {"word": "yes", "pattern": "S S"},
            {"word": "no", "pattern": "L"},
            {"word": "thirsty", "pattern": "S L"},
            {"word": "hungry", "pattern": "L S"},
            {"word": "pain", "pattern": "S S L"},
            {"word": "tired", "pattern": "L L"},
            {"word": "light", "pattern": "S S S"},
            {"word": "temp", "pattern": "S L L"},
            {"word": "bored", "pattern": "L S S"},
            {"word": "feelings", "pattern": "L L S"}
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sequences_data, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def sequence_engine(temp_sequences_file):
    """Create a sequence engine instance for testing."""
    return SequenceEngine(temp_sequences_file)


class TestSequenceEngine:
    """Test cases for SequenceEngine."""
    
    def test_initialization(self, sequence_engine):
        """Test sequence engine initialization."""
        assert sequence_engine is not None
        assert len(sequence_engine.get_vocabulary()) == 10
        assert sequence_engine.get_current_sequence() == []
        assert not sequence_engine.is_sequence_complete()
        assert sequence_engine.get_last_word() == ""
    
    def test_add_blink_valid(self, sequence_engine):
        """Test adding valid blinks to sequence."""
        sequence_engine.add_blink("S")
        assert sequence_engine.get_current_sequence() == ["S"]
        
        sequence_engine.add_blink("L")
        assert sequence_engine.get_current_sequence() == ["S", "L"]
        
        sequence_engine.add_blink("S")
        assert sequence_engine.get_current_sequence() == ["S", "L", "S"]
    
    def test_add_blink_invalid(self, sequence_engine, caplog):
        """Test adding invalid blink types."""
        sequence_engine.add_blink("X")  # Invalid
        assert sequence_engine.get_current_sequence() == []
        assert "Invalid blink type: X" in caplog.text
        
        sequence_engine.add_blink("")  # Empty
        assert sequence_engine.get_current_sequence() == []
    
    def test_exact_matches(self, sequence_engine):
        """Test exact pattern matching."""
        # Test "yes" (S S)
        sequence_engine.add_blink("S")
        sequence_engine.add_blink("S")
        result = sequence_engine.finalize_sequence()
        assert result == "yes"
        assert sequence_engine.is_sequence_complete()
        assert sequence_engine.get_last_word() == "yes"
        
        # Reset and test "no" (L)
        sequence_engine.clear_sequence()
        sequence_engine.add_blink("L")
        result = sequence_engine.finalize_sequence()
        assert result == "no"
        
        # Reset and test "thirsty" (S L)
        sequence_engine.clear_sequence()
        sequence_engine.add_blink("S")
        sequence_engine.add_blink("L")
        result = sequence_engine.finalize_sequence()
        assert result == "thirsty"
        
        # Reset and test "pain" (S S L)
        sequence_engine.clear_sequence()
        sequence_engine.add_blink("S")
        sequence_engine.add_blink("S")
        sequence_engine.add_blink("L")
        result = sequence_engine.finalize_sequence()
        assert result == "pain"
    
    def test_fuzzy_matching_single_symbol_difference(self, sequence_engine):
        """Test fuzzy matching with single symbol difference."""
        # Test "S L" vs "S S" (should match "thirsty" not "yes")
        sequence_engine.add_blink("S")
        sequence_engine.add_blink("L")
        result = sequence_engine.finalize_sequence()
        assert result == "thirsty"  # Exact match
        
        # Test "S S" vs "S L" (should match "yes" not "thirsty")
        sequence_engine.clear_sequence()
        sequence_engine.add_blink("S")
        sequence_engine.add_blink("S")
        result = sequence_engine.finalize_sequence()
        assert result == "yes"  # Exact match
        
        # Test fuzzy match: "S S S" vs "S S L" (should match "light")
        sequence_engine.clear_sequence()
        sequence_engine.add_blink("S")
        sequence_engine.add_blink("S")
        sequence_engine.add_blink("S")
        result = sequence_engine.finalize_sequence()
        assert result == "light"  # Exact match
    
    def test_fuzzy_matching_insertion_deletion(self, sequence_engine):
        """Test fuzzy matching with insertion/deletion."""
        # Test insertion: "S" vs "S S" (should not match anything)
        sequence_engine.add_blink("S")
        result = sequence_engine.finalize_sequence()
        # This should not match anything as "S" alone is not in vocabulary
        assert result is None
        
        # Test deletion: "S S S S" vs "S S S" (should match "light" via fuzzy matching)
        sequence_engine.clear_sequence()
        sequence_engine.add_blink("S")
        sequence_engine.add_blink("S")
        sequence_engine.add_blink("S")
        sequence_engine.add_blink("S")
        result = sequence_engine.finalize_sequence()
        # This should match "light" as "S S S S" is close to "S S S" (light)
        assert result == "light"
    
    def test_no_match(self, sequence_engine):
        """Test sequences that don't match any vocabulary."""
        # Test completely different pattern that's not in vocabulary
        sequence_engine.add_blink("L")
        sequence_engine.add_blink("L")
        sequence_engine.add_blink("L")
        sequence_engine.add_blink("L")  # L L L L is not in vocabulary
        result = sequence_engine.finalize_sequence()
        assert result is None
        assert not sequence_engine.is_sequence_complete()
    
    def test_empty_sequence(self, sequence_engine):
        """Test finalizing empty sequence."""
        result = sequence_engine.finalize_sequence()
        assert result is None
        assert not sequence_engine.is_sequence_complete()
    
    def test_clear_sequence(self, sequence_engine):
        """Test clearing sequence."""
        sequence_engine.add_blink("S")
        sequence_engine.add_blink("S")
        assert sequence_engine.get_current_sequence() == ["S", "S"]
        
        sequence_engine.clear_sequence()
        assert sequence_engine.get_current_sequence() == []
        assert not sequence_engine.is_sequence_complete()
    
    def test_sequence_state_management(self, sequence_engine):
        """Test sequence state management."""
        # Initially empty
        assert not sequence_engine.is_sequence_complete()
        assert sequence_engine.get_last_word() == ""
        
        # Add blinks
        sequence_engine.add_blink("S")
        sequence_engine.add_blink("S")
        assert not sequence_engine.is_sequence_complete()
        
        # Finalize
        result = sequence_engine.finalize_sequence()
        assert result == "yes"
        assert sequence_engine.is_sequence_complete()
        assert sequence_engine.get_last_word() == "yes"
        
        # Clear and reset
        sequence_engine.clear_sequence()
        assert not sequence_engine.is_sequence_complete()
        assert sequence_engine.get_last_word() == "yes"  # Last word persists
    
    def test_vocabulary_access(self, sequence_engine):
        """Test vocabulary access methods."""
        vocab = sequence_engine.get_vocabulary()
        assert isinstance(vocab, dict)
        assert len(vocab) == 10
        assert "S S" in vocab
        assert vocab["S S"] == "yes"
        assert "L" in vocab
        assert vocab["L"] == "no"
        
        # Test that returned vocab is a copy
        vocab["S S"] = "modified"
        assert sequence_engine.get_vocabulary()["S S"] == "yes"
    
    def test_meta_access(self, sequence_engine):
        """Test metadata access methods."""
        meta = sequence_engine.get_meta()
        assert isinstance(meta, dict)
        assert "units" in meta
        assert "gaps" in meta
        assert meta["units"]["short_max_ms"] == 350
        assert meta["gaps"]["word_gap_min_ms"] == 1100
        
        # Test that returned meta is a copy
        meta["units"]["short_max_ms"] = 999
        assert sequence_engine.get_meta()["units"]["short_max_ms"] == 350
    
    def test_complex_sequence(self, sequence_engine):
        """Test complex sequence patterns."""
        # Test "feelings" (L L S)
        sequence_engine.add_blink("L")
        sequence_engine.add_blink("L")
        sequence_engine.add_blink("S")
        result = sequence_engine.finalize_sequence()
        assert result == "feelings"
        
        # Reset and test "bored" (L S S)
        sequence_engine.clear_sequence()
        sequence_engine.add_blink("L")
        sequence_engine.add_blink("S")
        sequence_engine.add_blink("S")
        result = sequence_engine.finalize_sequence()
        assert result == "bored"
        
        # Reset and test "temp" (S L L)
        sequence_engine.clear_sequence()
        sequence_engine.add_blink("S")
        sequence_engine.add_blink("L")
        sequence_engine.add_blink("L")
        result = sequence_engine.finalize_sequence()
        assert result == "temp"
    
    def test_sequence_persistence(self, sequence_engine):
        """Test that sequences persist until cleared."""
        sequence_engine.add_blink("S")
        sequence_engine.add_blink("S")
        assert sequence_engine.get_current_sequence() == ["S", "S"]
        
        # Add more blinks
        sequence_engine.add_blink("L")
        assert sequence_engine.get_current_sequence() == ["S", "S", "L"]
        
        # Finalize should work with accumulated sequence
        result = sequence_engine.finalize_sequence()
        assert result == "pain"
    
    def test_multiple_finalizations(self, sequence_engine):
        """Test multiple finalizations of the same sequence."""
        sequence_engine.add_blink("S")
        sequence_engine.add_blink("S")
        
        # First finalization
        result1 = sequence_engine.finalize_sequence()
        assert result1 == "yes"
        assert sequence_engine.is_sequence_complete()
        
        # Second finalization should return the same result
        result2 = sequence_engine.finalize_sequence()
        assert result2 == "yes"
        assert sequence_engine.is_sequence_complete()
        
        # Clear and test again
        sequence_engine.clear_sequence()
        sequence_engine.add_blink("L")
        result3 = sequence_engine.finalize_sequence()
        assert result3 == "no"
