//
//  BlinkDetectionView.swift
//  Camera_View
//
//  Black screen interface for blink detection with background frame streaming
//

import SwiftUI
import AVFoundation
import Combine

struct BlinkDetectionView: View {
    @Environment(\.dismiss) private var dismiss
    
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
    @State private var lastFrameSentTime: Date = Date.distantPast
    @State private var isBackendReset: Bool = false  // Track if backend is reset but UI persists
    @State private var isResetComplete: Bool = false  // Track if backend reset has completed
    @State private var firstFrameAfterReset: Bool = true  // Track if this is the first frame after reset
    
    @StateObject private var cameraManager = BackgroundCameraManager()
    @StateObject private var frameProcessor = FrameProcessor()
    
    private let translationEndpoint = TranslationEndpoint()
    private let pollingTimeout: Int = 10  // 10 seconds
    private let pollingInterval: Double = 2.0  // 2 seconds
    private let frameSendInterval: TimeInterval = 0.2  // Send frame every 200ms (5 FPS)
    
    var body: some View {
        ZStack {
            // Black screen background
            Color.black
                .ignoresSafeArea()
            
            VStack {
                // Top bar with back button
                HStack {
                    Button(action: {
                        dismiss()
                    }) {
                        HStack {
                            Image(systemName: "chevron.left")
                            Text("Back")
                        }
                        .font(.headline)
                        .foregroundColor(.white)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 8)
                        .background(Color.white.opacity(0.1))
                        .cornerRadius(10)
                    }
                    Spacer()
                }
                .padding()
                
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
                
                // Sequence and Word Display - fixed container to prevent layout shifts
                VStack(spacing: 20) {
                    // Current Sequence Display - always present to maintain layout
                    ZStack {
                        // Background always visible
                        RoundedRectangle(cornerRadius: 10)
                            .fill(Color.white.opacity(0.1))
                            .frame(height: 100)
                        
                        // Text content - use fixed frame to prevent layout shifts
                        Text(currentSequence.isEmpty ? "" : currentSequence.joined(separator: " "))
                            .font(.system(size: 48, weight: .bold))
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity, maxHeight: .infinity)
                            .opacity(currentSequence.isEmpty ? 0 : 1)
                    }
                    .frame(height: 100)
                    .frame(maxWidth: .infinity)
                    .padding(.horizontal)
                    
                    // Last Word Display - always present to maintain layout
                    ZStack {
                        // Background always visible
                        RoundedRectangle(cornerRadius: 10)
                            .fill(Color.white.opacity(0.1))
                            .frame(height: 100)
                        
                        // Text content - use fixed frame to prevent layout shifts
                        Text(lastWord.isEmpty ? "" : lastWord)
                            .font(.system(size: 56, weight: .bold))
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity, maxHeight: .infinity)
                            .opacity(lastWord.isEmpty ? 0 : 1)
                    }
                    .frame(height: 100)
                    .frame(maxWidth: .infinity)
                    .padding(.horizontal)
                }
                .frame(height: 240) // Fixed height container - never changes
                .fixedSize(horizontal: false, vertical: true) // Prevent size changes
                
                Spacer()
                
                // Reset Button - appears when there's content and backend isn't reset yet
                if (!currentSequence.isEmpty || !lastWord.isEmpty) && !isBackendReset {
                    Button(action: {
                        resetSequence()
                    }) {
                        HStack {
                            Image(systemName: "arrow.counterclockwise")
                            Text("Reset Sequence")
                        }
                        .font(.headline)
                        .foregroundColor(.black)
                        .padding()
                        .background(Color.white)
                        .cornerRadius(12)
                    }
                    .padding(.horizontal)
                    .padding(.bottom, 10)
                }
                
