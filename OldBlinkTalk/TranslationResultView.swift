//
//  TranslationResultView.swift
//  BlinkTalk
//
//  Created by Bailey Pratt on 4/22/25.
//

import SwiftUI

struct TranslationResultView: View {
    let translatedText: String

    var body: some View {
        GeometryReader { geometry in
            VStack(spacing: 20) {
                Text("Final Translation")
                    .font(.title)

                Text(translatedText)
                    .font(.largeTitle)
                    .padding()
            }
            // flip width and height
            .frame(width: geometry.size.height, height: geometry.size.width)
            // rotate counterclockwise
            .rotationEffect(.degrees(90))
            // centering
            .position(x: geometry.size.width / 2, y: geometry.size.height / 2)
        }
        .edgesIgnoringSafeArea(.all)
    }
}


