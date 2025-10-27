//
//  FrameEndpoint.swift
//  Camera_View
//
//  Frame API endpoints
//

import Foundation

class FrameEndpoint {
    private let client: APIClient
    
    init(client: APIClient = .shared) {
        self.client = client
    }
    
    // MARK: - Ingest Frame
    func ingestFrame(frameB64: String, user: String) async throws -> FrameResponse {
        let request = FrameRequest(frameB64: frameB64, user: user)
        return try await client.request(
            endpoint: "/api/frame",
            method: .POST,
            body: request,
            responseType: FrameResponse.self
        )
    }
    
    // MARK: - Get Latest Frame
    func getLatestFrame() async throws -> LatestFrameResponse {
        try await client.request(
            endpoint: "/api/frame/latest",
            method: .GET,
            responseType: LatestFrameResponse.self
        )
    }
    
    // MARK: - Process Frame for Blinks
    func processFrame(frameB64: String, user: String) async throws -> FrameProcessResponse {
        let request = FrameRequest(frameB64: frameB64, user: user)
        return try await client.request(
            endpoint: "/api/frame/process",
            method: .POST,
            body: request,
            responseType: FrameProcessResponse.self
        )
    }
}

