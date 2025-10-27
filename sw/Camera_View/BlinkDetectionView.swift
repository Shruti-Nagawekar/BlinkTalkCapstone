//
//  BlinkDetectionView.swift
//  Camera_View
//
//  Black screen interface for blink detection with background frame streaming
//

import SwiftUI
import AVFoundation

struct BlinkDetectionView: View {
    @State private var currentSequence: [String] = []
    @State private var lastWord: String = ""
    @State private var isProcessing: Bool = false
    @State private var errorMessage: String? = nil
    @State private var blinkClass: String = ""
    @State private var earValue: Double = 0.0
    @State private var cameraPermissionStatus: AVAuthorizationStatus = .notDetermined
    @State private var showResultView: Bool = false
    @State private var resultWord: String = ""
    @State private var pollCount: Int = 0
    @State private var isPolling: Bool = false
    
    @StateObject private var cameraManager = BackgroundCameraManager()
    @StateObject private var frameProcessor = FrameProcessor()
    
    private let translationEndpoint = TranslationEndpoint()
    private let pollingTimeout: Int = 10  // 10 seconds
    private let pollingInterval: Double = 2.0  // 2 seconds
    
    var body: some View {
        ZStack {
            // Black screen background
            Color.black
                .ignoresSafeArea()
            
            VStack {
                // Permission denied view
                if cameraPermissionStatus == .denied {
                    VStack(spacing: 20) {
                        Image(systemName: "camera.fill")
                            .font(.system(size: 60))
                            .foregroundColor(.red)
                        
                        Text("Camera Permission Required")
                            .font(.title2)
                            .fontWeight(.bold)
                            .foregroundColor(.white)
                        
                        Text("Please enable camera access in Settings to use blink detection.")
                            .font(.body)
                            .multilineTextAlignment(.center)
                            .foregroundColor(.gray)
                            .padding(.horizontal)
                        
                        Button(action: {
                            if let url = URL(string: UIApplication.openSettingsURLString) {
                                UIApplication.shared.open(url)
                            }
                        }) {
                            Text("Open Settings")
                                .font(.headline)
                                .foregroundColor(.white)
                                .padding()
                                .background(Color.blue)
                                .cornerRadius(10)
                        }
                        .padding(.top, 20)
                    }
                    .padding()
                } else {
                Spacer()
                
                // Current Sequence Display
                if !currentSequence.isEmpty {
                    Text(currentSequence.joined(separator: " "))
                        .font(.system(size: 48, weight: .bold))
                        .foregroundColor(.green)
                        .padding()
                        .background(Color.green.opacity(0.1))
                        .cornerRadius(10)
                        .padding()
                }
                
                // Last Word Display
                if !lastWord.isEmpty {
                    Text(lastWord)
                        .font(.system(size: 56, weight: .bold))
                        .foregroundColor(.yellow)
                        .padding()
                        .background(Color.yellow.opacity(0.1))
                        .cornerRadius(10)
                        .padding()
                }
                
                Spacer()
                
                // Status Information
                VStack(spacing: 8) {
                    if isProcessing {
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: .white))
                            .padding()
                    }
                    
                    if let error = errorMessage {
                        Text("Error: \(error)")
                            .font(.caption)
                            .foregroundColor(.red)
                            .padding(.horizontal)
                    }
                    
                    if !blinkClass.isEmpty {
                        Text("Blink: \(blinkClass)")
                            .font(.caption)
                            .foregroundColor(.green)
                    }
                    
                    if earValue > 0 {
                        Text("EAR: \(String(format: "%.3f", earValue))")
                            .font(.caption)
                            .foregroundColor(.cyan)
                    }
                    
                    Text("Sequence: \(currentSequence.count) symbols")
                        .font(.caption)
                        .foregroundColor(.gray)
                }
                .padding(.bottom, 40)
                }
            }
        }
        .onAppear {
            checkCameraPermission()
        }
        .onChange(of: cameraManager.frameStatus) { status in
            handleFrameStatus(status)
        }
        .fullScreenCover(isPresented: $showResultView) {
            ResultView(translatedWord: resultWord) {
                // Reset for next detection
                resultWord = ""
                lastWord = ""
                currentSequence = []
            }
        }
    }
    
    private func checkCameraPermission() {
        cameraPermissionStatus = AVCaptureDevice.authorizationStatus(for: .video)
        
        if cameraPermissionStatus == .authorized {
            cameraManager.startCapture()
        } else if cameraPermissionStatus == .notDetermined {
            AVCaptureDevice.requestAccess(for: .video) { granted in
                DispatchQueue.main.async {
                    if granted {
                        self.cameraPermissionStatus = .authorized
                        self.cameraManager.startCapture()
                    } else {
                        self.cameraPermissionStatus = .denied
                        self.errorMessage = "Camera permission denied"
                    }
                }
            }
        } else {
            errorMessage = "Camera permission required. Please enable in Settings."
        }
    }
    
    private func handleFrameStatus(_ status: CameraFrameStatus) {
        switch status {
        case .processing(let frame):
            Task {
                await processFrame(frame)
            }
        case .error(let error):
            DispatchQueue.main.async {
                errorMessage = error.localizedDescription
                isProcessing = false
            }
        case .ready:
            isProcessing = false
        }
    }
    
    private func processFrame(_ frame: CMSampleBuffer) async {
        isProcessing = true
        
        do {
            // Convert frame to image
            guard let image = imageFromSampleBuffer(frame) else {
                DispatchQueue.main.async {
                    isProcessing = false
                }
                return
            }
            
            // Convert image to base64
            guard let imageData = image.jpegData(compressionQuality: 0.5) else {
                DispatchQueue.main.async {
                    isProcessing = false
                }
                return
            }
            
            let base64String = imageData.base64EncodedString()
            
            // Send frame to backend for processing
            let frameEndpoint = FrameEndpoint()
            let response = try await frameEndpoint.processFrame(
                frameB64: base64String,
                user: "user" // TODO: Get from profile
            )
            
            // Update UI with response
            DispatchQueue.main.async {
                currentSequence = response.currentSequence
                if let word = response.completedWord {
                    lastWord = word
                    // Start polling for translation when word is completed
                    startTranslationPolling()
                } else {
                    lastWord = response.lastWord ?? ""
                }
                blinkClass = response.blinkEvents > 0 ? "Detected" : ""
                isProcessing = false
            }
            
        } catch {
            DispatchQueue.main.async {
                errorMessage = error.localizedDescription
                isProcessing = false
            }
        }
    }
    
    private func startTranslationPolling() {
        guard !isPolling else { return }
        isPolling = true
        pollCount = 0
        
        Task {
            while pollCount < pollingTimeout {
                do {
                    let result = try await translationEndpoint.getTranslation()
                    
                    if !result.output.isEmpty {
                        // Found a translation
                        DispatchQueue.main.async {
                            resultWord = result.output
                            showResultView = true
                            isPolling = false
                        }
                        return
                    }
                    
                    // Wait before next poll
                    try await Task.sleep(nanoseconds: UInt64(pollingInterval * 1_000_000_000))
                    pollCount += 1
                    
                    DispatchQueue.main.async {
                        lastWord = "Polling... (\(pollCount * 2)s)"
                    }
                    
                } catch {
                    DispatchQueue.main.async {
                        errorMessage = "Translation polling error: \(error.localizedDescription)"
                        isPolling = false
                    }
                    return
                }
            }
            
            // Timeout reached
            DispatchQueue.main.async {
                errorMessage = "Translation timeout"
                isPolling = false
            }
        }
    }
    
    private func imageFromSampleBuffer(_ sampleBuffer: CMSampleBuffer) -> UIImage? {
        guard let imageBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return nil }
        let ciImage = CIImage(cvPixelBuffer: imageBuffer)
        let context = CIContext()
        guard let cgImage = context.createCGImage(ciImage, from: ciImage.extent) else { return nil }
        return UIImage(cgImage: cgImage)
    }
}

