//
//   CameraView.swift
//  Camera_View
//
//  Created by Owner on 10/7/25.
//

import SwiftUI
import AVFoundation
import UIKit
import Vision

struct CameraView: UIViewRepresentable {
    typealias UIViewType = PreviewView

    var onFrameCaptured: (CMSampleBuffer) -> Void

    func makeUIView(context: Context) -> PreviewView {
        let view = PreviewView()
        view.videoPreviewLayer.videoGravity = .resizeAspectFill
        context.coordinator.startSession(for: view, onFrameCaptured: onFrameCaptured)
        return view
    }

    func updateUIView(_ uiView: PreviewView, context: Context) {}

    func makeCoordinator() -> CameraCoordinator {
        CameraCoordinator()
    }
}

struct CameraViewWithDetection: UIViewRepresentable {
    typealias UIViewType = PreviewView
    
    var onFrameCaptured: (CMSampleBuffer) -> Void
    var onObjectsDetected: ([DetectedObject]) -> Void

    func makeUIView(context: Context) -> PreviewView {
        let view = PreviewView()
        view.videoPreviewLayer.videoGravity = .resizeAspectFill
        context.coordinator.startSession(for: view, onFrameCaptured: onFrameCaptured)
        context.coordinator.onObjectsDetected = { objects in
            DispatchQueue.main.async {
                self.onObjectsDetected(objects)
            }
        }
        return view
    }

    func updateUIView(_ uiView: PreviewView, context: Context) {}

    func makeCoordinator() -> CameraCoordinator {
        CameraCoordinator()
    }
}

class CameraCoordinator: NSObject, AVCaptureVideoDataOutputSampleBufferDelegate {
    private let session = AVCaptureSession()
    private let output = AVCaptureVideoDataOutput()
    private let visionQueue = DispatchQueue(label: "VisionQueue")
    var onObjectsDetected: (([DetectedObject]) -> Void)?

    func startSession(for previewView: PreviewView, onFrameCaptured: @escaping (CMSampleBuffer) -> Void) {
        session.beginConfiguration()
        session.sessionPreset = .high
        print("🎥 Starting camera session...")
        // Select camera
        guard let camera = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back),
              let input = try? AVCaptureDeviceInput(device: camera),
              session.canAddInput(input) else {
            print("⚠️ Unable to access camera input.")
            return
        }
        session.addInput(input)

        // Output configuration
        output.videoSettings = [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA]
        output.setSampleBufferDelegate(self, queue: DispatchQueue(label: "CameraFeedQueue"))
        guard session.canAddOutput(output) else { return }
        session.addOutput(output)

        session.commitConfiguration()

        previewView.videoPreviewLayer.session = session
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .notDetermined:
            AVCaptureDevice.requestAccess(for: .video) { granted in
                print("Camera permission granted? \(granted)")
            }
        default:
            break
        }
        session.startRunning()
        print("✅ Camera session started successfully.")

        // Capture closure
        self.frameHandler = onFrameCaptured
    }

    private var frameHandler: ((CMSampleBuffer) -> Void)?

    func captureOutput(_ output: AVCaptureOutput,
                       didOutput sampleBuffer: CMSampleBuffer,
                       from connection: AVCaptureConnection) {
        guard let imageBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
        
        // Process frame for object detection
        processFrameForObjectDetection(imageBuffer: imageBuffer)
        
        // Send frame to server
        let ciImage = CIImage(cvPixelBuffer: imageBuffer)
        let context = CIContext()
        guard let cgImage = context.createCGImage(ciImage, from: ciImage.extent) else { return }
        let uiImage = UIImage(cgImage: cgImage)
        guard let jpegData = uiImage.jpegData(compressionQuality: 0.5) else { return }
        sendFrameToServer(jpegData)
    }
    
    private func processFrameForObjectDetection(imageBuffer: CVPixelBuffer) {
        let request = VNDetectRectanglesRequest { [weak self] (request: VNRequest, error: Error?) in
            guard let self = self,
                  let results = request.results else { return }
            
            let detectedObjects = results.compactMap { observation -> DetectedObject? in
                guard let objectObservation = observation as? VNDetectedObjectObservation else { return nil }
                return DetectedObject(
                    boundingBox: objectObservation.boundingBox,
                    confidence: objectObservation.confidence,
                    label: "Object"
                )
            }
            
            self.onObjectsDetected?(detectedObjects)
        }
        
        let handler = VNImageRequestHandler(cvPixelBuffer: imageBuffer, options: [:])
        try? handler.perform([request])
    }

    func sendFrameToServer(_ data: Data) {
        let baseURL = UserDefaults.standard.string(forKey: "serverURL") ?? "http://192.168.1.10:5000"
        guard let url = URL(string: baseURL + "/frame") else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.httpBody = data
        request.setValue("image/jpeg", forHTTPHeaderField: "Content-Type")
        URLSession.shared.dataTask(with: request).resume()
    }
}

/// UIView subclass hosting the AVCaptureVideoPreviewLayer
class PreviewView: UIView {
    override class var layerClass: AnyClass {
        AVCaptureVideoPreviewLayer.self
    }

    var videoPreviewLayer: AVCaptureVideoPreviewLayer {
        return layer as! AVCaptureVideoPreviewLayer
    }
}

// MARK: - Object Detection Models
struct DetectedObject {
    let boundingBox: CGRect
    let confidence: Float
    let label: String
}

// MARK: - Object Detection Overlay View
struct ObjectDetectionOverlay: View {
    let detectedObjects: [DetectedObject]
    let previewSize: CGSize
    
    var body: some View {
        ZStack {
            ForEach(Array(detectedObjects.enumerated()), id: \.offset) { index, object in
                Rectangle()
                    .stroke(Color.green, lineWidth: 2)
                    .frame(
                        width: object.boundingBox.width * previewSize.width,
                        height: object.boundingBox.height * previewSize.height
                    )
                    .position(
                        x: object.boundingBox.midX * previewSize.width,
                        y: (1 - object.boundingBox.midY) * previewSize.height
                    )
                
                Text("\(object.label) \(Int(object.confidence * 100))%")
                    .font(.caption)
                    .foregroundColor(.white)
                    .padding(4)
                    .background(Color.green.opacity(0.8))
                    .cornerRadius(4)
                    .position(
                        x: object.boundingBox.midX * previewSize.width,
                        y: (1 - object.boundingBox.midY) * previewSize.height - 20
                    )
            }
        }
    }
}
