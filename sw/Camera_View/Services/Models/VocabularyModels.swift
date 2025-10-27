//
//  VocabularyModels.swift
//  Camera_View
//
//  Models for vocabulary API endpoints
//

import Foundation

// MARK: - Vocabulary Response
struct VocabularyResponse: Codable {
    let items: [VocabularyItem]
    let count: Int
}

// MARK: - Vocabulary Item
struct VocabularyItem: Codable {
    let word: String
    let pattern: String
}

// MARK: - Vocabulary Word List Response
struct VocabularyWordListResponse: Codable {
    let words: [String]
}

// MARK: - Vocabulary Pattern List Response
struct VocabularyPatternListResponse: Codable {
    let patterns: [String]
}

// MARK: - Vocabulary Search Response
struct VocabularySearchResponse: Codable {
    let found: Bool
    let word: String?
    let pattern: String?
}

// MARK: - Vocabulary Count Response
struct VocabularyCountResponse: Codable {
    let totalWords: Int
    let totalPatterns: Int
    
    enum CodingKeys: String, CodingKey {
        case totalWords = "total_words"
        case totalPatterns = "total_patterns"
    }
}

// MARK: - Vocabulary Reload Response
struct VocabularyReloadResponse: Codable {
    let message: String
    let count: Int
}