// MARK: - Camera Frame Status
enum CameraFrameStatus: Equatable {
    case ready
    case processing(CMSampleBuffer)
    case error(Error)
}

// MARK: - Background Camera Manager
class BackgroundCameraManager: ObservableObject {
    @Published var frameStatus: CameraFrameStatus = .ready
    
    private let session = AVCaptureSession()
    private let output = AVCaptureVideoDataOutput()
    private var isRunning = false
    
    func startCapture() {
        guard !isRunning else { return }
        
        session.beginConfiguration()
        session.sessionPreset = .high
        
        // Setup camera
        guard let camera = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .front),
              let input = try? AVCaptureDeviceInput(device: camera),
              session.canAddInput(input) else {
            DispatchQueue.main.async {
                self.frameStatus = .error(NSError(domain: "CameraManager", code: -1, userInfo: [NSLocalizedDescriptionKey: "Unable to access camera"]))
            }
            return
        }
        
        session.addInput(input)
        
        // Setup output
        output.videoSettings = [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA]
        output.setSampleBufferDelegate(self, queue: DispatchQueue(label: "CameraQueue"))
        
        guard session.canAddOutput(output) else { return }
        session.addOutput(output)
        
        session.commitConfiguration()
        session.startRunning()
        isRunning = true
        
        print("✅ Background camera started")
    }
    
    func stopCapture() {
        session.stopRunning()
        isRunning = false
    }
    
    deinit {
        stopCapture()
    }
}

extension BackgroundCameraManager: AVCaptureVideoDataOutputSampleBufferDelegate {
    func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        DispatchQueue.main.async {
            self.frameStatus = .processing(sampleBuffer)
        }
    }
    
    func captureOutput(_ output: AVCaptureOutput, didDrop sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        // Handle dropped frames silently
    }
}

// MARK: - Frame Processor
class FrameProcessor: ObservableObject {
    @Published var isProcessing = false
}

