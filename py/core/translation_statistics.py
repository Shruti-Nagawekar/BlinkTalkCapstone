"""
Translation statistics tracking for BlinkTalk system.
"""
import time
import logging
from typing import Dict, Any, List
from collections import Counter
from datetime import datetime
import threading

logger = logging.getLogger(__name__)


class TranslationStatistics:
    """
    Tracks translation statistics including success rates,
    timing, word frequency, and error tracking.
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self.reset()
    
    def reset(self) -> None:
        """Reset all statistics."""
        with self._lock:
            self.total_translations = 0
            self.successful_translations = 0
            self.failed_translations = 0
            self.word_frequency = Counter()
            self.translation_times = []
            self.errors = []
            self.last_translation_time = None
            self.last_translated_word = None
            
            logger.info("Translation statistics reset")
    
    def record_translation(self, word: str, processing_time: float = None) -> None:
        """
        Record a successful translation.
        
        Args:
            word: The translated word
            processing_time: Time taken to process (seconds)
        """
        with self._lock:
            self.total_translations += 1
            self.successful_translations += 1
            self.word_frequency[word] += 1
            self.last_translation_time = datetime.now()
            self.last_translated_word = word
            
            if processing_time is not None:
                self.translation_times.append(processing_time)
            
            logger.debug(f"Recorded translation: '{word}' (total: {self.total_translations})")
    
    def record_failure(self, error_message: str) -> None:
        """
        Record a failed translation.
        
        Args:
            error_message: Description of the failure
        """
        with self._lock:
            self.total_translations += 1
            self.failed_translations += 1
            self.errors.append({
                "message": error_message,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.warning(f"Recorded translation failure: {error_message}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive translation statistics.
        
        Returns:
            Dictionary containing all statistics
        """
        with self._lock:
            avg_time = (
                sum(self.translation_times) / len(self.translation_times)
                if self.translation_times else 0
            )
            
            success_rate = (
                (self.successful_translations / self.total_translations * 100)
                if self.total_translations > 0 else 0
            )
            
            return {
                "total_translations": self.total_translations,
                "successful_translations": self.successful_translations,
                "failed_translations": self.failed_translations,
                "success_rate": round(success_rate, 2),
                "average_processing_time_ms": round(avg_time * 1000, 2),
                "word_frequency": dict(self.word_frequency.most_common(10)),
                "total_unique_words": len(self.word_frequency),
                "last_translation_time": (
                    self.last_translation_time.isoformat()
                    if self.last_translation_time else None
                ),
                "last_translated_word": self.last_translated_word,
                "recent_errors": self.errors[-5:] if self.errors else []
            }
    
    def get_summary(self) -> str:
        """
        Get a human-readable summary of statistics.
        
        Returns:
            Formatted summary string
        """
        stats = self.get_stats()
        return (
            f"Translations: {stats['total_translations']} | "
            f"Success: {stats['successful_translations']} ({stats['success_rate']}%) | "
            f"Avg Time: {stats['average_processing_time_ms']}ms"
        )


# Global statistics instance
_translation_stats = TranslationStatistics()


def get_translation_statistics() -> TranslationStatistics:
    """Get the global translation statistics instance."""
    return _translation_stats


def reset_translation_statistics() -> None:
    """Reset translation statistics (for testing)."""
    _translation_stats.reset()


