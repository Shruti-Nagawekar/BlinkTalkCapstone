//
//  TranslationEndpoint.swift
//  Camera_View
//
//  Translation API endpoints
//

import Foundation

class TranslationEndpoint {
    private let client: APIClient
    
    init(client: APIClient = .shared) {
        self.client = client
    }
    
    // MARK: - Get Translation
    func getTranslation() async throws -> TranslationResponse {
        try await client.request(
            endpoint: "/api/translation",
            method: .GET,
            responseType: TranslationResponse.self
        )
    }
    
    // MARK: - Process EAR Sample
    func processEARSample(earValue: Double, timestamp: Double? = nil) async throws -> EARSampleResponse {
        let request = EARSampleRequest(earValue: earValue, timestamp: timestamp)
        return try await client.request(
            endpoint: "/api/translation/process_ear",
            method: .POST,
            body: request,
            responseType: EARSampleResponse.self
        )
    }
    
    // MARK: - Reset Sequence
    func resetSequence() async throws -> SequenceResetResponse {
        try await client.request(
            endpoint: "/api/translation/reset",
            method: .POST,
            responseType: SequenceResetResponse.self
        )
    }
}

