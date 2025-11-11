//
//  CalibrationView.swift
//  Camera_View
//
//  Calibration profile selection view
//

import SwiftUI
import CoreData

struct CalibrationView: View {
    @Environment(\.managedObjectContext) private var viewContext
    @Environment(\.dismiss) private var dismiss
    
    let profile: UserProfile
    let onContinue: () -> Void
    
    @State private var selectedProfile: String = "medium"
    @State private var currentActiveProfile: String = "medium"
    @State private var isLoading: Bool = false
    @State private var isSaving: Bool = false
    @State private var errorMessage: String? = nil
    
    private let calibrationEndpoint = CalibrationEndpoint()
    
    var body: some View {
        ZStack {
            // Black background
            Color.black
                .ignoresSafeArea()
            
            VStack(spacing: 30) {
                // Title
                Text("Select Calibration Profile")
                    .font(.title)
                    .fontWeight(.bold)
                    .foregroundColor(.white)
                    .padding(.top, 40)
                
                // Current active profile display - updates in real-time with selection
                VStack(spacing: 8) {
                    Text("Current Profile")
                        .font(.caption)
                        .foregroundColor(.white.opacity(0.6))
                    if isLoading && currentActiveProfile.isEmpty {
                        // Show loading indicator only while fetching from backend
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: .white))
                    } else {
                        // Show selected profile (updates in real-time) or backend profile if available
                        Text(selectedProfile.capitalized)
                            .font(.headline)
                            .foregroundColor(.white)
                    }
                }
                .padding()
                .frame(maxWidth: .infinity)
                .background(Color.white.opacity(0.1))
                .cornerRadius(10)
                .padding(.horizontal)
                
                // Profile selection buttons
                VStack(spacing: 20) {
                    // Slow profile button
                    Button(action: {
                        selectedProfile = "slow"
                    }) {
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("Slow")
                                    .font(.title2)
                                    .fontWeight(.bold)
                                    .foregroundColor(.white)
                                Text("For users with slower blink patterns")
                                    .font(.caption)
                                    .foregroundColor(.white.opacity(0.6))
                            }
                            Spacer()
                            if selectedProfile == "slow" {
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundColor(.white)
                                    .font(.title2)
                            }
                        }
                        .padding()
                        .frame(maxWidth: .infinity)
                        .background(selectedProfile == "slow" ? Color.white.opacity(0.2) : Color.white.opacity(0.1))
                        .cornerRadius(12)
                    }
                    
