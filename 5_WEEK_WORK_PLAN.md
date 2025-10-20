# BlinkTalk 5-Week Work Plan
## Team Division: Swift Developer + Python Developer

This document outlines the work plan for the next 5 weeks, dividing tasks between the Swift frontend developer and Python backend developer. After individual work is completed, both developers will work together to integrate the pieces.

## Current Project Status

### ✅ **Python Backend - COMPLETED**
- FastAPI application with all core routers
- Calibration system with slow/medium profiles
- Frame buffer and processing pipeline
- Blink detection and classification
- Sequence engine with fuzzy matching
- Translation API endpoints
- Comprehensive test suite
- Health monitoring

### 🟡 **Swift Frontend - PARTIALLY IMPLEMENTED**

#### ✅ **Completed Swift Components:**
- SwiftUI app structure with navigation flow
- Camera integration with AVFoundation
- Object detection with Vision framework
- Core Data integration for user profiles
- Basic UI with server URL configuration
- Camera preview with frame rate display
- IntroView, HomeView, ContentView implemented

#### ❌ **Missing Critical Components:**
- No networking layer (APIClient, Services)
- No API models matching Python backend
- No calibration API integration
- No frame streaming to backend
- No translation polling system
- No result display view

---

## 🚨 **IMMEDIATE NEXT STEPS** (Current Priority)

Based on the current project status, here's what needs to be done **right now**:

### **Critical Missing Components:**
1. **Networking Layer** - Create `sw/Services/APIClient.swift` and related files
2. **API Models** - Create Swift structs matching Python API endpoints
3. **Calibration Integration** - Connect Swift app to Python calibration API
4. **Frame Streaming** - Send camera frames to Python backend
5. **Translation Polling** - Implement translation result polling
6. **Result Display** - Create view to show translation results

### **Recommended Starting Point:**
Start with **Week 1 tasks** - focus on creating the networking layer and API integration, as this is the foundation for everything else.

---

## 📱 **DEVICE SPECIFICATIONS & USER EXPERIENCE**

### **Target Device: iPhone 15 Only**
- Optimize all development for iPhone 15 specifications
- Test exclusively on iPhone 15 hardware
- Utilize iPhone 15 specific camera capabilities

### **User Experience Requirements:**
- **No Camera View**: Remove live camera preview to avoid disorientation
- **Black Screen Interface**: Display sequence on black background
- **Calibration Test Flow**: Interactive calibration with visual feedback
- **Profile Management**: Save user profiles with custom settings

---

## 🧪 **DETAILED CALIBRATION TEST FLOW**

### **Interactive Calibration Process:**

1. **Test Initiation**
   - White screen flash (2 seconds) to indicate test start
   - Clear instruction: "Calibration Test Starting"
   - Countdown: "3... 2... 1... Begin"

2. **Slow Blink Test**
   - Instruction: "Blink slowly when you see the cue"
   - Visual cue: Brief white flash
   - Record blink duration and intensity
   - Repeat 3 times for accuracy
   - Calculate average slow blink values

3. **Fast Blink Test**
   - Instruction: "Blink quickly when you see the cue"
   - Visual cue: Brief white flash
   - Record blink duration and intensity
   - Repeat 3 times for accuracy
   - Calculate average fast blink values

4. **Results Display & Recommendation**
   - Show measured values to user
   - Display recommendation: "Based on your results, we recommend [Slow/Medium] profile"
   - Show reasoning: "Your slow blinks average Xms, fast blinks average Yms"

5. **User Choice**
   - **Accept Recommendation**: Proceed with recommended profile
   - **Choose Custom**: Show custom input fields with measured values as reference

6. **Custom Input (if chosen)**
   - Display measured values as reference
   - Input fields for custom thresholds
   - Validation for reasonable ranges
   - Preview of custom settings

7. **Profile Saving**
   - Name input field
   - Save profile with all settings
   - Confirmation: "Profile saved successfully"

8. **Profile Selection**
   - List of saved profiles
   - One-click selection for future use
   - Quick setup for returning users

---

## Week 1: Foundation & Custom Calibration

### 🐍 **Python Developer Tasks**
**Goal**: Add custom calibration support to existing backend

#### Tasks:
1. **Extend CalibrationManager** (`py/core/calibration.py`)
   - Add support for "custom" profile type
   - Add method to set custom thresholds dynamically
   - Add validation for custom threshold ranges
   - Update `get_calibration_manager()` to handle custom profiles

2. **Add Custom Calibration API** (`py/api/routers/calibration.py`)
   - Add `POST /api/calibration/custom` endpoint
   - Create `CustomCalibrationRequest` model
   - Add validation for threshold values (reasonable ranges)
   - Update existing endpoints to handle custom profile

3. **Update Tests** (`py/tests/`)
   - Add tests for custom calibration functionality
   - Test threshold validation
   - Test custom profile switching
   - Update existing calibration tests

#### Deliverables:
- Custom calibration API working
- All tests passing
- Documentation for new endpoints

