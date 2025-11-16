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
    @State private var framesAfterReset: Int = 0  // Count frames after reset to ignore first few
    @State private var resetTime: Date = Date.distantPast  // Track when reset happened
    
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
                    if let error = errorMessage {
                        Text("Error: \(error)")
                            .font(.caption)
                            .foregroundColor(.red)
                            .padding(.horizontal)
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
            // Clear UI state
            currentSequence = []
            lastWord = ""
            resultWord = ""
            isBackendReset = false
            isResetComplete = false  // Block frame processing until reset is done
            firstFrameAfterReset = true  // Mark that we're waiting for first frame after reset
            framesAfterReset = 0  // Reset frame counter
            resetTime = Date()  // Record reset time
            isPolling = false
            pollCount = 0
            errorMessage = nil
            
            // Reset backend sequence when view appears to start fresh
            Task {
                do {
                    print("🔄 Calling backend reset...")
                    let resetResponse = try await translationEndpoint.resetSequence()
                    print("✅ Backend sequence reset on view appear: \(resetResponse.message ?? "success")")
                    
                    // Verify reset worked by checking sequence state
                    // Add a delay to ensure reset is fully processed
                    try await Task.sleep(nanoseconds: 200_000_000) // 0.2 second - longer delay
                    
                    // Allow frame processing after backend reset
                    await MainActor.run {
                        isResetComplete = true
                        resetTime = Date()  // Update reset time when reset completes
                        framesAfterReset = 0  // Reset frame counter
                        print("✅ Frame processing enabled after reset (resetTime: \(resetTime))")
                    }
                } catch {
                    print("⚠️ Failed to reset sequence on appear: \(error.localizedDescription)")
                    // Even if reset fails, allow processing (backend might be clean)
                    await MainActor.run {
                        isResetComplete = true
                        resetTime = Date()
                        framesAfterReset = 0
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
        print("📷 Camera permission status: \(cameraPermissionStatus.rawValue) (0=notDetermined, 1=restricted, 2=denied, 3=authorized)")
        
        if cameraPermissionStatus == .authorized {
            print("✅ Camera permission granted, starting camera")
            // Start camera on background thread with a small delay to ensure view is stable
            DispatchQueue.global(qos: .userInitiated).asyncAfter(deadline: .now() + 0.1) {
                self.cameraManager.startCapture()
            }
        } else if cameraPermissionStatus == .notDetermined {
            print("❓ Camera permission not determined, requesting...")
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
            print("⏸️ Frame skipped: waiting for backend reset to complete")
            return // Skip processing until reset is complete
        }
        
        // Don't process frames if backend is reset (waiting for user to be ready)
        guard !isBackendReset else {
            print("⏸️ Frame skipped: backend reset, waiting for user to be ready")
            return // Skip processing until user is ready for next sequence
        }
        
        // Ignore first 3 frames after reset to ensure backend is clean
        // Also ignore frames within 0.5 seconds of reset
        let timeSinceReset = Date().timeIntervalSince(resetTime)
        if framesAfterReset < 3 || timeSinceReset < 0.5 {
            framesAfterReset += 1
            print("⏸️ Frame #\(framesAfterReset) skipped: too soon after reset (time: \(String(format: "%.2f", timeSinceReset))s)")
            return
        }
        
        // Throttle frame sending - only send every 200ms (5 FPS)
        let now = Date()
        let timeSinceLastFrame = now.timeIntervalSince(lastFrameSentTime)
        guard timeSinceLastFrame >= frameSendInterval else {
            // Log throttled frames occasionally (every 10th frame or so)
            if Int.random(in: 0..<10) == 0 {
                print("⏸️ Frame throttled (last sent \(String(format: "%.2f", timeSinceLastFrame))s ago)")
            }
            return // Skip this frame
        }
        
        lastFrameSentTime = now
        
        guard !isProcessing else {
            print("⏸️ Frame skipped: already processing a frame")
            return // Don't process if already processing
        }
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
            
            // Log frame sending
            print("📤 Sending frame to backend (size: \(imageData.count) bytes, base64: \(base64String.count) chars)")
            
            // Send frame to backend for processing
            let frameEndpoint = FrameEndpoint()
            let response = try await frameEndpoint.processFrame(
                frameB64: base64String,
                user: "user" // TODO: Get from profile
            )
            
            // Log response
            print("📥 Received response: EAR=\(response.earValue ?? -1), blinks=\(response.blinkEvents), sequence=\(response.currentSequence)")
            
            // Update UI with response
            DispatchQueue.main.async {
                // On first frame after reset, ALWAYS ignore any sequence (it's old persisted data)
                if firstFrameAfterReset {
                    // Force clear everything - don't trust the backend response on first frame
                    if !response.currentSequence.isEmpty || !(response.lastWord ?? "").isEmpty {
                        let sequenceString = response.currentSequence.joined(separator: " ")
                        print("⚠️ FORCING CLEAR: First frame after reset has data - sequence: [\(sequenceString)], lastWord: '\(response.lastWord ?? "")' - IGNORING")
                    }
                    // Force clear UI immediately regardless of response
                    currentSequence = []
                    lastWord = ""
                    // Stop any ongoing polling from old persisted sequences
                    isPolling = false
                    pollCount = 0
                    // Ensure we don't show any old data
                    resultWord = ""
                    firstFrameAfterReset = false  // Only check first frame
                    print("✅ First frame processed - UI cleared, ready for new sequence")
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
            print("❌ Error processing frame: \(error.localizedDescription)")
            if let apiError = error as? APIError {
                print("   API Error details: \(apiError.errorDescription ?? "unknown")")
            }
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
        // Reset backend again to ensure it's clean, then clear UI
        Task {
            do {
                print("🔄 Resetting backend before ready for next sequence...")
                _ = try await translationEndpoint.resetSequence()
                print("✅ Backend reset before ready")
                // Add a small delay to ensure reset is processed
                try await Task.sleep(nanoseconds: 100_000_000) // 0.1 second
                
                await MainActor.run {
                    // Clear UI and allow new sequence
                    currentSequence = []
                    lastWord = ""
                    isBackendReset = false
                    isResetComplete = true
                    resetTime = Date()  // Update reset time
                    framesAfterReset = 0  // Reset frame counter
                    firstFrameAfterReset = true  // Mark first frame after reset
                    print("✅ Ready for next sequence - backend reset and UI cleared")
                }
            } catch {
                print("⚠️ Failed to reset before ready: \(error.localizedDescription)")
                // Still clear UI even if reset fails
                await MainActor.run {
                    currentSequence = []
                    lastWord = ""
                    isBackendReset = false
                    isResetComplete = true
                    resetTime = Date()
                    framesAfterReset = 0
                    firstFrameAfterReset = true
                }
            }
        }
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
    private let sessionQueue = DispatchQueue(label: "CameraSessionQueue")
    private var frameCount = 0  // Track frame count for debugging
    
    func startCapture() {
        sessionQueue.async {
            print("🔍 DEBUG: startCapture() called")
            print("   Session isRunning: \(self.session.isRunning)")
            print("   Session isInterrupted: \(self.session.isInterrupted)")
            
            // Stop if already running
            if self.session.isRunning {
                print("   Stopping existing session...")
                self.session.stopRunning()
                Thread.sleep(forTimeInterval: 0.2)
            }
            
            // Simple setup - bare minimum
            print("   Beginning configuration...")
            self.session.beginConfiguration()
            self.session.sessionPreset = .high
            
            // Remove existing inputs/outputs
            print("   Removing \(self.session.inputs.count) inputs, \(self.session.outputs.count) outputs")
            for input in self.session.inputs {
                self.session.removeInput(input)
            }
            for output in self.session.outputs {
                self.session.removeOutput(output)
            }
            
            // Setup camera
            print("   Getting camera device...")
            guard let camera = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .front) else {
                self.session.commitConfiguration()
                DispatchQueue.main.async {
                    self.frameStatus = .error("Unable to access camera")
                }
                print("❌ DEBUG: Failed to get camera device")
                return
            }
            print("   Camera device found: \(camera.localizedName)")
            
            guard let input = try? AVCaptureDeviceInput(device: camera) else {
                self.session.commitConfiguration()
                DispatchQueue.main.async {
                    self.frameStatus = .error("Unable to create camera input")
                }
                print("❌ DEBUG: Failed to create camera input")
                return
            }
            
            guard self.session.canAddInput(input) else {
                self.session.commitConfiguration()
                DispatchQueue.main.async {
                    self.frameStatus = .error("Cannot add camera input")
                }
                print("❌ DEBUG: Cannot add input to session")
                return
            }
            
            print("   Adding camera input...")
            self.session.addInput(input)
            
            // Setup output
            print("   Configuring output...")
            self.output.videoSettings = [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA]
            self.output.setSampleBufferDelegate(self, queue: DispatchQueue(label: "CameraQueue"))
            
            guard self.session.canAddOutput(self.output) else {
                self.session.removeInput(input)
                self.session.commitConfiguration()
                DispatchQueue.main.async {
                    self.frameStatus = .error("Cannot add camera output")
                }
                print("DEBUG: Cannot add output to session")
                return
            }
            
            print("   Adding output...")
            self.session.addOutput(self.output)
            self.session.commitConfiguration()
            print("   Configuration committed")
            
            // Start running
            print("   Calling startRunning()...")
            self.session.startRunning()
            
            // Check if it actually started
            Thread.sleep(forTimeInterval: 0.5)
            print("   After 0.5s - isRunning: \(self.session.isRunning), isInterrupted: \(self.session.isInterrupted)")
            
            if self.session.isRunning {
                print("✅ Camera started successfully")
            } else {
                print("⚠️ Camera session not running after startRunning()")
                if self.session.isInterrupted {
                    print("   Session is interrupted!")
                }
            }
        }
    }
    
    func stopCapture() {
        sessionQueue.async {
            guard self.session.isRunning else { return }
            
            self.session.beginConfiguration()
            for input in self.session.inputs {
                self.session.removeInput(input)
            }
            for output in self.session.outputs {
                self.session.removeOutput(output)
            }
            self.session.commitConfiguration()
            self.session.stopRunning()
            print("✅ Camera stopped")
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
        
        // Debug: Log first few frames to confirm capture is working
        self.frameCount += 1
        if self.frameCount <= 5 {
            print("📹 DEBUG: Frame #\(self.frameCount) captured! Callback set: \(self.onFrameCaptured != nil)")
        } else if self.frameCount % 30 == 0 {
            print("📹 DEBUG: Frame #\(self.frameCount) captured")
        }
        
        guard let callback = onFrameCaptured else {
            if self.frameCount <= 10 {
                print("⚠️ DEBUG: Frame #\(self.frameCount) captured but callback is nil!")
            }
            return
        }
        callback(sampleBuffer)
    }
    
    func captureOutput(_ output: AVCaptureOutput, didDrop sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        // Log dropped frames occasionally
        if Int.random(in: 0..<50) == 0 {
            print("⚠️ Frame dropped by camera")
        }
    }
}

// MARK: - Frame Processor
class FrameProcessor: ObservableObject {
    @Published var isProcessing = false
}


