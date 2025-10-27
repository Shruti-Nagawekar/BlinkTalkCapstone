//
//  VocabularyEndpoint.swift
//  Camera_View
//
//  Vocabulary API endpoints
//

import Foundation

class VocabularyEndpoint {
    private let client: APIClient
    
    init(client: APIClient = .shared) {
        self.client = client
    }
    
    // MARK: - Get Vocabulary
    func getVocabulary() async throws -> VocabularyResponse {
        try await client.request(
            endpoint: "/api/vocabulary",
            method: .GET,
            responseType: VocabularyResponse.self
        )
    }
    
    // MARK: - Get Words List
    func getWords() async throws -> VocabularyWordListResponse {
        try await client.request(
            endpoint: "/api/vocabulary/words",
            method: .GET,
            responseType: VocabularyWordListResponse.self
        )
    }
    
    // MARK: - Get Patterns List
    func getPatterns() async throws -> VocabularyPatternListResponse {
        try await client.request(
            endpoint: "/api/vocabulary/patterns",
            method: .GET,
            responseType: VocabularyPatternListResponse.self
        )
    }
    
    // MARK: - Search Word
    func searchWord(_ word: String) async throws -> VocabularySearchResponse {
        try await client.request(
            endpoint: "/api/vocabulary/search/\(word)",
            method: .GET,
            responseType: VocabularySearchResponse.self
        )
    }
    
    // MARK: - Get Word for Pattern
    func getWordForPattern(_ pattern: String) async throws -> String {
        struct PatternResponse: Codable {
            let pattern: String
            let word: String
            let found: Bool
        }
        
        let response = try await client.request(
            endpoint: "/api/vocabulary/pattern/\(pattern)",
            method: .GET,
            responseType: PatternResponse.self
        )
        
        return response.word
    }
    
    // MARK: - Get Vocabulary Count
    func getCount() async throws -> VocabularyCountResponse {
        try await client.request(
            endpoint: "/api/vocabulary/count",
            method: .GET,
            responseType: VocabularyCountResponse.self
        )
    }
    
    // MARK: - Reload Vocabulary
    func reload() async throws -> VocabularyReloadResponse {
        try await client.request(
            endpoint: "/api/vocabulary/reload",
            method: .POST,
            responseType: VocabularyReloadResponse.self
        )
    }
}

