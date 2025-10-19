# Week 5: Calibration Profiles & Overrides
## BlinkTalk Capstone Project Specification

---

## 🎯 **Purpose & User Problem**

**Problem**: Different users have different blink patterns and timing. A one-size-fits-all approach doesn't work for assistive communication systems.

**Solution**: Implement calibration profiles that allow dynamic adjustment of blink detection thresholds to accommodate different user capabilities and preferences.

**User Impact**: Users with slower or faster blink patterns can now use the system effectively by selecting an appropriate calibration profile.

---

## 📋 **Success Criteria**

### **Primary Goals**
- ✅ Implement "slow" and "medium" calibration profiles with different timing thresholds
- ✅ Add `POST /api/calibration/set` endpoint to switch active profile server-side
- ✅ Create calibration management system that updates thresholds in memory
- ✅ Ensure profile switching measurably changes classification behavior
- ✅ Maintain backward compatibility with existing Week 4 functionality

### **Secondary Goals**
- ✅ Add comprehensive unit tests for calibration profile switching
- ✅ Create integration tests for calibration API endpoints
- ✅ Add logging for calibration profile changes
- ✅ Prepare infrastructure for future save/load named calibrations (Week 8)

---

## 🏗️ **Scope & Constraints**

### **In Scope**
- **Calibration Profiles**: Slow and medium profiles with predefined thresholds
- **Profile Switching**: API endpoint to change active profile
- **Threshold Management**: Dynamic updates to blink detection parameters
- **Testing**: Unit and integration tests for calibration functionality
- **Logging**: Track profile changes and threshold updates

### **Out of Scope (Future Weeks)**
- **Save/Load Named Calibrations**: Deferred to Week 8
- **Custom Threshold Input**: Users can't set arbitrary values yet
- **Profile Persistence**: Profiles reset on server restart
- **Advanced Calibration UI**: Basic profile selection only

### **Technical Constraints**
- Must maintain existing Week 4 API compatibility
- Profile changes must be immediate (no restart required)
- Threshold updates must be thread-safe
- Must preserve existing test coverage (28/28 tests passing)

---

## 🔧 **Technical Implementation**

### **1. Calibration Profile Definitions**

```python
# py/core/calibration.py
CALIBRATION_PROFILES = {
    "slow": {
        "short_max_ms": 500,      # Increased from 350ms
        "long_min_ms": 501,       # Increased from 351ms
        "long_max_ms": 1200,      # Increased from 900ms
        "symbol_gap_max_ms": 600, # Increased from 450ms
        "word_gap_min_ms": 1500,  # Increased from 1100ms
        "description": "For users with slower blink patterns"
    },
    "medium": {
        "short_max_ms": 350,      # Default from sequences_v1.json
        "long_min_ms": 351,       # Default from sequences_v1.json
        "long_max_ms": 900,       # Default from sequences_v1.json
        "symbol_gap_max_ms": 450, # Default from sequences_v1.json
        "word_gap_min_ms": 1100,  # Default from sequences_v1.json
        "description": "Standard timing for typical users"
    }
}
```

### **2. Calibration Manager**

```python
# py/core/calibration.py
class CalibrationManager:
    def __init__(self):
        self.active_profile = "medium"  # Default profile
        self.thresholds = CALIBRATION_PROFILES["medium"].copy()
    
    def set_profile(self, profile_name: str) -> bool:
        """Switch to specified calibration profile."""
        
    def get_active_profile(self) -> str:
        """Get currently active profile name."""
        
    def get_thresholds(self) -> Dict[str, int]:
        """Get current threshold values."""
        
    def reset_to_default(self) -> None:
        """Reset to medium profile."""
```

### **3. API Endpoints**

```python
# py/api/routers/calibration.py
@router.post("/api/calibration/set")
async def set_calibration_profile(profile: CalibrationProfileRequest):
    """Set active calibration profile."""
    
@router.get("/api/calibration/active")
async def get_active_profile():
    """Get currently active calibration profile."""
    
@router.get("/api/calibration/thresholds")
async def get_current_thresholds():
    """Get current threshold values."""
```

### **4. Integration Points**

- **BlinkClassifier**: Use calibration manager for threshold values
- **SequenceEngine**: Access calibration for gap detection
- **Frame Processing**: Pass calibration context through pipeline
- **Logging**: Track profile changes and threshold updates

---

## 📊 **Calibration Profile Details**

### **Slow Profile** (For users with slower blink patterns)
- **Short Blink Max**: 500ms (vs 350ms default)
- **Long Blink Min**: 501ms (vs 351ms default)  
- **Long Blink Max**: 1200ms (vs 900ms default)
- **Symbol Gap Max**: 600ms (vs 450ms default)
- **Word Gap Min**: 1500ms (vs 1100ms default)

### **Medium Profile** (Standard timing)
- **Short Blink Max**: 350ms (default)
- **Long Blink Min**: 351ms (default)
- **Long Blink Max**: 900ms (default)
- **Symbol Gap Max**: 450ms (default)
- **Word Gap Min**: 1100ms (default)

