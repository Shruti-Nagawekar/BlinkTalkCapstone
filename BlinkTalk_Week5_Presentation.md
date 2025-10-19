# BlinkTalk Week 5: Calibration Profiles & Overrides
## Capstone Project Presentation

---

## 🎯 **Project Overview**

**BlinkTalk** - A blink-based communication system that replaces Morse code with custom sequence-to-word mapping for assistive communication.

**Week 5 Focus**

 Implementing calibration profiles to accommodate different user capabilities and timing preferences.

### ✅ **Core Implementation**
- **Calibration Profiles**: Slow and medium profiles with different timing thresholds
- **Profile Switching**: `POST /api/calibration/set` endpoint for real-time switching
- **Dynamic Thresholds**: Blink detection adapts immediately to profile changes
- **API Integration**: Complete calibration management via RESTful endpoints
- **Thread Safety**: Multiple users can switch profiles safely


## 🏗️ **Architecture Overview**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Camera        │    │   Eye Tracker    │    │ BlinkClassifier │
│   Frames        │───▶│   (EAR Values)   │───▶│   (S/L Events)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Translation   │◀───│  SequenceEngine  │◀───│   Gap Detection │
│   API Response  │    │  (Pattern Match) │    │   (Word Gaps)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                ▲
                                │
                    ┌──────────────────┐
                    │ Calibration      │
                    │ Manager          │
                    │ (Dynamic         │
                    │  Thresholds)     │
                    └──────────────────┘
```

---

## 🔧 **Key Components Implemented**

### 1. **Calibration Manager** (`py/core/calibration.py`)

```python
class CalibrationManager:
    def set_profile(self, profile_name: str) -> bool
    def get_active_profile(self) -> str
    def get_thresholds(self) -> Dict[str, int]
    def get_profile_info(self, profile_name: str) -> Dict[str, Any]
```

**Features:**
- ✅ Thread-safe profile switching
- ✅ Real-time threshold updates
- ✅ Profile validation and error handling
- ✅ Singleton pattern for global access

### 2. **Calibration API** (`py/api/routers/calibration.py`)

**Endpoints:**
- `POST /api/calibration/set` - Switch active profile
- `GET /api/calibration/active` - Get current profile info
- `GET /api/calibration/thresholds` - Get current threshold values
- `GET /api/calibration/info` - Get comprehensive calibration info
- `POST /api/calibration/reset` - Reset to default profile

---

## 🧪 **Testing & Quality Assurance**

### **Test Coverage**
- **20 Unit Tests** for Calibration Manager
- **14 Integration Tests** for API endpoints
- **34 Total Tests** - All Passing ✅

### **Test Categories**
1. **Profile Management** - Switching, validation, error handling
2. **Thread Safety** - Concurrent profile switching
3. **API Integration** - All endpoints and error cases
4. **Blink Detection** - Threshold changes affect classification
5. **Gap Detection** - Different profiles affect gap timing

### **Testing Strategy: Proving Profile Switching**

```python

# Profile Switching: API round-trip validation
def test_profile_switching(self):
    response = client.post("/api/calibration/set", json={"profile": "slow"})
    assert response.json()["thresholds"]["short_max_ms"] == 500


---

### **Threshold Comparison** makesure you can back the diff up in someone
```
┌─────────────────────┬─────────┬─────────┬─────────┐
│ Threshold           │ Slow    │ Medium  │ Diff    │
├─────────────────────┼─────────┼─────────┼─────────┤
│ short_max_ms        │     500 │     350 │    +150 │
│ long_max_ms         │    1200 │     900 │    +300 │
│ symbol_gap_max_ms   │     600 │     450 │    +150 │
│ word_gap_min_ms     │    1500 │    1100 │    +400 │
└─────────────────────┴─────────┴─────────┴─────────┘
```

### **Calibration Manager Architecture** use this to talk about theading keep it the focus
```python
class CalibrationManager:
    def __init__(self, default_profile: str = "medium"):
        self._lock = threading.RLock()  # Thread safety
        self._active_profile = default_profile
        self._current_thresholds = self._get_profile_thresholds(default_profile)
    
    def set_profile(self, profile_name: str) -> bool:
        with self._lock:  # Atomic operation
            if profile_name not in self.CALIBRATION_PROFILES:
                return False
            self._active_profile = profile_name
            self._current_thresholds = self._get_profile_thresholds(profile_name)
            return True
```

---

## 🔮 **Next Steps (Week 6)**

### **Swift Networking & UX**
- Swift app integration with calibration API
- Profile selection UI
- Real-time profile switching from mobile app

---

## 📞 **Questions & Discussion**

Thank you for your attention!

**Questions?**
