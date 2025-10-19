# Week 6: Swift Networking & UX Glue - Specification

## 🎯 **Purpose & User Problem**

**Problem**: Users need a complete end-to-end experience where they can:
1. Select their calibration profile (slow/medium) from a mobile app
2. Stream camera frames to the backend for real-time blink detection
3. See translation results automatically appear when a word is completed
4. Have a smooth, responsive experience with proper error handling

**Current State**: Week 5 delivered a robust Python backend with calibration profiles and API endpoints, but no mobile app integration.

**Goal**: Create a SwiftUI app that seamlessly integrates with the existing backend to provide a complete BlinkTalk experience.

---

## ✅ **Success Criteria**

### **Primary Success Criteria**
- [ ] **End-to-end demo**: Pick profile → blink (or simulate) → see word
- [ ] **Profile switching**: CalibrationView can select and apply slow/medium profiles
- [ ] **Real-time streaming**: CameraView streams frames at 5-10 FPS with backpressure
- [ ] **Auto-translation**: App polls `/api/translation` and shows results automatically
- [ ] **Error resilience**: Network errors, timeouts, and edge cases handled gracefully

### **Technical Success Criteria**
- [ ] Swift networking layer with proper timeout handling
- [ ] JSON request/response handling for all API endpoints
- [ ] Frame streaming with backpressure (skip if request in flight)
- [ ] 2-second polling interval with 10-second overall timeout
- [ ] Retry banner with cancel option for failed operations
- [ ] Auto-navigation to ResultView on successful translation

---

## 🏗️ **Scope & Architecture**

### **In Scope**

#### **Swift App Structure**
```
sw/
├── App/
│   ├── BlinkTalkApp.swift          # Main app entry point
│   └── ContentView.swift           # Root navigation
├── Views/
│   ├── HomeView.swift              # Landing screen
│   ├── CalibrationView.swift       # Profile selection
│   ├── CameraView.swift            # Frame streaming + polling
│   └── ResultView.swift            # Translation display
└── Services/
    ├── NetworkService.swift        # API client
    ├── CameraService.swift         # Frame capture
    └── TranslationService.swift    # Polling logic
```

#### **API Integration**
- `POST /api/calibration/set` - Profile switching
- `POST /api/frame` - Frame streaming
- `GET /api/translation` - Result polling
- `GET /api/health` - Connection health check

#### **User Flow**
1. **HomeView** → Start button → CalibrationView
2. **CalibrationView** → Select profile → CameraView
3. **CameraView** → Stream frames + poll translation → ResultView
4. **ResultView** → Show word → Back to HomeView

### **Out of Scope**
- Advanced camera controls (focus, zoom, etc.)
- Offline mode or local storage
- User authentication or profiles
- Advanced error recovery beyond retry/cancel
- Custom calibration tuning (save/load profiles)

---

## 🔧 **Technical Considerations**

### **Swift Networking Architecture**

#### **NetworkService.swift**
```swift
class NetworkService: ObservableObject {
    private let baseURL = "http://localhost:8011"
    private let session: URLSession
    
    // Timeout configuration
    private let requestTimeout: TimeInterval = 10.0
    private let pollingInterval: TimeInterval = 2.0
    private let overallTimeout: TimeInterval = 10.0
}
```

#### **Key Features**
- **Base URL Configuration**: Easy environment switching
- **Timeout Handling**: Request timeout + overall operation timeout
- **JSON Encoding/Decoding**: Codable models for all API calls
- **Error Handling**: Network errors, HTTP status codes, parsing errors
- **Retry Logic**: Exponential backoff for failed requests

### **Camera Integration**

#### **CameraService.swift**
```swift
class CameraService: NSObject, ObservableObject {
    private let captureSession = AVCaptureSession()
    private let videoOutput = AVCaptureVideoDataOutput()
    
    // Frame streaming configuration
    private let targetFPS: Double = 8.0
    private let maxConcurrentRequests = 1
    private var isRequestInFlight = false
}
```

#### **Key Features**
- **Frame Rate Control**: 5-10 FPS with backpressure
- **Backpressure Handling**: Skip frames if request in flight
- **Base64 Encoding**: Convert frames to API format
- **Error Handling**: Camera permissions, capture errors

### **Translation Polling**

#### **TranslationService.swift**
```swift
class TranslationService: ObservableObject {
    @Published var currentWord: String = ""
    @Published var isPolling: Bool = false
    @Published var showRetryBanner: Bool = false
    
    private var pollingTimer: Timer?
    private var overallTimeoutTimer: Timer?
}
```

#### **Key Features**
- **2-Second Polling**: Regular `/api/translation` requests
- **10-Second Timeout**: Overall operation timeout
- **Auto-Navigation**: Navigate to ResultView on non-empty response
- **Retry Banner**: Show retry option with cancel

---

## 🎨 **UI/UX Design**

### **CalibrationView**
- **Profile Selection**: Toggle between "Slow" and "Medium" profiles
- **Visual Feedback**: Show selected profile with checkmark
- **API Integration**: POST to `/api/calibration/set` on selection
- **Error Handling**: Show alert if profile switch fails

