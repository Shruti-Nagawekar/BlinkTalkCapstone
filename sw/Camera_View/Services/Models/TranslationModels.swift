//
//  TranslationModels.swift
//  Camera_View
//
//  Models for translation API endpoints
//

import Foundation

// MARK: - Translation Response
struct TranslationResponse: Codable {
    let output: String
}

// MARK: - EAR Sample Request
struct EARSampleRequest: Codable {
    let earValue: Double
    let timestamp: Double?
    
    enum CodingKeys: String, CodingKey {
        case earValue = "ear_value"
        case timestamp
    }
}

// MARK: - EAR Sample Response
struct EARSampleResponse: Codable {
    let blinkEvents: Int
    let currentSequence: [String]
    let wordGapDetected: Bool
    let sequenceComplete: Bool
    let lastWord: String
    
    enum CodingKeys: String, CodingKey {
        case blinkEvents = "blink_events"
        case currentSequence = "current_sequence"
        case wordGapDetected = "word_gap_detected"
        case sequenceComplete = "sequence_complete"
        case lastWord = "last_word"
    }
}

// MARK: - Sequence Reset Response
struct SequenceResetResponse: Codable {
    let message: String
}

// MARK: - Frame Request
struct FrameRequest: Codable {
    let frameB64: String
    let user: String
    
    enum CodingKeys: String, CodingKey {
        case frameB64 = "frame_b64"
        case user
    }
}

// MARK: - Frame Response
struct FrameResponse: Codable {
    let ok: Bool
    let bytes: Int
    let message: String
}

// MARK: - Latest Frame Response
struct LatestFrameResponse: Codable {
    let frameAvailable: Bool
    let metadata: [String: AnyCodable]?
    let frameSizeBytes: Int?
    let message: String?
    
    enum CodingKeys: String, CodingKey {
        case frameAvailable = "frame_available"
        case metadata
        case frameSizeBytes = "frame_size_bytes"
        case message
    }
}

// MARK: - Any Codable (for dynamic metadata)
struct AnyCodable: Codable {
    let value: Any
    
    init(_ value: Any) {
        self.value = value
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let bool = try? container.decode(Bool.self) {
            value = bool
        } else if let int = try? container.decode(Int.self) {
            value = int
        } else if let double = try? container.decode(Double.self) {
            value = double
        } else if let string = try? container.decode(String.self) {
            value = string
        } else if let array = try? container.decode([AnyCodable].self) {
            value = array.map { $0.value }
        } else if let dictionary = try? container.decode([String: AnyCodable].self) {
            value = dictionary.mapValues { $0.value }
        } else {
            throw DecodingError.dataCorruptedError(in: container, debugDescription: "Unsupported type")
        }
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch value {
        case let bool as Bool:
            try container.encode(bool)
        case let int as Int:
            try container.encode(int)
        case let double as Double:
            try container.encode(double)
        case let string as String:
            try container.encode(string)
        default:
            throw EncodingError.invalidValue(value, EncodingError.Context(codingPath: encoder.codingPath, debugDescription: "Unsupported type"))
        }
    }
}

// MARK: - Frame Process Response
struct FrameProcessResponse: Codable {
    let success: Bool
    let earValue: Double?
    let blinkEvents: Int
    let currentSequence: [String]
    let wordGapDetected: Bool
    let sequenceComplete: Bool
    let completedWord: String?
    let lastWord: String?
    let message: String?
    
    enum CodingKeys: String, CodingKey {
        case success
        case earValue = "ear_value"
        case blinkEvents = "blink_events"
        case currentSequence = "current_sequence"
        case wordGapDetected = "word_gap_detected"
        case sequenceComplete = "sequence_complete"
        case completedWord = "completed_word"
        case lastWord = "last_word"
        case message
    }
}

