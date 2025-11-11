"""
Sequence engine for processing blink patterns and matching to vocabulary.
"""
import logging
from typing import List, Optional, Dict, Any
from .sequences_loader import SequencesLoader
from .blink_classifier import BlinkType

# Configure logging
logger = logging.getLogger(__name__)

class SequenceEngine:
    """Main engine for processing blink sequences and matching to words."""
    
    def __init__(self, sequences_file: str = "sequences_v1.json"):
        """Initialize the sequence engine with vocabulary data."""
        self.sequences_file = sequences_file
        self.loader = SequencesLoader(sequences_file)
        self.vocab = self.loader.get_vocabulary()
        self.meta = self.loader.get_meta()
        self.current_sequence = []
        self.last_word = ""
        self.sequence_complete = False
        self.max_sequence_length = 4  # Maximum sequence length (longest vocab is 3, 4 allows fuzzy matching)
        
        # Log initialization
        logger.info(f"SequenceEngine initialized with {len(self.vocab)} vocabulary entries, max_sequence_length={self.max_sequence_length}")
    
    def add_blink(self, blink_type: str) -> None:
        """
        Add a blink to the current sequence.
        
        Args:
            blink_type: "S" for short blink, "L" for long blink
        """
        if blink_type not in ["S", "L"]:
            logger.warning(f"Invalid blink type: {blink_type}, ignoring")
            return
        
        # Don't add blinks if sequence is already complete
        if self.sequence_complete:
            logger.warning(f"⚠️ Sequence already complete, ignoring blink '{blink_type}'. Last word: '{self.last_word}'")
            print(f"⚠️ DEBUG: Sequence already complete (word: '{self.last_word}'), ignoring blink '{blink_type}'")
            return
        
        # Check if sequence is already at max length
        if len(self.current_sequence) >= self.max_sequence_length:
            logger.warning(f"⚠️ Sequence already at max length ({self.max_sequence_length}), ignoring blink '{blink_type}'. Current: {self.current_sequence}")
            print(f"⚠️ DEBUG: Sequence at max length, auto-finalizing before adding new blink")
            self.finalize_sequence()
            return
        
        self.current_sequence.append(blink_type)
        logger.info(f"✅ Added blink '{blink_type}' to sequence: {self.current_sequence} (length: {len(self.current_sequence)}/{self.max_sequence_length})")
        print(f"✅ DEBUG: Added blink '{blink_type}', sequence: {self.current_sequence} (length: {len(self.current_sequence)}/{self.max_sequence_length})")
        
        # Auto-finalize if we've reached max length
        if len(self.current_sequence) >= self.max_sequence_length:
            logger.info(f"🔄 Sequence reached max length ({self.max_sequence_length}), auto-finalizing...")
            print(f"🔄 DEBUG: Sequence reached max length ({self.max_sequence_length}), auto-finalizing...")
            self.finalize_sequence()
    
    def finalize_sequence(self) -> Optional[str]:
        """
        Finalize current sequence and return matched word.
        
        Returns:
            Matched word if found, None if no match
        """
        if not self.current_sequence:
            logger.debug("No sequence to finalize")
            print("⚠️ DEBUG: finalize_sequence() called but sequence is empty")
            return None
        
        # Convert sequence to pattern string
        pattern = " ".join(self.current_sequence)
        logger.info(f"Finalizing sequence: {pattern}")
        print(f"🔍 DEBUG: Finalizing sequence: '{pattern}' (length: {len(self.current_sequence)})")
        
        # Try exact match first
        if pattern in self.vocab:
            word = self.vocab[pattern]
            self.last_word = word
            self.sequence_complete = True
            logger.info(f"Exact match found: '{pattern}' -> '{word}'")
            print(f"✅ DEBUG: Exact match found: '{pattern}' -> '{word}'")
            return word
        
        # Try fuzzy matching (off-by-one symbol tolerance)
        word = self._fuzzy_match(pattern)
        if word:
            self.last_word = word
            self.sequence_complete = True
            logger.info(f"Fuzzy match found: '{pattern}' -> '{word}'")
            print(f"✅ DEBUG: Fuzzy match found: '{pattern}' -> '{word}'")
            return word
        
        logger.warning(f"No match found for sequence: {pattern}")
        print(f"❌ DEBUG: No match found for sequence: '{pattern}'")
        return None
    
    def _fuzzy_match(self, pattern: str) -> Optional[str]:
        """
        Try to find a close match with off-by-one symbol tolerance.
        
        Args:
            pattern: The pattern to match (e.g., "S L S")
            
        Returns:
            Matched word if found, None otherwise
        """
        pattern_parts = pattern.split()
        
        for vocab_pattern, word in self.vocab.items():
            vocab_parts = vocab_pattern.split()
            
            # Check if lengths differ by at most 1
            if abs(len(pattern_parts) - len(vocab_parts)) > 1:
                continue
            
            # Check for exact match (should have been caught above, but just in case)
            if pattern == vocab_pattern:
                return word
            
            # Check for single symbol difference (same length)
            if len(pattern_parts) == len(vocab_parts):
                differences = sum(1 for p, v in zip(pattern_parts, vocab_parts) if p != v)
                # Only match if there's exactly one difference AND the patterns are similar
                # (e.g., "S L" vs "S S" but not "S" vs "L")
                if differences == 1 and len(pattern_parts) > 1:
                    logger.debug(f"Single symbol difference: '{pattern}' vs '{vocab_pattern}'")
                    return word
            
            # Check for insertion/deletion (length differs by exactly 1)
            elif abs(len(pattern_parts) - len(vocab_parts)) == 1:
                # Only allow fuzzy matching if the pattern is longer than the vocab pattern
                # This prevents "S" from matching "S S" but allows "S S S" to match "S S"
                if len(pattern_parts) > len(vocab_parts):
                    shorter = vocab_parts
                    longer = pattern_parts
                    
                    # Check if shorter is a subsequence of longer
                    # But only if the extra symbol is at the end (not in the middle)
                    if self._is_subsequence(shorter, longer) and self._is_prefix_match(shorter, longer):
                        logger.debug(f"Insertion match: '{pattern}' vs '{vocab_pattern}'")
                        return word
        
        return None
    
    def _is_subsequence(self, shorter: List[str], longer: List[str]) -> bool:
        """
        Check if shorter list is a subsequence of longer list.
        
        Args:
            shorter: The shorter list
            longer: The longer list
            
        Returns:
            True if shorter is a subsequence of longer
        """
        i = j = 0
        while i < len(shorter) and j < len(longer):
            if shorter[i] == longer[j]:
                i += 1
            j += 1
        return i == len(shorter)
    
    def _is_prefix_match(self, shorter: List[str], longer: List[str]) -> bool:
        """
        Check if longer list starts with shorter list.
        
        This ensures that extra symbols are only at the end, not in the middle.
        
        Args:
            shorter: The shorter list
            longer: The longer list
            
        Returns:
            True if longer starts with shorter
        """
        if len(shorter) >= len(longer):
            return False
        
        # Check if longer starts with shorter
        for i in range(len(shorter)):
            if shorter[i] != longer[i]:
                return False
        
        return True
    
    def clear_sequence(self) -> None:
        """Clear the current sequence and reset state."""
        logger.debug(f"Clearing sequence: {self.current_sequence}")
        print(f"🧹 DEBUG: Clearing sequence: {self.current_sequence}, was complete: {self.sequence_complete}")
        self.current_sequence = []
        self.sequence_complete = False
        print(f"✅ DEBUG: Sequence cleared, ready for new blinks")
    
    def get_current_sequence(self) -> List[str]:
        """Get the current sequence as a list of blink types."""
        return self.current_sequence.copy()
    
    def get_last_word(self) -> str:
        """Get the last successfully matched word."""
        return self.last_word
    
    def is_sequence_complete(self) -> bool:
        """Check if the current sequence has been completed."""
        return self.sequence_complete
    
    def get_vocabulary(self) -> Dict[str, str]:
        """Get current vocabulary mapping."""
        return self.vocab.copy()
    
    def get_meta(self) -> Dict[str, Any]:
        """Get metadata including timing thresholds."""
        import copy
        return copy.deepcopy(self.meta)
