//
//  HealthEndpoint.swift
//  Camera_View
//
//  Health check API endpoint
//

import Foundation

// MARK: - Health Response
struct HealthResponse: Codable {
    let status: String
}

class HealthEndpoint {
    private let client: APIClient
    
    init(client: APIClient = .shared) {
        self.client = client
    }
    
    // MARK: - Health Check
    func checkHealth() async throws -> HealthResponse {
        try await client.request(
            endpoint: "/api/health",
            method: .GET,
            responseType: HealthResponse.self
        )
    }
}

