//
//  CalibrationModels.swift
//  Camera_View
//
//  Models for calibration API endpoints
//

import Foundation

// MARK: - Calibration Profile Request
struct CalibrationProfileRequest: Codable {
    let profile: String
}

// MARK: - Calibration Profile Response
struct CalibrationProfileResponse: Codable {
    let message: String
    let profile: String
    let description: String
    let thresholds: CalibrationThresholds
}

// MARK: - Calibration Thresholds
struct CalibrationThresholds: Codable {
    let shortMaxMs: Int
    let longMinMs: Int
    let longMaxMs: Int
    let symbolGapMaxMs: Int
    let wordGapMinMs: Int
    
    enum CodingKeys: String, CodingKey {
        case shortMaxMs = "short_max_ms"
        case longMinMs = "long_min_ms"
        case longMaxMs = "long_max_ms"
        case symbolGapMaxMs = "symbol_gap_max_ms"
        case wordGapMinMs = "word_gap_min_ms"
    }
}

// MARK: - Calibration Thresholds Response
struct CalibrationThresholdsResponse: Codable {
    let profile: String
    let thresholds: CalibrationThresholds
}

// MARK: - Calibration Info Response
struct CalibrationInfoResponse: Codable {
    let activeProfile: String
    let availableProfiles: [String: String]
    let currentThresholds: CalibrationThresholds
    
    enum CodingKeys: String, CodingKey {
        case activeProfile = "active_profile"
        case availableProfiles = "available_profiles"
        case currentThresholds = "current_thresholds"
    }
}

// MARK: - Custom Calibration Request
struct CustomCalibrationRequest: Codable {
    let shortMaxMs: Int
    let longMinMs: Int
    let longMaxMs: Int
    let symbolGapMaxMs: Int
    let wordGapMinMs: Int
    
    enum CodingKeys: String, CodingKey {
        case shortMaxMs = "short_max_ms"
        case longMinMs = "long_min_ms"
        case longMaxMs = "long_max_ms"
        case symbolGapMaxMs = "symbol_gap_max_ms"
        case wordGapMinMs = "word_gap_min_ms"
    }
}

// MARK: - Custom Calibration Response
struct CustomCalibrationResponse: Codable {
    let message: String
    let profile: String
    let description: String
    let thresholds: CalibrationThresholds
    let isCustom: Bool
    
    enum CodingKeys: String, CodingKey {
        case message
        case profile
        case description
        case thresholds
        case isCustom = "is_custom"
    }
}

// MARK: - Calibration Profile Type
enum CalibrationProfileType: String, Codable, CaseIterable {
    case slow = "slow"
    case medium = "medium"
    case custom = "custom"
    
    var displayName: String {
        switch self {
        case .slow:
            return "Slow"
        case .medium:
            return "Medium"
        case .custom:
            return "Custom"
        }
    }
    
    var description: String {
        switch self {
        case .slow:
            return "For users with slower blink patterns"
        case .medium:
            return "Standard timing for typical users"
        case .custom:
            return "Custom calibration profile"
        }
    }
}

