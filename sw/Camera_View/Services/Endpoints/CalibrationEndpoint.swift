//
//  CalibrationEndpoint.swift
//  Camera_View
//
//  Calibration API endpoints
//

import Foundation

class CalibrationEndpoint {
    private let client: APIClient
    
    init(client: APIClient = .shared) {
        self.client = client
    }
    
    // MARK: - Set Calibration Profile
    func setProfile(_ profile: String) async throws -> CalibrationProfileResponse {
        try await client.request(
            endpoint: "/api/calibration/set",
            method: .POST,
            body: CalibrationProfileRequest(profile: profile),
            responseType: CalibrationProfileResponse.self
        )
    }
    
    // MARK: - Get Active Profile
    func getActiveProfile() async throws -> CalibrationProfileResponse {
        try await client.request(
            endpoint: "/api/calibration/active",
            method: .GET,
            responseType: CalibrationProfileResponse.self
        )
    }
    
    // MARK: - Get Current Thresholds
    func getThresholds() async throws -> CalibrationThresholdsResponse {
        try await client.request(
            endpoint: "/api/calibration/thresholds",
            method: .GET,
            responseType: CalibrationThresholdsResponse.self
        )
    }
    
    // MARK: - Get Calibration Info
    func getInfo() async throws -> CalibrationInfoResponse {
        try await client.request(
            endpoint: "/api/calibration/info",
            method: .GET,
            responseType: CalibrationInfoResponse.self
        )
    }
    
    // MARK: - Reset Calibration
    func reset() async throws -> CalibrationProfileResponse {
        try await client.request(
            endpoint: "/api/calibration/reset",
            method: .POST,
            responseType: CalibrationProfileResponse.self
        )
    }
    
    // MARK: - Set Custom Calibration
    func setCustomCalibration(_ request: CustomCalibrationRequest) async throws -> CustomCalibrationResponse {
        try await client.request(
            endpoint: "/api/calibration/custom",
            method: .POST,
            body: request,
            responseType: CustomCalibrationResponse.self
        )
    }
    
    // MARK: - Get Custom Calibration
    func getCustomCalibration() async throws -> CustomCalibrationResponse {
        try await client.request(
            endpoint: "/api/calibration/custom",
            method: .GET,
            responseType: CustomCalibrationResponse.self
        )
    }
    
    // MARK: - Clear Custom Calibration
    func clearCustomCalibration() async throws -> CalibrationProfileResponse {
        try await client.request(
            endpoint: "/api/calibration/custom",
            method: .DELETE,
            responseType: CalibrationProfileResponse.self
        )
    }
}

