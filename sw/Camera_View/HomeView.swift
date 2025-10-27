import SwiftUI
import CoreData

struct HomeView: View {
    @Environment(\.managedObjectContext) private var viewContext
    @FetchRequest(sortDescriptors: [NSSortDescriptor(keyPath: \UserProfile.createdAt, ascending: false)], animation: .default)
    private var profiles: FetchedResults<UserProfile>

    @State private var newName: String = ""
    @State private var serverURLString: String = UserDefaults.standard.string(forKey: "serverURL") ?? "http://192.168.1.10:5000"
    @State private var showCamera: Bool = false
    @State private var apiStatus: String = "Not tested"
    @State private var isTestingAPI: Bool = false
    
    // API Endpoints
    private let calibrationEndpoint = CalibrationEndpoint()
    private let healthEndpoint = HealthEndpoint()

    var body: some View {
        List {
            Section(header: Text("Server")) {
                TextField("Server base URL", text: $serverURLString)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                Button("Save Server URL") {
                    UserDefaults.standard.set(serverURLString, forKey: "serverURL")
                }
                
                HStack {
                    Text("Status: \(apiStatus)")
                        .foregroundColor(apiStatus.contains("OK") ? .green : 
                                        apiStatus.contains("Error") ? .red : .secondary)
                    Spacer()
                }
                .padding(.vertical, 4)
                
                Button("Test API Connection") {
                    testAPIConnection()
                }
                .disabled(isTestingAPI)
            }

            Section(header: Text("Create Profile")) {
                HStack {
                    TextField("Name", text: $newName)
                    Button("Add") { addProfile() }
                        .disabled(newName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }
            }

            Section(header: Text("Profiles")) {
                ForEach(profiles) { profile in
                    HStack {
                        VStack(alignment: .leading) {
                            Text(profile.name ?? "Unnamed")
                                .font(.headline)
                            if let createdAt = profile.createdAt {
                                Text(createdAt, style: .date)
                                    .foregroundColor(.secondary)
                            }
                        }
                        Spacer()
                        Button("Use") {
                            showCamera = true
                        }
                    }
                }
                .onDelete(perform: deleteProfiles)
            }
        }
        .navigationTitle("Home")
        .toolbar { EditButton() }
        .sheet(isPresented: $showCamera) {
            BlinkDetectionView()
        }
    }

    private func addProfile() {
        let profile = UserProfile(context: viewContext)
        profile.id = UUID()
        profile.name = newName.trimmingCharacters(in: .whitespacesAndNewlines)
        profile.createdAt = Date()
        do { try viewContext.save(); newName = "" } catch { print("Save error: \(error)") }
    }

    private func deleteProfiles(offsets: IndexSet) {
        offsets.map { profiles[$0] }.forEach(viewContext.delete)
        do { try viewContext.save() } catch { print("Delete error: \(error)") }
    }
    
    private func testAPIConnection() {
        isTestingAPI = true
        apiStatus = "Testing..."
        
        Task {
            do {
                // Test health endpoint
                let health = try await healthEndpoint.checkHealth()
                apiStatus = "OK - Connected: \(health.status)"
                
                // Test calibration endpoint
                let calibration = try await calibrationEndpoint.getActiveProfile()
                apiStatus += "\nProfile: \(calibration.profile)"
            } catch let error as APIError {
                apiStatus = "Error: \(error.localizedDescription)"
            } catch {
                apiStatus = "Error: \(error.localizedDescription)"
            }
            
            isTestingAPI = false
        }
    }
}

struct HomeView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationStack { HomeView() }
            .environment(\.managedObjectContext, PersistenceController.shared.container.viewContext)
    }
}


