"""
Tests for vocabulary API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


class TestVocabularyAPI:
    """Test suite for vocabulary API endpoints."""
    
    def test_get_vocabulary(self):
        """Test getting the complete vocabulary list."""
        response = client.get("/api/vocabulary")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "count" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["count"], int)
        assert data["count"] > 0
        
        # Check structure of items
        if len(data["items"]) > 0:
            item = data["items"][0]
            assert "word" in item
            assert "pattern" in item
            assert isinstance(item["word"], str)
            assert isinstance(item["pattern"], str)
    
    def test_get_words_list(self):
        """Test getting list of all words."""
        response = client.get("/api/vocabulary/words")
        
        assert response.status_code == 200
        data = response.json()
        assert "words" in data
        assert isinstance(data["words"], list)
        assert len(data["words"]) > 0
        
        # Verify all items are strings
        for word in data["words"]:
            assert isinstance(word, str)
    
    def test_get_patterns_list(self):
        """Test getting list of all patterns."""
        response = client.get("/api/vocabulary/patterns")
        
        assert response.status_code == 200
        data = response.json()
        assert "patterns" in data
        assert isinstance(data["patterns"], list)
        assert len(data["patterns"]) > 0
        
        # Verify all items are strings
        for pattern in data["patterns"]:
            assert isinstance(pattern, str)
    
    def test_search_word_found(self):
        """Test searching for a word that exists."""
        # First get the vocabulary to find a real word
        vocab_response = client.get("/api/vocabulary")
        assert vocab_response.status_code == 200
        vocab_data = vocab_response.json()
        
        if vocab_data["items"]:
            real_word = vocab_data["items"][0]["word"]
            response = client.get(f"/api/vocabulary/search/{real_word}")
            
            assert response.status_code == 200
            data = response.json()
            assert "found" in data
            assert data["found"] is True
    
    def test_search_word_not_found(self):
        """Test searching for a word that doesn't exist."""
        response = client.get("/api/vocabulary/search/nonexistentwordxyz123")
        
        assert response.status_code == 200
        data = response.json()
        assert "found" in data
        assert data["found"] is False
    
    def test_get_word_for_pattern_valid(self):
        """Test getting word for a valid pattern."""
        response = client.get("/api/vocabulary/pattern/S S")
        
        assert response.status_code == 200
        data = response.json()
        assert "pattern" in data
        assert "word" in data
        assert "found" in data
        assert data["found"] is True
    
    def test_get_word_for_pattern_invalid(self):
        """Test getting word for an invalid pattern."""
        response = client.get("/api/vocabulary/pattern/INVALID PATTERN")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    def test_get_vocabulary_count(self):
        """Test getting vocabulary count."""
        response = client.get("/api/vocabulary/count")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_words" in data
        assert "total_patterns" in data
        assert isinstance(data["total_words"], int)
        assert isinstance(data["total_patterns"], int)
        assert data["total_words"] > 0
        assert data["total_patterns"] > 0
    
    def test_reload_vocabulary(self):
        """Test reloading vocabulary."""
        response = client.post("/api/vocabulary/reload")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "count" in data
        assert "reloaded" in data["message"].lower() or "success" in data["message"].lower()
    
    def test_vocabulary_integrity(self):
        """Test that vocabulary data is consistent."""
        vocab_response = client.get("/api/vocabulary")
        words_response = client.get("/api/vocabulary/words")
        patterns_response = client.get("/api/vocabulary/patterns")
        count_response = client.get("/api/vocabulary/count")
        
        # All should succeed
        assert vocab_response.status_code == 200
        assert words_response.status_code == 200
        assert patterns_response.status_code == 200
        assert count_response.status_code == 200
        
        vocab_data = vocab_response.json()
        words_data = words_response.json()
        patterns_data = patterns_response.json()
        count_data = count_response.json()
        
        # Count should match
        assert vocab_data["count"] == count_data["total_words"]
        assert vocab_data["count"] == count_data["total_patterns"]
        assert vocab_data["count"] == len(words_data["words"])
        assert vocab_data["count"] == len(patterns_data["patterns"])
        
        # Each item should have both word and pattern
        for item in vocab_data["items"]:
            assert item["word"] in words_data["words"]
            assert item["pattern"] in patterns_data["patterns"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