---

## 🧪 **Testing Strategy**

### **Unit Tests** (py/tests/test_calibration.py)
- ✅ Profile switching functionality
- ✅ Threshold value updates
- ✅ Invalid profile handling
- ✅ Default profile behavior
- ✅ Thread safety of profile changes

### **Integration Tests** (py/tests/test_calibration_integration.py)
- ✅ API endpoint functionality
- ✅ Profile switching via API
- ✅ Threshold retrieval endpoints
- ✅ Error handling for invalid profiles
- ✅ Backward compatibility with existing tests

### **Test Coverage Goals**
- **New Tests**: 8-10 additional tests
- **Total Coverage**: Maintain 100% for new code
- **Existing Tests**: All 28 Week 4 tests must still pass

---

## 🔄 **API Workflow**

### **1. Set Calibration Profile**
```bash
POST /api/calibration/set
{
  "profile": "slow"
}
# Response: {"message": "Profile set to 'slow'", "thresholds": {...}}
```

### **2. Get Active Profile**
```bash
GET /api/calibration/active
# Response: {"profile": "slow", "description": "For users with slower blink patterns"}
```

### **3. Get Current Thresholds**
```bash
GET /api/calibration/thresholds
# Response: {"short_max_ms": 500, "long_min_ms": 501, ...}
```

### **4. Verify Profile Impact**
```bash
# Profile switching should affect blink classification
# Test with same EAR values but different profiles
# Should produce different S/L classifications
```

---

## 📈 **Performance Requirements**

### **Response Times**
- Profile switching: < 10ms
- Threshold retrieval: < 5ms
- API responses: < 50ms (consistent with Week 4)

### **Memory Usage**
- Calibration profiles: < 1KB total
- No significant memory overhead
- Thread-safe access patterns

### **Reliability**
- Profile changes must be atomic
- No race conditions during profile switching
- Graceful handling of invalid profile names

---

## 🚀 **Implementation Plan**

### **Phase 1: Core Calibration System**
1. Create `CalibrationManager` class
2. Define profile configurations
3. Implement profile switching logic
4. Add thread safety mechanisms

### **Phase 2: API Integration**
1. Create calibration router
2. Implement API endpoints
3. Add request/response models
4. Integrate with existing API structure

### **Phase 3: System Integration**
1. Update `BlinkClassifier` to use calibration
2. Modify `SequenceEngine` for gap detection
3. Update frame processing pipeline
4. Add calibration context passing

### **Phase 4: Testing & Validation**
1. Write unit tests for calibration manager
2. Create integration tests for API
3. Verify existing tests still pass
4. Test profile switching impact on classification

---

## 🔍 **Acceptance Criteria**

### **Functional Requirements**
- ✅ Switching to "slow" profile increases all timing thresholds
- ✅ Switching to "medium" profile uses default thresholds
- ✅ Profile changes take effect immediately
- ✅ Invalid profile names return appropriate errors
- ✅ API endpoints return correct profile information

### **Technical Requirements**
- ✅ All existing Week 4 tests continue to pass
- ✅ New calibration tests achieve 100% coverage
- ✅ Profile switching is thread-safe
- ✅ No breaking changes to existing API
- ✅ Logging tracks profile changes

### **Performance Requirements**
- ✅ Profile switching completes in < 10ms
- ✅ No performance degradation in blink detection
- ✅ Memory usage remains minimal
- ✅ API response times stay under 50ms

---

## 🔮 **Future Considerations (Week 8)**

### **Save/Load Named Calibrations**
- File I/O for calibration persistence
- Custom profile creation
- Profile management UI
- Calibration sharing between users

### **Advanced Features**
- Real-time threshold adjustment
- User-specific calibration profiles
- Calibration validation and testing
- Performance analytics per profile

---

## 📝 **Deliverables**

### **Code Files**
- `py/core/calibration.py` - Calibration manager and profiles
- `py/api/routers/calibration.py` - Calibration API endpoints
- `py/tests/test_calibration.py` - Unit tests
- `py/tests/test_calibration_integration.py` - Integration tests

### **Documentation**
- Updated API documentation
- Calibration profile descriptions
- Usage examples and demos
- Week 5 presentation materials

### **Testing**
- 8-10 new test cases
- 100% test coverage for new code
- All existing tests passing
- Performance benchmarks

---

## 🎯 **Success Metrics**

- ✅ **Functionality**: Both slow and medium profiles work correctly
- ✅ **API**: All calibration endpoints respond properly
- ✅ **Integration**: Profile changes affect blink classification
- ✅ **Testing**: 100% coverage for new calibration code
- ✅ **Compatibility**: All Week 4 functionality preserved
- ✅ **Performance**: No degradation in system performance

---

**Ready to implement Week 5: Calibration Profiles & Overrides! 🚀**