### **CameraView**
- **Camera Preview**: Full-screen camera feed
- **Status Indicators**: Show "Streaming", "Processing", "Polling" states
- **Progress Bar**: Visual countdown for 10-second timeout
- **Retry Banner**: Slide-up banner with retry/cancel options

### **ResultView**
- **Word Display**: Large, clear text showing translated word
- **Action Buttons**: "Try Again" and "New Profile" options
- **Success Animation**: Subtle animation when word appears

---

## 🧪 **Testing Strategy**

### **Unit Tests**
- **NetworkService**: Mock API responses, timeout handling
- **CameraService**: Frame capture, encoding, backpressure
- **TranslationService**: Polling logic, timeout handling

### **Integration Tests**
- **API Integration**: Real API calls with test backend
- **Camera Integration**: Frame streaming with mock data
- **End-to-End**: Complete user flow with simulated blinks

### **Manual Testing**
- **Profile Switching**: Verify API calls and UI updates
- **Frame Streaming**: Check frame rate and backpressure
- **Translation Polling**: Verify 2-second intervals and timeout
- **Error Scenarios**: Network failures, camera errors, timeouts

---

## 📋 **Implementation Plan**

### **Phase 1: Foundation (Day 1)**
1. Create Swift project structure
2. Implement NetworkService with basic API calls
3. Create Codable models for API requests/responses
4. Add basic error handling

### **Phase 2: Camera Integration (Day 2)**
1. Implement CameraService with AVCaptureSession
2. Add frame streaming with backpressure
3. Integrate with NetworkService for frame uploads
4. Test frame rate and performance

### **Phase 3: Translation Polling (Day 3)**
1. Implement TranslationService with polling logic
2. Add timeout handling and retry mechanisms
3. Create auto-navigation logic
4. Test polling intervals and timeouts

### **Phase 4: UI/UX Polish (Day 4)**
1. Implement all four main views
2. Add status indicators and progress feedback
3. Implement error handling and retry banners
4. Test complete user flow

### **Phase 5: Integration & Testing (Day 5)**
1. End-to-end testing with real backend
2. Performance optimization
3. Error scenario testing
4. Demo preparation

---

## 🚀 **Demo Script**

### **Setup (1 minute)**
1. Start Python backend: `python -m uvicorn api.main:app --host 0.0.0.0 --port 8011`
2. Launch Swift app on simulator/device
3. Verify connection with health check

### **Profile Selection (1 minute)**
1. Navigate to CalibrationView
2. Show "Slow" and "Medium" profile options
3. Select "Medium" profile
4. Verify API call success

### **Camera Streaming (2 minutes)**
1. Navigate to CameraView
2. Show camera preview and streaming status
3. Demonstrate frame streaming at 5-10 FPS
4. Show backpressure handling (skip frames if busy)

### **Translation Demo (2 minutes)**
1. Simulate blink pattern or use real camera
2. Show polling every 2 seconds
3. Demonstrate 10-second timeout with retry banner
4. Show auto-navigation to ResultView with translated word

### **Error Handling (1 minute)**
1. Disconnect network to show error handling
2. Show retry banner with cancel option
3. Reconnect and demonstrate recovery

---

## ⚠️ **Risks & Mitigations**

### **Risk: Network Latency**
- **Mitigation**: Implement proper timeouts and retry logic
- **Fallback**: Show clear error messages with retry options

### **Risk: Camera Performance**
- **Mitigation**: Implement backpressure and frame rate limiting
- **Fallback**: Graceful degradation with error messages

### **Risk: API Integration Issues**
- **Mitigation**: Comprehensive error handling and logging
- **Fallback**: Mock responses for demo purposes

### **Risk: Polling Performance**
- **Mitigation**: Efficient polling with proper cleanup
- **Fallback**: Manual refresh option

---

## 📊 **Success Metrics**

### **Performance Metrics**
- Frame streaming: 5-10 FPS sustained
- API response time: < 500ms average
- Polling accuracy: 2-second intervals ± 100ms
- Overall timeout: 10 seconds ± 1 second

### **User Experience Metrics**
- Profile switching: < 2 seconds
- Translation display: < 3 seconds after word completion
- Error recovery: < 5 seconds
- App responsiveness: No UI blocking

### **Reliability Metrics**
- Network error handling: 100% of error cases covered
- Camera error handling: 100% of error cases covered
- Timeout handling: 100% of timeout scenarios covered
- End-to-end success rate: > 90% in demo conditions

---

## 🔄 **Next Steps**

After Week 6 completion:
- **Week 7**: Vocabulary UI & resilience improvements
- **Week 8**: Calibration save/load & tuning
- **Week 9**: Polish & delivery

---

**Spec Status**: ✅ Ready for Implementation
**Estimated Effort**: 5 days
**Dependencies**: Week 5 calibration system (completed)
**Deliverable**: Complete Swift app with end-to-end demo capability