#### Acceptance Criteria:
- `POST /api/calibration/custom` accepts custom threshold values
- Custom profile can be set and retrieved
- Threshold validation prevents invalid values
- All existing functionality still works

### 🍎 **Swift Developer Tasks**
**Goal**: Create networking layer and API integration

#### ✅ **COMPLETED:**
- SwiftUI app structure with navigation flow
- Camera integration with AVFoundation
- Basic UI layouts and navigation
- Core Data integration for user profiles

#### 🚧 **CURRENT TASKS:**
1. **Create Networking Layer** (`sw/Services/`)
   ```
   sw/Services/
   ├── APIClient.swift              # Base networking client
   ├── Models/
   │   ├── CalibrationModels.swift  # Request/response models
   │   ├── TranslationModels.swift  # Translation models
   │   └── VocabularyModels.swift   # Vocabulary models
   └── Endpoints/
       ├── CalibrationEndpoint.swift
       ├── TranslationEndpoint.swift
       └── VocabularyEndpoint.swift
   ```

2. **Implement API Models**
   - Create Swift structs matching Python API
   - Add JSON encoding/decoding
   - Handle error responses

3. **Create Interactive CalibrationView**
   - **Calibration Test Flow**:
     - White screen flash to indicate test start
     - "Blink slowly" instruction with visual cue
     - Record slow blink values
     - "Blink quickly" instruction with visual cue  
     - Record fast blink values
     - Display measured values to user
     - Recommend slow/medium profile based on results
     - Allow user to accept recommendation or choose custom
   - **Custom Input Flow**:
     - If user denies recommendation, show custom input fields
     - Display their measured values as reference
     - Allow manual threshold input with validation
   - **Profile Management**:
     - Name input field for saving profile
     - Save profile with all settings
     - Profile selection for future use

#### Deliverables:
- Complete networking layer
- API models and endpoints
- CalibrationView with backend integration
- Error handling and loading states

#### Acceptance Criteria:
- Can make API calls to Python backend
- CalibrationView successfully sets profiles
- Error handling works properly
- Loading states show during API calls

---

## Week 2: Frame Streaming & Camera Integration

### 🐍 **Python Developer Tasks**
**Goal**: Enhance backend for better Swift integration

#### Tasks:
1. **Add Vocabulary API** (`py/api/routers/`)
   - Create `vocabulary.py` router
   - Add `GET /api/vocabulary` endpoint
   - Return vocabulary list from sequences_v1.json
   - Add vocabulary validation

2. **Enhance Error Handling**
   - Standardize error responses
   - Add request ID tracking
   - Improve logging for debugging

3. **Add CORS Configuration**
   - Configure CORS for Swift app
   - Add proper headers for camera streaming

#### Deliverables:
- Vocabulary API endpoint
- Enhanced error handling
- CORS configuration
- Updated API documentation

### 🍎 **Swift Developer Tasks**
**Goal**: Implement frame streaming and camera integration

#### ✅ **COMPLETED:**
- Basic networking layer (if completed in Week 1)
- API models and endpoints
- CalibrationView with backend integration

#### 🚧 **CURRENT TASKS:**
1. **Create Black Screen Interface** (`sw/Views/BlinkDetectionView.swift`)
   - Remove camera preview (background processing only)
   - Black screen with sequence display
   - Show detected sequence in real-time
   - iPhone 15 optimized camera integration

2. **Implement Background Frame Streaming**
   - Camera runs in background (no preview)
   - Frame streaming to Python backend
   - Base64 encoding for API transmission
   - Frame rate control (5-10 FPS)
   - iPhone 15 specific optimizations

3. **Add Camera Permissions & Error Handling**
   - Request camera permissions
   - Handle permission denials
   - Show appropriate error messages
   - Background camera operation

#### Deliverables:
- Black screen interface with sequence display
- Background camera processing (no preview)
- Frame streaming to Python backend
- iPhone 15 optimized performance
- Permission handling and error states

#### Acceptance Criteria:
- Black screen shows detected sequence in real-time
- Camera operates in background without preview
- Frames are captured and sent to backend
- Handles camera permission requests
- Error handling for camera failures
- iPhone 15 specific optimizations working

---

## Week 3: Translation Integration & Real-time Processing

### 🐍 **Python Developer Tasks**
**Goal**: Ensure translation pipeline works with Swift integration

#### Tasks:
1. **Test Translation Pipeline**
   - End-to-end testing with Swift frames
   - Performance optimization
   - Debug any integration issues

2. **Add Translation Statistics**
   - Track translation success rates
   - Log translation timing
   - Monitor system performance

3. **Prepare for Integration**
   - Ensure all APIs work with Swift
   - Test with real camera frames
   - Optimize for production use

#### Deliverables:
- Tested translation pipeline
- Performance optimizations
- Integration-ready backend

### 🍎 **Swift Developer Tasks**
**Goal**: Implement translation polling and result display

#### ✅ **COMPLETED:**
- Camera integration with frame streaming
- Frame processing and backend communication