                    // Medium profile button
                    Button(action: {
                        selectedProfile = "medium"
                    }) {
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("Medium")
                                    .font(.title2)
                                    .fontWeight(.bold)
                                    .foregroundColor(.white)
                                Text("Standard timing for typical users")
                                    .font(.caption)
                                    .foregroundColor(.white.opacity(0.6))
                            }
                            Spacer()
                            if selectedProfile == "medium" {
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundColor(.white)
                                    .font(.title2)
                            }
                        }
                        .padding()
                        .frame(maxWidth: .infinity)
                        .background(selectedProfile == "medium" ? Color.white.opacity(0.2) : Color.white.opacity(0.1))
                        .cornerRadius(12)
                    }
                }
                .padding(.horizontal)
                
                Spacer()
                
                // Error message
                if let error = errorMessage {
                    Text(error)
                        .font(.caption)
                        .foregroundColor(.white)
                        .padding()
                        .frame(maxWidth: .infinity)
                        .background(Color.white.opacity(0.1))
                        .cornerRadius(10)
                        .padding(.horizontal)
                }
                
                // Action buttons
                VStack(spacing: 15) {
                    // Save and Continue button
                    Button(action: {
                        saveAndContinue()
                    }) {
                        HStack {
                            if isSaving {
                                ProgressView()
                                    .progressViewStyle(CircularProgressViewStyle(tint: .black))
                            } else {
                                Text("Save & Continue")
                                    .fontWeight(.semibold)
                            }
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(isSaving ? Color.white.opacity(0.5) : Color.white)
                        .foregroundColor(.black)
                        .cornerRadius(12)
                    }
                    .disabled(isSaving)
                    .opacity(isLoading ? 0.5 : 1.0)
                    
                    // Delete Profile button
                    Button(action: {
                        deleteProfile()
                    }) {
                        HStack {
                            Image(systemName: "trash")
                            Text("Delete Profile")
                                .fontWeight(.semibold)
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.white.opacity(0.1))
                        .foregroundColor(.white)
                        .cornerRadius(12)
                    }
                    .disabled(isSaving)
                    .opacity(isLoading ? 0.5 : 1.0)
                    
                    // Cancel button
                    Button(action: {
                        dismiss()
                    }) {
                        Text("Cancel")
                            .fontWeight(.semibold)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.white.opacity(0.1))
                            .foregroundColor(.white)
                            .cornerRadius(12)
                    }
                    .disabled(isSaving)
                    .opacity(isLoading ? 0.5 : 1.0)
                }
                .padding(.horizontal)
                .padding(.bottom, 40)
            }
        }
        .onAppear {
            loadCurrentProfile()
            loadSavedProfile()
        }
    }
    
    private func loadCurrentProfile() {
        isLoading = true
        errorMessage = nil
        
        // Set a timeout to ensure isLoading doesn't stay true forever
        Task {
            // Add timeout - if it takes more than 5 seconds, just use default
            try? await Task.sleep(nanoseconds: 5_000_000_000) // 5 seconds
            await MainActor.run {
                if isLoading {
                    print("⚠️ Profile loading timed out, using default")
                    currentActiveProfile = "medium"
                    isLoading = false
                }
            }
        }
        
        Task {
            do {
                let response = try await calibrationEndpoint.getActiveProfile()
                await MainActor.run {
                    currentActiveProfile = response.profile
                    isLoading = false
                    print("✅ Loaded current profile: \(currentActiveProfile)")
                }
            } catch {
                await MainActor.run {
                    print("⚠️ Failed to load current profile: \(error.localizedDescription)")
                    // Don't block the UI if loading fails - allow user to proceed
                    currentActiveProfile = "medium" // Default fallback
                    isLoading = false
                    // Only show error if it's critical, otherwise silently fail
                    // errorMessage = "Failed to load current profile: \(error.localizedDescription)"
                }
            }
        }
    }
    
    private func loadSavedProfile() {
        // Load saved profile from UserProfile if it exists
        if let savedProfile = profile.calibrationProfile, !savedProfile.isEmpty {
            selectedProfile = savedProfile
        } else {
            selectedProfile = currentActiveProfile
        }
    }
    
    private func saveAndContinue() {
        guard !isSaving else { 
            print("Save blocked: isSaving=\(isSaving)")
            return 
        }
        
        // If still loading, just proceed anyway - don't block the user
        if isLoading {
            print("⚠️ Still loading profile, but proceeding with save anyway")
            isLoading = false
        }
        
        print("Starting save and continue...")
        isSaving = true
        errorMessage = nil
        
        Task {
            do {
                // Set profile on backend
                print("Setting profile on backend: \(selectedProfile)")
                _ = try await calibrationEndpoint.setProfile(selectedProfile)
                print("Backend profile set successfully")
            } catch {
                print("⚠️ Backend API error (will save locally anyway): \(error.localizedDescription)")
                // Continue even if backend fails
            }
            
            // Always save to Core Data and proceed, regardless of backend success/failure
            await MainActor.run {
                profile.calibrationProfile = selectedProfile
                do {
                    try viewContext.save()
                    print("✅ Profile saved to Core Data")
                    isSaving = false
                    // Call the onContinue callback to navigate
                    print("Calling onContinue callback")
                    onContinue()
                } catch {
                    print("❌ Core Data save error: \(error)")
                    errorMessage = "Failed to save profile: \(error.localizedDescription)"
                    isSaving = false
                }
            }
        }
    }
    
    private func deleteProfile() {
        viewContext.delete(profile)
        do {
            try viewContext.save()
            dismiss()
        } catch {
            errorMessage = "Failed to delete profile: \(error.localizedDescription)"
        }
    }
}