                // Ready for Next Sequence Button - appears after reset
                if isBackendReset {
                    Button(action: {
                        readyForNextSequence()
                    }) {
                        HStack {
                            Image(systemName: "checkmark.circle.fill")
                            Text("Ready for Next Sequence")
                        }
                        .font(.headline)
                        .foregroundColor(.black)
                        .padding()
                        .background(Color.white)
                        .cornerRadius(12)
                    }
                    .padding(.horizontal)
                    .padding(.bottom, 10)
                }
                
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
                            .foregroundColor(.white.opacity(0.8))
                    }
                    
                    if earValue > 0 {
                        Text("EAR: \(String(format: "%.3f", earValue))")
                            .font(.caption)
                            .foregroundColor(.white.opacity(0.6))
                    }
                    
                    Text("Sequence: \(currentSequence.count) symbols")
                        .font(.caption)
                        .foregroundColor(.white.opacity(0.6))
                }
                .padding(.bottom, 40)
                }
            }
        }
        .onAppear {
            // Clear ALL UI state immediately to prevent showing old persisted sequence
            currentSequence = []
            lastWord = ""
            resultWord = ""
            isBackendReset = false
            isResetComplete = false  // Block frame processing until reset is done
            firstFrameAfterReset = true  // Mark that we're waiting for first frame after reset
            isPolling = false
            pollCount = 0
            errorMessage = nil
            
            // Reset backend sequence when view appears to start fresh
            Task {
                do {
                    _ = try await translationEndpoint.resetSequence()
                    print("✅ Backend sequence reset on view appear")
                    // Ensure UI is completely cleared and allow frame processing after backend reset
                    await MainActor.run {
                        // Force clear everything again after reset
                        currentSequence = []
                        lastWord = ""
                        resultWord = ""
                        isPolling = false
                        pollCount = 0
                        isResetComplete = true  // Now allow frame processing
                    }
                } catch {
                    print("⚠️ Failed to reset sequence on appear: \(error.localizedDescription)")
                    // Even if reset fails, allow processing (backend might be clean)
                    await MainActor.run {
                        // Still clear UI state
                        currentSequence = []
                        lastWord = ""
                        isResetComplete = true
                    }
                }
            }
            
            checkCameraPermission()
            cameraManager.onFrameCaptured = { frame in
                Task {
                    await processFrame(frame)
                }
            }
        }
        .onDisappear {
            // Stop camera when view disappears to prevent multiple input errors
            cameraManager.stopCapture()
        }
        .onChange(of: cameraManager.frameStatus) { oldValue, newValue in
            handleFrameStatus(newValue)
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
            // Start camera on background thread
            DispatchQueue.global(qos: .userInitiated).async {
                self.cameraManager.startCapture()
            }
        } else if cameraPermissionStatus == .notDetermined {
            AVCaptureDevice.requestAccess(for: .video) { granted in
                DispatchQueue.main.async {
                    if granted {
                        self.cameraPermissionStatus = .authorized
                        // Start camera on background thread
                        DispatchQueue.global(qos: .userInitiated).async {
                            self.cameraManager.startCapture()
                        }
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
        case .processing:
            // Frame processing will be handled by the camera delegate
            break
        case .error(let errorString):
            DispatchQueue.main.async {
                errorMessage = errorString
                isProcessing = false
            }
        case .ready:
            isProcessing = false
        }
    }
    
    private func processFrame(_ frame: CMSampleBuffer) async {
        // Don't process frames until backend reset is complete
        guard isResetComplete else {
            return // Skip processing until reset is complete
        }
        
        // Don't process frames if backend is reset (waiting for user to be ready)
        guard !isBackendReset else {
            return // Skip processing until user is ready for next sequence
        }
        
        // Throttle frame sending - only send every 200ms (5 FPS)
        let now = Date()
        let timeSinceLastFrame = now.timeIntervalSince(lastFrameSentTime)
        guard timeSinceLastFrame >= frameSendInterval else {
            return // Skip this frame
        }
        
        lastFrameSentTime = now
        
        guard !isProcessing else { return } // Don't process if already processing
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
                // On first frame after reset, ignore any non-empty sequence (it's old persisted data)
                if firstFrameAfterReset {
                    if !response.currentSequence.isEmpty {
                        let sequenceString = response.currentSequence.joined(separator: " ")
                        print("⚠️ Ignoring old persisted sequence on first frame: [\(sequenceString)] (length: \(response.currentSequence.count))")
                        // Force clear UI immediately
                        currentSequence = []
                        lastWord = ""
                        // Stop any ongoing polling from old persisted sequences
                        isPolling = false
                        pollCount = 0
                        // Ensure we don't show any old data
                        resultWord = ""
                    } else {
                        currentSequence = []
                        lastWord = ""
                    }
                    firstFrameAfterReset = false  // Only check first frame
                } else {
                    // After first frame, process normally
                    // Ignore sequences that are longer than max length (4) - these are old persisted data
                    if response.currentSequence.count > 4 {
                        let sequenceString = response.currentSequence.joined(separator: " ")
                        print("⚠️ Ignoring old persisted sequence (too long): [\(sequenceString)] (length: \(response.currentSequence.count))")
                        currentSequence = []
                        lastWord = ""
                    } else if !response.currentSequence.isEmpty {
                        // Valid new sequence
                        currentSequence = response.currentSequence
                        // Only set lastWord if we have a valid new sequence
                        if let word = response.completedWord {
                            lastWord = word
                            // Start polling for translation when word is completed
                            startTranslationPolling()
                        } else {
                            lastWord = response.lastWord ?? ""
                        }
                    } else {
                        // Backend returned empty sequence, ensure UI is also empty
                        currentSequence = []
                        lastWord = ""
                    }
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
    
    private func resetSequence() {
        Task {
            do {
                _ = try await translationEndpoint.resetSequence()
                await MainActor.run {
                    // Reset backend but keep UI visible
                    isBackendReset = true
                    print("✅ Backend sequence reset, UI persists")
                }
            } catch {
                await MainActor.run {
                    print("⚠️ Failed to reset sequence: \(error.localizedDescription)")
                    // Still mark as reset even if backend fails
                    isBackendReset = true
                }
            }
        }
    }
    
    private func readyForNextSequence() {
        // Clear UI and allow new sequence
        currentSequence = []
        lastWord = ""
        isBackendReset = false
        isResetComplete = true  // Ensure processing is enabled
        print("✅ Ready for next sequence")
    }
}

// MARK: - Camera Frame Status
enum CameraFrameStatus: Equatable {
    case ready
    case processing
    case error(String)
    
    static func == (lhs: CameraFrameStatus, rhs: CameraFrameStatus) -> Bool {
        switch (lhs, rhs) {
        case (.ready, .ready), (.processing, .processing):
            return true
        case (.error(let lhsError), .error(let rhsError)):
            return lhsError == rhsError
        default:
            return false
        }
    }
}

// MARK: - Background Camera Manager
class BackgroundCameraManager: NSObject, ObservableObject {
    @Published var frameStatus: CameraFrameStatus = .ready
    
    var onFrameCaptured: ((CMSampleBuffer) -> Void)?
    
    private let session = AVCaptureSession()
    private let output = AVCaptureVideoDataOutput()
    private var isRunning = false
    private let sessionQueue = DispatchQueue(label: "CameraSessionQueue")
    
    func startCapture() {
        sessionQueue.async {
            // Always stop and clean up first to prevent multiple inputs
            if self.session.isRunning {
                self.session.stopRunning()
                // Wait a moment for session to fully stop
                Thread.sleep(forTimeInterval: 0.1)
            }
            
            self.session.beginConfiguration()
            self.session.sessionPreset = .high
            
            // Remove existing inputs first (critical to prevent multiple input error)
            let existingInputs = self.session.inputs
            for input in existingInputs {
                self.session.removeInput(input)
            }
            
            // Remove existing outputs first
            let existingOutputs = self.session.outputs
            for output in existingOutputs {
                self.session.removeOutput(output)
            }
            
            // Setup camera
            guard let camera = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .front),
                  let input = try? AVCaptureDeviceInput(device: camera) else {
                self.session.commitConfiguration()
                DispatchQueue.main.async {
                    self.frameStatus = .error("Unable to access camera")
                }
                self.isRunning = false
                return
            }
            
            // Only add input if session can accept it
            guard self.session.canAddInput(input) else {
                self.session.commitConfiguration()
                DispatchQueue.main.async {
                    self.frameStatus = .error("Cannot add camera input")
                }
                self.isRunning = false
                return
            }
            
            self.session.addInput(input)
            
            // Setup output
            self.output.videoSettings = [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA]
            self.output.setSampleBufferDelegate(self, queue: DispatchQueue(label: "CameraQueue"))
            
            guard self.session.canAddOutput(self.output) else {
                self.session.removeInput(input) // Clean up input if output fails
                self.session.commitConfiguration()
                DispatchQueue.main.async {
                    self.frameStatus = .error("Cannot add camera output")
                }
                self.isRunning = false
                return
            }
            
            self.session.addOutput(self.output)
            self.session.commitConfiguration()
            
            // Start running after configuration is committed
            self.session.startRunning()
            self.isRunning = true
            
            DispatchQueue.main.async {
                print("✅ Background camera started")
            }
        }
    }
    
    func stopCapture() {
        sessionQueue.async {
            guard self.isRunning else { return }
            
            self.session.beginConfiguration()
            
            // Remove all inputs
            for input in self.session.inputs {
                self.session.removeInput(input)
            }
            
            // Remove all outputs
            for output in self.session.outputs {
                self.session.removeOutput(output)
            }
            
            self.session.commitConfiguration()
            self.session.stopRunning()
            self.isRunning = false
            
            DispatchQueue.main.async {
                print("✅ Background camera stopped")
            }
        }
    }
    
    deinit {
        stopCapture()
    }
}

extension BackgroundCameraManager: AVCaptureVideoDataOutputSampleBufferDelegate {
    func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        DispatchQueue.main.async {
            self.frameStatus = .processing
        }
        onFrameCaptured?(sampleBuffer)
    }
    
    func captureOutput(_ output: AVCaptureOutput, didDrop sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        // Handle dropped frames silently
    }
}

// MARK: - Frame Processor
class FrameProcessor: ObservableObject {
    @Published var isProcessing = false
}