#### 🚧 **CURRENT TASKS:**
1. **Implement Translation Polling**
   - Poll `/api/translation` every 2 seconds
   - 10-second overall timeout
   - Handle empty responses
   - Background polling with proper lifecycle

2. **Create ResultView**
   - Display translated word
   - Handle empty results
   - Navigation back to camera
   - Success/error states

3. **Add Translation Feedback**
   - Show polling status
   - Display translation progress
   - Handle timeout scenarios
   - Retry mechanisms

#### Deliverables:
- Translation polling system
- ResultView with proper display
- Feedback and status indicators
- Timeout and retry handling

#### Acceptance Criteria:
- Polls translation API correctly
- Shows results when available
- Handles timeouts gracefully
- Provides user feedback during polling

---

## Week 4: Integration & Polish

### 🤝 **Both Developers - Integration Tasks**
**Goal**: Integrate Swift and Python components

#### Tasks:
1. **End-to-End Testing**
   - Test complete user flow
   - Calibration → Camera → Translation
   - Debug integration issues
   - Performance testing

2. **Error Handling**
   - Consistent error messages
   - Network error recovery
   - Camera error handling
   - Translation error states

3. **User Experience**
   - Smooth navigation flow
   - Loading states and feedback
   - Error recovery mechanisms
   - Performance optimization

#### Deliverables:
- Fully integrated application
- End-to-end testing completed
- Error handling implemented
- User experience polished

---

## Week 5: Production Readiness & Deployment

### 🤝 **Both Developers - Final Integration**
**Goal**: Production-ready application

#### Tasks:
1. **Final Integration Testing**
   - Complete end-to-end testing
   - Performance optimization
   - Bug fixes and polish
   - User acceptance testing

2. **Production Configuration**
   - Environment setup
   - Security hardening
   - Performance monitoring
   - Error tracking

#### Deliverables:
- Production-ready application
- Complete testing suite
- Deployment configuration
- Documentation

### 🐍 **Python Developer - Final Tasks**
**Goal**: Production backend deployment

#### Tasks:
1. **Production Configuration**
   - Environment configuration
   - Logging setup
   - Performance monitoring
   - Security considerations

2. **Documentation**
   - API documentation
   - Deployment instructions
   - Troubleshooting guide

#### Deliverables:
- Production-ready backend
- Complete documentation
- Deployment configuration

### 🍎 **Swift Developer - Final Tasks**
**Goal**: App store readiness

#### Tasks:
1. **App Polish**
   - UI/UX improvements
   - Accessibility features
   - Performance optimization
   - Error message improvements

2. **App Configuration**
   - App icons and metadata
   - Build configuration
   - Testing on devices

#### Deliverables:
- Polished SwiftUI app
- App store ready
- Device testing completed

#### Acceptance Criteria:
- Complete end-to-end functionality
- Smooth user experience
- Proper error handling
- Production ready

---

## Integration Points

### API Contracts
- **Calibration**: `POST /api/calibration/set`, `POST /api/calibration/custom`
- **Frames**: `POST /api/frame`
- **Translation**: `GET /api/translation`
- **Vocabulary**: `GET /api/vocabulary`
- **Health**: `GET /api/health`

### Data Flow
1. User selects calibration profile (Swift → Python)
2. Camera captures frames (Swift)
3. Frames sent to backend (Swift → Python)
4. Backend processes frames and detects blinks (Python)
5. Translation polling (Swift → Python)
6. Results displayed (Python → Swift)

### Testing Strategy
- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **End-to-End Tests**: Complete user flow testing
- **Performance Tests**: Frame processing and translation speed

---

## Success Metrics

### Technical Metrics
- Frame processing: < 100ms per frame
- Translation response: < 2 seconds
- API response times: < 500ms
- App startup: < 3 seconds

### User Experience Metrics
- Successful calibration rate: > 90%
- Translation accuracy: > 80%
- User satisfaction with custom calibration
- Smooth navigation flow

### Integration Metrics
- Zero critical bugs in integration
- All API endpoints working
- Complete user flow functional
- Production ready deployment

---

## Risk Mitigation

### Technical Risks
- **Camera performance**: Test on multiple devices
- **Network latency**: Implement proper timeouts
- **Translation accuracy**: Extensive testing with real users
- **Custom calibration**: Thorough validation and testing

### Timeline Risks
- **Swift development**: Start with basic UI, iterate
- **Integration complexity**: Regular integration testing
- **Testing time**: Parallel testing during development
- **Polish time**: Focus on core functionality first

### Communication Risks
- **API changes**: Document all changes immediately
- **Integration issues**: Daily communication during Week 5
- **Testing coordination**: Shared testing environment
- **Deployment**: Coordinate deployment procedures

---

## Next Steps After Week 5

1. **User Testing**: Test with real users and gather feedback
2. **Performance Optimization**: Based on real-world usage
3. **Feature Enhancements**: Additional vocabulary, improved accuracy
4. **Production Deployment**: Deploy to production environment
5. **Documentation**: User guides and troubleshooting documentation
