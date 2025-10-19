//
//  HomePage.swift
//  BlinkTalk
//
//  Created by Bailey Pratt on 5/1/25.
//

import SwiftUI

struct HomePage: View {
    @Binding var path: NavigationPath
    
    var body: some View {
        GeometryReader { geometry in
            VStack(spacing: 10) {
                
                Image("BlinkTalk")
                    .resizable()
                    .aspectRatio(contentMode: .fit)
                    .frame(width: 300, height: 300)
                
                Button(action: {
                    path.append("User")
                }) {
                    Text("Click to Proceed")
                        .frame(width: 200, height: 30)
                        .background(Color.blue)
                        .foregroundColor(.white)
                        .cornerRadius(8)
                }
            }
            .frame(width: geometry.size.height, height: geometry.size.width)
            .rotationEffect(.degrees(90))
            .position(x: geometry.size.width / 2, y: geometry.size.height / 2)
            .offset(y: 0)
        }
        .background(Color.white)
    }
}

