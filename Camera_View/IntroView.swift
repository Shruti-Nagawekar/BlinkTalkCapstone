import SwiftUI

struct IntroView: View {
    var body: some View {
        NavigationStack {
            ZStack {
                LinearGradient(colors: [.black, .blue.opacity(0.7)], startPoint: .top, endPoint: .bottom)
                    .ignoresSafeArea()
                VStack(spacing: 24) {
                    Text("Welcome to BlinkTalk")
                        .font(.largeTitle).bold()
                        .foregroundColor(.white)
                        .multilineTextAlignment(.center)
                    Text("Private, fast, camera-powered experiences.")
                        .foregroundColor(.white.opacity(0.8))
                        .multilineTextAlignment(.center)
                    NavigationLink("Continue", destination: HomeView())
                        .buttonStyle(.borderedProminent)
                }
                .padding(32)
            }
        }
    }
}

struct IntroView_Previews: PreviewProvider {
    static var previews: some View {
        IntroView()
    }
}


