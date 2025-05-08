import speech_recognition as sr

r = sr.Recognizer()

with sr.Microphone() as source:
    print("🎤 Speak now (testing mic)...")
    audio = r.listen(source, timeout=10, phrase_time_limit=5)

try:
    text = r.recognize_google(audio)
    print("✅ You said:", text)
except sr.UnknownValueError:
    print("❌ Could not understand audio.")
except sr.RequestError as e:
    print(f"🔌 Could not request results; {e}")
except Exception as e:
    print(f"⚠️ Other error: {e}")
