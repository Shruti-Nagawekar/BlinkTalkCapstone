import SwiftUI
import AVFoundation
import UIKit

struct CameraView: View {
    @Binding var path: NavigationPath
    @StateObject private var cameraManager = CameraManager()
    @State private var translatedText: String = ""
    @State private var navigateToResult = false

    var body: some View {
        
        ZStack {
            GeometryReader { geometry in
                LiveCameraPreview(size: geometry.size, cameraManager: cameraManager)
            }
            .ignoresSafeArea()
        }
        .onAppear {
            cameraManager.startCamera()
            startPollingForTranslation()
        }
        .onDisappear {
            cameraManager.stopCamera()
        }
        .navigationDestination(isPresented: $navigateToResult) {
            TranslationResultView(translatedText: translatedText)
        }
    }

    func startPollingForTranslation() {
        Timer.scheduledTimer(withTimeInterval: 2.0, repeats: true) { timer in
            guard let url = URL(string: "http://192.168.1.124:8011/get_translation") else { return }

            URLSession.shared.dataTask(with: url) { data, response, error in
                if let error = error {
                    print("Polling error: \(error.localizedDescription)")
                }

                if let data = data,
                   let json = try? JSONSerialization.jsonObject(with: data) as? [String: String],
                   let result = json["output"] {

                    print("Received from server: \(result)")

                    if !result.isEmpty {
                        DispatchQueue.main.async {
                            translatedText = result
                            navigateToResult = true
                            timer.invalidate()
                        }
                    }
                } else {
                    print("No valid result yet.")
                }
            }.resume()
        }
    }
}


class CameraManager: NSObject, ObservableObject, AVCaptureVideoDataOutputSampleBufferDelegate {
    @Published var session = AVCaptureSession()

    override init() {
        super.init()
        checkPermissions()
    }

    func checkPermissions() {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            configureCamera()
        case .notDetermined:
            AVCaptureDevice.requestAccess(for: .video) { granted in
                if granted { self.configureCamera() }
            }
        default:
            print("Camera access restricted")
        }
    }

    func configureCamera() {
        DispatchQueue.global(qos: .background).async {
            guard let device = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back) else {
                print("No camera found!")
                return
            }

            do {
                let input = try AVCaptureDeviceInput(device: device)
                self.session.beginConfiguration()

                if let existingInput = self.session.inputs.first {
                    self.session.removeInput(existingInput)
                }

                if self.session.canAddInput(input) {
                    self.session.addInput(input)
                }

                let videoOutput = AVCaptureVideoDataOutput()
                videoOutput.setSampleBufferDelegate(self, queue: DispatchQueue(label: "videoQueue"))
                if self.session.canAddOutput(videoOutput) {
                    self.session.addOutput(videoOutput)
                }

                self.session.commitConfiguration()
                self.session.startRunning()
            } catch {
                print("Error setting up camera: \(error.localizedDescription)")
            }
        }
    }

    func startCamera() {
        if !session.isRunning {
            session.startRunning()
        }
    }

    func stopCamera() {
        if session.isRunning {
            session.stopRunning()
        }
    }

    func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        guard let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }

        let ciImage = CIImage(cvPixelBuffer: pixelBuffer)
        let context = CIContext()

        if let cgImage = context.createCGImage(ciImage, from: ciImage.extent) {
            let uiImage = UIImage(cgImage: cgImage)
            sendFrameToPython(image: uiImage, user: "User1")
        }
    }
}

struct LiveCameraPreview: UIViewRepresentable {
    var size: CGSize
    var cameraManager: CameraManager  // ✅ Accept manager as parameter

    func makeUIView(context: Context) -> UIView {
        let view = UIView(frame: CGRect(origin: .zero, size: size))
        view.backgroundColor = .black

        let previewLayer = AVCaptureVideoPreviewLayer(session: cameraManager.session)
        previewLayer.frame = view.bounds
        previewLayer.videoGravity = .resizeAspectFill
        view.layer.addSublayer(previewLayer)

        return view
    }

    func updateUIView(_ uiView: UIView, context: Context) { }
}

func sendFrameToPython(image: UIImage, user: String) {
    guard let imageData = image.jpegData(compressionQuality: 0.5) else { return }
    let base64String = imageData.base64EncodedString()

    guard let url = URL(string: "http://192.168.1.124:8011/send_frame") else { return }
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")

    let payload: [String: Any] = [
        "frame_data": base64String,
        "user": user
    ]

    do {
        request.httpBody = try JSONSerialization.data(withJSONObject: payload, options: [])
    } catch {
        print("Error serializing payload: \(error)")
        return
    }

    URLSession.shared.dataTask(with: request) { data, response, error in
        if let error = error {
            print("HTTP Request Failed: \(error)")
            return
        }
        if let data = data,
           let responseJSON = try? JSONSerialization.jsonObject(with: data) {
            print("Response: \(responseJSON)")
        }
    }.resume()
}


