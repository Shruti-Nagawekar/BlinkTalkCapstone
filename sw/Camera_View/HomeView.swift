import SwiftUI
import CoreData

struct HomeView: View {
    @Environment(\.managedObjectContext) private var viewContext
    @FetchRequest(sortDescriptors: [NSSortDescriptor(keyPath: \UserProfile.createdAt, ascending: false)], animation: .default)
    private var profiles: FetchedResults<UserProfile>

    @State private var newName: String = ""
    @State private var showBlinkDetection: Bool = false
    @State private var selectedProfile: UserProfile? = nil

    var body: some View {
        ZStack {
            // Black background
            Color.black
                .ignoresSafeArea()
            
            ScrollView {
                VStack(spacing: 30) {
                    // Title
                    Text("BlinkTalk")
                        .font(.largeTitle)
                        .fontWeight(.bold)
                        .foregroundColor(.white)
                        .padding(.top, 20)
                    
                    // Create Profile Section
                    VStack(alignment: .leading, spacing: 15) {
                        Text("Create Profile")
                            .font(.headline)
                            .foregroundColor(.white)
                        
                        HStack {
                            TextField("Name", text: $newName)
                                .padding()
                                .background(Color.white.opacity(0.1))
                                .foregroundColor(.white)
                                .cornerRadius(10)
                            
                            Button("Add") {
                                addProfile()
                            }
                            .padding()
                            .background(newName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? Color.white.opacity(0.3) : Color.white)
                            .foregroundColor(newName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? .white.opacity(0.5) : .black)
                            .cornerRadius(10)
                            .disabled(newName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                        }
                    }
                    .padding()
                    .background(Color.white.opacity(0.05))
                    .cornerRadius(15)
                    
                    // Profiles Section
                    VStack(alignment: .leading, spacing: 15) {
                        Text("Profiles")
                            .font(.headline)
                            .foregroundColor(.white)
                        
                        if profiles.isEmpty {
                            Text("No profiles yet. Create one above.")
                                .foregroundColor(.white.opacity(0.6))
                                .padding()
                        } else {
                            ForEach(profiles) { profile in
                                HStack {
                                    VStack(alignment: .leading, spacing: 4) {
                                        Text(profile.name ?? "Unnamed")
                                            .font(.headline)
                                            .foregroundColor(.white)
                                        if let createdAt = profile.createdAt {
                                            Text(createdAt, style: .date)
                                                .font(.caption)
                                                .foregroundColor(.white.opacity(0.6))
                                        }
                                    }
                                    Spacer()
                                    if let calibrationProfile = profile.calibrationProfile, !calibrationProfile.isEmpty {
                                        Text(calibrationProfile.capitalized)
                                            .font(.caption)
                                            .foregroundColor(.black)
                                            .padding(.horizontal, 8)
                                            .padding(.vertical, 4)
                                            .background(Color.white)
                                            .cornerRadius(6)
                                    }
                                    
                                    Button("Use") {
                                        // Set profile to show sheet
                                        selectedProfile = profile
                                    }
                                    .padding(.horizontal, 20)
                                    .padding(.vertical, 10)
                                    .background(Color.white)
                                    .foregroundColor(.black)
                                    .cornerRadius(10)
                                }
                                .padding()
                                .background(Color.white.opacity(0.05))
                                .cornerRadius(10)
                            }
                        }
                    }
                    .padding()
                    .background(Color.white.opacity(0.05))
                    .cornerRadius(15)
                }
                .padding()
            }
        }
        .navigationTitle("")
        .navigationBarTitleDisplayMode(.inline)
        .sheet(item: $selectedProfile) { profile in
            NavigationStack {
                CalibrationView(profile: profile, onContinue: {
                    print("onContinue callback called")
                    selectedProfile = nil  // Dismiss sheet
                    // Small delay to ensure sheet dismisses before showing new view
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                        print("Showing BlinkDetectionView")
                        showBlinkDetection = true
                    }
                })
            }
        }
        .fullScreenCover(isPresented: $showBlinkDetection) {
            BlinkDetectionView()
        }
    }

    private func addProfile() {
        let profile = UserProfile(context: viewContext)
        profile.id = UUID()
        profile.name = newName.trimmingCharacters(in: .whitespacesAndNewlines)
        profile.createdAt = Date()
        do { 
            try viewContext.save()
            // Automatically show calibration view for the new profile
            newName = ""
            selectedProfile = profile  // This will trigger the sheet
        } catch { 
            print("Save error: \(error)") 
        }
    }

    private func deleteProfile(_ profile: UserProfile) {
        viewContext.delete(profile)
        do { 
            try viewContext.save() 
        } catch { 
            print("Delete error: \(error)") 
        }
    }
    
    private func deleteProfiles(offsets: IndexSet) {
        offsets.map { profiles[$0] }.forEach(viewContext.delete)
        do { try viewContext.save() } catch { print("Delete error: \(error)") }
    }
}

struct HomeView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationStack { HomeView() }
            .environment(\.managedObjectContext, PersistenceController.shared.container.viewContext)
    }
}


