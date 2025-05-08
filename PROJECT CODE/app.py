
import streamlit as st
import speech_recognition as sr
import joblib
from googletrans import Translator
import pandas as pd
import altair as alt
from datetime import datetime
import csv
import os
import smtplib
from email.message import EmailMessage
import streamlit.components.v1 as components
from streamlit_js_eval import streamlit_js_eval


# Email alert function
def send_email_alert(to_email, subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = "sakthims2809@gmail.com"
    msg['To'] = to_email
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login("sakthims2809@gmail.com", "ngsx vpsm ztxi sdcg")
            smtp.send_message(msg)
    except Exception as e:
        st.warning(f"Email simulation failed: {e}")

# Load model and vectorizer
model = joblib.load("emergency_priority_model.joblib")
vectorizer = joblib.load("vectorizer.joblib")

# Classify emergency type
def classify_emergency_type(text):
    text = text.lower()
    if any(word in text for word in ['fire', 'burn', 'smoke', 'gas']):
        return 'Fire'
    elif any(word in text for word in ['gun', 'shot', 'stab', 'rob', 'fight']):
        return 'Crime'
    elif any(word in text for word in ['collapse', 'unconscious', 'injury', 'bleeding', 'ambulance']):
        return 'Medical'
    else:
        return 'Other'

# Translate input to English
def translate_to_english(text):
    translator = Translator()
    try:
        translated = translator.translate(text, dest='en')
        return translated.text
    except Exception as e:
        return f"[Translation failed: {e}]"

# Icon helper
def get_icon(em_type):
    icon_map = {
        'Fire': '🔥',
        'Crime': '🚓',
        'Medical': '🏥',
        'Other': 'ℹ️'
    }
    return icon_map.get(em_type, '')

# Logging function
def log_input(timestamp, original_msg, translated_msg, prediction, confidence, em_type):
    header = ['Timestamp', 'Original Message', 'Translated Message', 'Priority', 'Confidence (%)', 'Emergency Type']
    row = [timestamp, original_msg, translated_msg, prediction, f"{confidence:.2f}", em_type]
    try:
        with open("call_logs.csv", "a", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if f.tell() == 0:
                writer.writerow(header)
            writer.writerow(row)
    except Exception as e:
        st.error(f"⚠️ Failed to log entry: {e}")

# UI setup
st.set_page_config(page_title="Emergency Call Classifier", layout="centered")
st.title("🚨 Emergency Call Prioritization System")

# Browser-based geolocation


st.markdown("### 📍 Precise Location from Browser (if permission granted)")
coords_input = st.text_input("📍 Sender Coordinates (auto-filled)", key="gps_hidden")

components.html("""
<script>
navigator.geolocation.getCurrentPosition(
    function(position) {
        const coords = position.coords.latitude + "," + position.coords.longitude;

        // Show map
        const iframe = document.createElement("iframe");
        iframe.src = "https://maps.google.com/maps?q=" + coords + "&z=15&output=embed";
        iframe.width = "100%";
        iframe.height = "300";
        iframe.style.border = "0";
        document.body.appendChild(iframe);

        // Inject coordinates into Streamlit's hidden input
        const input = window.parent.document.querySelector('input[name="gps_hidden"]');
        if (input) {
            input.value = coords;
            const event = new Event('input', { bubbles: true });
            input.dispatchEvent(event);
        } else {
            console.warn("Hidden input not found");
        }
    },
    function(error) {
        document.body.innerHTML += "<p style='color:red;'>Could not retrieve location. Please allow location access.</p>";
    }
);
</script>
""", height=370)


# Input Section
user_input = st.text_area("✍️ Type the emergency situation (any language):")

if st.button("🎤 Use Voice Input"):
    try:
        r = sr.Recognizer()
        with sr.Microphone() as source:
            st.info("🎤 Listening... please speak clearly.")
            audio = r.listen(source, timeout=10, phrase_time_limit=8)
            text = r.recognize_google(audio)
            st.success(f"🗣️ You said: {text}")
            user_input = text
    except sr.UnknownValueError:
        st.error("❌ Could not understand what you said.")
    except sr.RequestError:
        st.error("🔌 Could not connect to the speech recognition service.")
    except Exception as e:
        st.error(f"⚠️ Microphone error: {e}")

# Classification Trigger
if st.button("Classify Priority"):
    if user_input.strip():
        translated_input = translate_to_english(user_input)
        st.write(f"🌐 Translated to English: {translated_input}")
        cleaned = translated_input.lower().strip()
        input_vec = vectorizer.transform([cleaned])
        prediction = model.predict(input_vec)[0]
        probs = model.predict_proba(input_vec)[0]
        confidence = max(probs) * 100
        emergency_type = classify_emergency_type(translated_input)

        if prediction == "High":
            st.markdown("🟥 **Priority: HIGH**", unsafe_allow_html=True)
            st.audio("alert.mp3")
        elif prediction == "Medium":
            st.markdown("🟧 **Priority: MEDIUM**", unsafe_allow_html=True)
        else:
            st.markdown("🟩 **Priority: LOW**", unsafe_allow_html=True)

        st.markdown(f"📦 Emergency Type: {get_icon(emergency_type)} **{emergency_type}**")
        st.write(f"⏰ Prediction Time: {datetime.now().strftime('%I:%M:%S %p')}")


        if emergency_type == "Fire":
            st.success("🚒 Routed to Fire Department")
           
            sender_coords = coords_input if coords_input else "Unavailable"

# Include Google Maps link if coordinates available
           # Clean Google Maps link only
            if sender_coords != "Unavailable" and "," in sender_coords:
             location_text = f"https://www.google.com/maps?q={sender_coords}"
            else:
             location_text = "Unavailable"


# Send email
            send_email_alert(
               to_email="sakthims2809@gmail.com",
               subject="🔥 High Priority Alert - Fire Department",
               body=f"Emergency Message: {translated_input}\nPriority: {prediction}\nSender Location: {location_text}")

        elif emergency_type == "Crime":
            st.success("🚓 Routed to Police Department")
            send_email_alert(
                to_email="sakthims2809@gmail.com",
                subject="🔥 High Priority Alert - Crime Department",
                body=f"Emergency Message: {translated_input}\nPriority: {prediction}\nSender Location: {sender_coords}"
            )
        elif emergency_type == "Medical":
            st.success("🏥 Routed to Nearest Hospital")
            send_email_alert(
                to_email="sakthims2809@gmail.com",
                subject="🔥 High Priority Alert - Medical Department",
                body=f"Emergency Message: {translated_input}\nPriority: {prediction}\nSender Location:{sender_coords}"
            )
        else:
            st.info("📨 Logged for General Support Team")
            send_email_alert(
                to_email="sakthims2809@gmail.com",
                subject="🔥 High Priority Alert - Other Department",
                 body=f"Emergency Message: {translated_input}\nPriority: {prediction}\nSender Location: {sender_coords}"
            )

        log_input(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            original_msg=user_input,
            translated_msg=translated_input,
            prediction=prediction,
            confidence=confidence,
            em_type=emergency_type
        )

        with st.expander("📊 Show Model Confidence Details"):
            st.markdown("*Confidence shows how certain the model is about each class.*")
            prob_df = pd.DataFrame({
                'Priority': model.classes_,
                'Confidence': probs * 100
            })
            bar_chart = alt.Chart(prob_df).mark_bar().encode(
                x='Priority',
                y='Confidence',
                color='Priority'
            ).properties(height=300)
            st.altair_chart(bar_chart, use_container_width=True)
    else:
        st.warning("Please enter or speak an emergency message first.")

# Emergency Log Viewer
st.markdown("## 📋 Real-Time Emergency Queue")
if os.path.exists("call_logs.csv"):
    try:
        df_logs = pd.read_csv("call_logs.csv")
        filter_priority = st.selectbox("🔎 Filter by Priority", ["All", "High", "Medium", "Low"])
        if filter_priority != "All":
            df_logs = df_logs[df_logs["Priority"] == filter_priority]
        st.markdown("## 🧭 Filter by Emergency Type (Department View)")
        dept_filter = st.selectbox("👨‍🚒 Select Department", ["All", "Fire", "Crime", "Medical", "Other"])
        if dept_filter != "All":
            df_logs = df_logs[df_logs["Emergency Type"] == dept_filter]
        df_logs = df_logs.sort_values("Timestamp", ascending=False)
        st.dataframe(df_logs)
    except Exception as e:
        st.error(f"Failed to load emergency log table: {e}")
else:
    st.info("No emergency logs yet.")
