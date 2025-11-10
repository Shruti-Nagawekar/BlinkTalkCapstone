//
//  APIClient.swift
//  Camera_View
//
//  Networking client for BlinkTalk API communication
//

import Foundation

/// Base networking client for API communication
class APIClient {
    
    // MARK: - Singleton
    static let shared = APIClient()
    
    // MARK: - Properties
    private let session: URLSession
    
    var baseURL: String {
        get {
            // Check if old URL is stored and update it
            if let storedURL = UserDefaults.standard.string(forKey: "serverURL"),
               storedURL.contains("192.168.1.10") {
                // Update to new IP
                let newURL = storedURL.replacingOccurrences(of: "192.168.1.10", with: "100.70.127.109")
                UserDefaults.standard.set(newURL, forKey: "serverURL")
                return newURL
            }
            return UserDefaults.standard.string(forKey: "serverURL") ?? "http://100.70.127.109:5000"
        }
    }
    
    // Initialize with default session that has timeout configuration
    init(session: URLSession? = nil) {
        if let session = session {
            self.session = session
        } else {
            // Create session with timeout configuration
            let configuration = URLSessionConfiguration.default
            configuration.timeoutIntervalForRequest = 10.0 // 10 second timeout
            configuration.timeoutIntervalForResource = 30.0 // 30 second total timeout
            self.session = URLSession(configuration: configuration)
        }
    }
    
    // MARK: - Generic Request Method
    func request<T: Decodable>(
        endpoint: String,
        method: HTTPMethod = .GET,
        body: Encodable? = nil,
        responseType: T.Type
    ) async throws -> T {
        // Build URL
        guard let url = URL(string: baseURL + endpoint) else {
            throw APIError.invalidURL
        }
        
        // Create request
        var request = URLRequest(url: url)
        request.httpMethod = method.rawValue
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        // Add request body if needed
        if let body = body {
            do {
                request.httpBody = try JSONEncoder().encode(body)
            } catch {
                throw APIError.encodingError(error)
            }
        }
        
        // Perform request
        do {
            let (data, response) = try await session.data(for: request)
            
            // Check response status
            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.invalidResponse
            }
            
            // Handle status codes
            guard (200...299).contains(httpResponse.statusCode) else {
                throw APIError.httpError(statusCode: httpResponse.statusCode, data: data)
            }
            
            // Decode response
            do {
                let decoder = JSONDecoder()
                return try decoder.decode(T.self, from: data)
            } catch {
                throw APIError.decodingError(error)
            }
            
        } catch let error as APIError {
            throw error
        } catch {
            throw APIError.networkError(error)
        }
    }
    
    // MARK: - Generic Request without response
    func request(
        endpoint: String,
        method: HTTPMethod = .GET,
        body: Encodable? = nil
    ) async throws {
        // Build URL
        guard let url = URL(string: baseURL + endpoint) else {
            throw APIError.invalidURL
        }
        
        // Create request
        var request = URLRequest(url: url)
        request.httpMethod = method.rawValue
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        // Add request body if needed
        if let body = body {
            do {
                request.httpBody = try JSONEncoder().encode(body)
            } catch {
                throw APIError.encodingError(error)
            }
        }
        
        // Perform request
        do {
            let (data, response) = try await session.data(for: request)
            
            // Check response status
            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.invalidResponse
            }
            
            // Handle status codes
            guard (200...299).contains(httpResponse.statusCode) else {
                throw APIError.httpError(statusCode: httpResponse.statusCode, data: data)
            }
            
        } catch let error as APIError {
            throw error
        } catch {
            throw APIError.networkError(error)
        }
    }
}

// MARK: - HTTP Method
enum HTTPMethod: String {
    case GET = "GET"
    case POST = "POST"
    case PUT = "PUT"
    case DELETE = "DELETE"
}

// MARK: - API Error
enum APIError: LocalizedError {
    case invalidURL
    case invalidResponse
    case networkError(Error)
    case encodingError(Error)
    case decodingError(Error)
    case httpError(statusCode: Int, data: Data?)
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .invalidResponse:
            return "Invalid response"
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .encodingError(let error):
            return "Encoding error: \(error.localizedDescription)"
        case .decodingError(let error):
            return "Decoding error: \(error.localizedDescription)"
        case .httpError(let statusCode, let data):
            if let data = data, let message = String(data: data, encoding: .utf8) {
                return "HTTP \(statusCode): \(message)"
            }
            return "HTTP error: \(statusCode)"
        }
    }
}

