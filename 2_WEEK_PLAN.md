# BlinkTalk 2-Week Implementation Plan

## Project Status

### ✅ **Completed**
- **Python Backend**: All APIs (calibration, frame processing, translation, health)
- **Swift Frontend**: Networking layer, camera integration, frame streaming, translation polling, result display

### ❌ **Missing**
- CalibrationView for profile selection
- Profile-calibration integration
- End-to-end testing

---

## Device & Design Specifications

### Target Device
- **iPhone 15 only** - Front camera exclusively
- Optimize for iPhone 15 hardware specifications
- No multi-device testing required

### Color Scheme
- **Black and white only** - No color accents
- Black backgrounds, white text
- Monochrome UI throughout

---

## User Flow

1. **App Launch** → IntroView (if first launch)
2. **HomeView** → Create/select user profile
3. **CalibrationView** → Select calibration profile (slow/medium)
4. **BlinkDetectionView** → Black screen, background camera processing
   - Real-time sequence display (white text on black)
   - Automatic translation when word completes
5. **ResultView** → Display translated word (white text on black)
6. **Return** → Back to BlinkDetectionView for next word

---

## Week 1: Calibration & Profile Integration

### Python Developer
- Verify calibration API endpoints work correctly
- Ensure CORS configured for Swift app
- Test frame processing with iPhone 15 front camera frames

### Swift Developer
- **CalibrationView**: Profile selection UI (slow/medium buttons, current profile display)
- **Profile Integration**: Save/load calibration settings with user profiles
- **Navigation**: Connect CalibrationView to HomeView and BlinkDetectionView
- **Error Handling**: API errors, network failures, loading states

**Key Files:**
- `sw/Camera_View/CalibrationView.swift` (new)
- Update `sw/Camera_View/HomeView.swift` for calibration integration
- Update Core Data model if needed for calibration storage

---

## Week 2: Integration & Testing

### Both Developers
- **End-to-End Testing**: Complete flow from profile selection → calibration → blink detection → translation
- **Bug Fixes**: Address integration issues, edge cases
- **Performance**: Optimize frame processing, reduce latency
- **Error Recovery**: Network disconnections, camera failures, API timeouts

### Swift Developer
- **UI Polish**: Ensure black/white theme consistency
- **Camera Optimization**: iPhone 15 front camera specific tuning
- **User Feedback**: Loading indicators, error messages, status updates

### Python Developer
- **API Stability**: Handle edge cases, improve error responses
- **Performance**: Frame processing optimization
- **Logging**: Debug information for troubleshooting

---

## Technical Requirements

### API Endpoints
- `POST /api/calibration/set` - Set profile (slow/medium)
- `POST /api/frame` - Send camera frames
- `GET /api/translation` - Poll for translation results
- `GET /api/health` - Health check

### Camera Specifications
- **Device**: iPhone 15 front camera only
- **Frame Rate**: 5-10 FPS
- **Processing**: Background only (no preview)
- **Format**: Base64 encoded JPEG

### Performance Targets
- Frame processing: < 100ms
- Translation response: < 2 seconds
- API response: < 500ms

---

## Risk Mitigation

- **Network latency**: Implement proper timeouts and retry logic
- **Translation accuracy**: Test with real blink sequences
- **Integration complexity**: Daily testing of complete flow
- **Timeline**: Focus on core functionality first, polish second

---

## Success Criteria

- User can create profile and select calibration (slow/medium)
- Camera captures frames in background without preview
- Blink sequences detected and displayed in real-time
- Translations appear within 2 seconds of word completion
- Complete flow works end-to-end on iPhone 15
- Black and white UI consistent throughout

