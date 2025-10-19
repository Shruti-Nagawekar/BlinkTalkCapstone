//
//  Camera_ViewApp.swift
//  Camera_View
//
//  Created by Owner on 9/29/25.
//

import SwiftUI
import CoreData

@main
struct Camera_ViewApp: App {
    let persistenceController = PersistenceController.shared

    var body: some Scene {
        WindowGroup {
            IntroView()
                .environment(\.managedObjectContext, persistenceController.container.viewContext)
        }
    }
}
