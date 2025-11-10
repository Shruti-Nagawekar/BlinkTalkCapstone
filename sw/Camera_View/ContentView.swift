import SwiftUI
import AVFoundation

struct ContentView: View {
    @State private var lastFrameTime: Date = .now
    @State private var frameRate: Double = 0.0
    @State private var detectedObjects: [DetectedObject] = []
    @State private var previewSize: CGSize = .zero

    var body: some View {
        GeometryReader { geometry in
            ZStack(alignment: .bottom) {
                CameraViewWithDetection { sampleBuffer in
                    calculateFrameRate()
                } onObjectsDetected: { objects in
                    detectedObjects = objects
                }
                .edgesIgnoringSafeArea(.all)
                .onAppear {
                    previewSize = geometry.size
                }
                .onChange(of: geometry.size) { oldValue, newValue in
                    previewSize = newValue
                }

                // Object detection overlay
                ObjectDetectionOverlay(
                    detectedObjects: detectedObjects,
                    previewSize: previewSize
                )
                .allowsHitTesting(false)

                VStack {
                    Spacer()
                    
                    HStack {
                        Text(String(format: "FPS: %.1f", frameRate))
                            .font(.headline)
                            .padding(8)
                            .background(.black.opacity(0.6))
                            .cornerRadius(10)
                            .foregroundColor(.white)
                        
                        Spacer()
                        
                        Text("Objects: \(detectedObjects.count)")
                            .font(.headline)
                            .padding(8)
                            .background(.black.opacity(0.6))
                            .cornerRadius(10)
                            .foregroundColor(.white)
                    }
                    .padding(.horizontal)
                    .padding(.bottom, 30)
                }
            }
        }
    }

    private func calculateFrameRate() {
        let now = Date()
        let interval = now.timeIntervalSince(lastFrameTime)
        frameRate = 1.0 / interval
        lastFrameTime = now
    }

    private func imageFromSampleBuffer(_ sampleBuffer: CMSampleBuffer) -> UIImage? {
        guard let imageBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return nil }
        let ciImage = CIImage(cvPixelBuffer: imageBuffer)
        let context = CIContext()
        guard let cgImage = context.createCGImage(ciImage, from: ciImage.extent) else { return nil }
        return UIImage(cgImage: cgImage)
    }
}
