import SwiftUI

struct User: View {
    @Binding var path: NavigationPath

    var body: some View {
        GeometryReader { geometry in
            VStack(spacing: 20) {
                Text("Select Calibration")
                    .font(.title)
                    .bold()

                Button(action: {
                    sendCalibration(option: "slow")
                    path.append("CameraView")
                }) {
                    Text("Slow Timing")
                        .frame(width: 200, height: 50)
                        .background(Color.blue)
                        .foregroundColor(.white)
                        .cornerRadius(8)
                }

                Button(action: {
                    sendCalibration(option: "medium")
                    path.append("CameraView")
                }) {
                    Text("Medium Timing")
                        .frame(width: 200, height: 50)
                        .background(Color.red)
                        .foregroundColor(.white)
                        .cornerRadius(8)
                }
            }
            .frame(width: geometry.size.height, height: geometry.size.width)
            .rotationEffect(.degrees(90))
            .position(x: geometry.size.width / 2, y: geometry.size.height / 2)
            .offset(y: 0) // ← adjust this value to shift left/right
        }
        .background(Color.black)
        /*
        .navigationDestination(for: String.self) { destination in
            if destination == "CameraView" {
                CameraView(path: $path)
            }
        }
        */
    }

    func sendCalibration(option: String) {
        guard let url = URL(string: "http://192.168.1.124:8011/set_calibration") else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let payload = ["option": option]

        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: payload)
        } catch {
            print("Error serializing JSON: \(error)")
            return
        }

        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                print("HTTP request failed: \(error)")
                return
            }
            if let data = data,
               let responseJSON = try? JSONSerialization.jsonObject(with: data) {
                print("Calibration response: \(responseJSON)")
            }
        }.resume()
    }
}

