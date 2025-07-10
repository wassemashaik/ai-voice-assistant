# 🧪 Quick Testing Guide - Voice Assistant Fixes

## ✅ **Pre-Test Setup**

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the App:**
   ```bash
   streamlit run voice_assistant/voice_assistant.py
   ```

3. **Enable Debug Panel:**
   - Check the "🔧 Debug Info" checkbox at the bottom
   - This will help monitor what's happening

## 🎯 **Testing Steps**

### **Test 1: Check Session State Initialization**
- ✅ App should load without any AttributeError
- ✅ Debug panel should show all session state variables
- ✅ Recording State should show "stopped"

### **Test 2: Basic Recording Setup**
- ✅ Click WebRTC "START" button
- ✅ Browser should ask for microphone permission (allow it)
- ✅ Debug panel should show "WebRTC State: True"
- ✅ Status should change to "🎤 Recording in progress... Speak now!"

### **Test 3: Audio Frame Capture**
- ✅ While recording, speak clearly for 3-5 seconds
- ✅ Debug panel should show increasing "Audio Frames Count"
- ✅ Status should show "📊 Listening for audio... (frames will appear here)"
- ✅ Console should print "Audio frames recorded: X" (check terminal)

### **Test 4: Automatic Processing**
- ✅ Click WebRTC "STOP" button
- ✅ Status should automatically change to "🔄 Recording stopped. Processing audio..."
- ✅ Then "🔄 Processing your recording..."
- ✅ Finally "✅ Recording processed successfully!"

### **Test 5: Full Workflow**
- ✅ Transcript should appear in text area
- ✅ AI response should be generated
- ✅ Recording state should reset to "stopped"
- ✅ Audio buffer should be cleared (0 frames)

## 🔧 **Debugging Checklist**

If something doesn't work:

### **Check Browser Console (F12)**
Look for error messages like:
- WebRTC permission denied
- Audio device not found
- JavaScript errors

### **Check Terminal Output**
Look for debug messages:
```
Audio frames recorded: 100
Processing 150 audio frames...
Audio saved to: /tmp/tmpxxx.wav
Audio file size: 12345 bytes
Transcription result: Hello world
```

### **Check Debug Panel Values**
- **WebRTC State**: Should be `True` when recording, `False` when stopped
- **Audio Frames Count**: Should increase while recording
- **Recording State**: Should follow the state flow properly
- **Current Transcript**: Should show the transcribed text

### **Use Reset Features**
- Click "🗑️ Clear Audio Buffer" if things get stuck
- Refresh the page to completely reset
- Check microphone permissions in browser settings

## 🎉 **Success Indicators**

✅ **Working properly when:**
- No AttributeError on startup
- Audio frames increase during recording
- Automatic transcription after stopping
- AI response generated
- State resets for next recording

❌ **Still having issues if:**
- Audio frames stay at 0 during recording
- No automatic processing after stopping
- Session state errors in debug panel
- No transcription appears

## 📞 **If Issues Persist**

1. **Check Requirements:**
   - All packages from requirements.txt installed
   - streamlit-webrtc>=0.47.0 specifically

2. **Browser Compatibility:**
   - Chrome/Edge work best with WebRTC
   - Firefox may have issues
   - Try incognito/private mode

3. **System Issues:**
   - Check microphone is working in other apps
   - Try restarting browser
   - Clear browser cache/cookies

4. **Environment Issues:**
   - Try different virtual environment
   - Check Python version compatibility
   - Reinstall problematic packages

Good luck testing! 🚀