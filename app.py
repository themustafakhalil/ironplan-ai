import os
import re
from datetime import date

import streamlit as st
from google import genai
from google.genai import errors as genai_errors

APP_NAME = "IRONPLAN AI"
MODEL_NAME = "gemini-3.4-flash"

st.set_page_config(
    page_title="IRONPLAN AI | Workout Planner",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------- Styling ----------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root { --lime: #b7f34a; --panel: #171a1d; --line: #2b3035; --muted: #a6adb5; }
    .stApp { background: #0e1012; color: #f5f7f8; font-family: 'DM Sans', sans-serif; }
    .block-container { max-width: 1180px; padding-top: 1.8rem; padding-bottom: 3rem; }
    h1, h2, h3 { font-family: 'Space Grotesk', sans-serif !important; letter-spacing: -0.035em; }
    h1 { font-size: clamp(2rem, 4vw, 3.15rem) !important; line-height: 1.08 !important; }
    h2 { margin-top: 1.5rem !important; }
    p, li { line-height: 1.65; }
    .brand { display:flex; align-items:center; gap:12px; margin-bottom: 1.2rem; }
    .brand-mark { display:flex; align-items:center; justify-content:center; width:48px; height:48px; border-radius:14px; background:var(--lime); color:#111; font-size:24px; font-weight:900; }
    .brand-name { font-family:'Space Grotesk',sans-serif; font-weight:700; font-size:1.2rem; letter-spacing:.08em; }
    .brand-tag { color:var(--muted); font-size:.82rem; margin-top:2px; }
    .hero { padding: 1.6rem 0 1.3rem; border-bottom:1px solid var(--line); margin-bottom:1.6rem; }
    .eyebrow { color:var(--lime); font-weight:700; text-transform:uppercase; font-size:.76rem; letter-spacing:.14em; }
    .hero-copy { color:#b9c0c7; font-size:1.02rem; max-width:650px; }
    .panel { background:var(--panel); border:1px solid var(--line); border-radius:18px; padding:1.15rem 1.2rem; }
    .metric-label { color:var(--muted); font-size:.78rem; text-transform:uppercase; letter-spacing:.08em; }
    .metric-value { color:var(--lime); font-family:'Space Grotesk',sans-serif; font-size:1.45rem; font-weight:700; margin-top:.35rem; }
    div[data-testid="stForm"] { background:var(--panel); border:1px solid var(--line); border-radius:18px; padding:1.3rem; }
    div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea, div[data-testid="stSelectbox"] > div,
    div[data-testid="stNumberInput"] input { background:#101214 !important; border-color:#363c42 !important; }
    .stButton > button, .stFormSubmitButton > button { background:var(--lime); color:#10120e; border:0; border-radius:11px; font-weight:800; min-height:2.8rem; }
    .stButton > button:hover, .stFormSubmitButton > button:hover { background:#c8ff68; color:#10120e; border:0; }
    .stDownloadButton > button { border:1px solid #4c5a3a; background:#1b2415; color:var(--lime); border-radius:10px; font-weight:700; }
    div[data-testid="stAlert"] { border-radius:12px; }
    .small-note { color:var(--muted); font-size:.83rem; }
    .section-kicker { color:var(--lime); text-transform:uppercase; font-size:.75rem; font-weight:700; letter-spacing:.13em; }
    [data-testid="stExpander"] { border:1px solid var(--line); border-radius:12px; background:#141719; }
    @media (max-width: 640px) {
      .block-container { padding-left:1rem; padding-right:1rem; }
      .brand-mark { width:42px; height:42px; }
      div[data-testid="stForm"] { padding:.85rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Helpers ----------
def get_api_key():
    """Read the API key from Streamlit secrets, with an environment fallback."""
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        key = ""
    return key or os.getenv("GEMINI_API_KEY", "")


def needs_professional_guidance(text):
    """Conservative keyword check for injury/medical restriction disclosures."""
    terms = (
        "injury", "injured", "medical restriction", "doctor told", "physiotherapy",
        "physio", "rehab", "rehabilitation", "chronic pain", "severe pain",
        "back pain", "knee pain", "shoulder pain", "herniated", "surgery",
        "heart condition", "pregnan", "disability",
    )
    lowered = text.lower()
    return any(term in lowered for term in terms)


def build_prompt(profile):
    return f"""
You are a careful, evidence-informed general fitness programming assistant. Create a practical,
personalized workout plan in clean Markdown for the profile below.

USER PROFILE
- Goal: {profile['goal']}
- Experience: {profile['experience']}
- Training days per week: {profile['days']}
- Location: {profile['location']}
- Available equipment: {profile['equipment']}
- Session duration: {profile['duration']} minutes
- Preferred style / muscle groups: {profile['preferences'] or 'No preference supplied'}
- Limitations / exercises to avoid: {profile['limitations'] or 'None supplied'}
- Target date / short-term goal: {profile['target'] or 'No target supplied'}

NON-NEGOTIABLE RULES
1. Match the goal, experience, days, equipment, duration, and preferences above. Do not prescribe unavailable equipment.
2. Provide exactly {profile['days']} training-day plans. Schedule rest/recovery days for the remaining days of a 7-day week.
3. Keep the number of exercises and rest periods realistic for {profile['duration']} minutes. Use sensible volumes, especially for beginners.
4. For every workout day, include a Markdown table with columns: Exercise, Sets, Reps / Duration, Rest, Technique cue, Alternative.
5. Use a logical exercise order. Include a brief warm-up and cool-down for each day. Give clear, short technique cues.
6. Avoid guaranteeing results or diagnosing conditions. No extreme volume, max-effort testing, or training through pain.
7. Include a manageable starting-load explanation, simple progressive-overload method, recovery tips, and a modest week-to-week progression suggestion.
8. If the limitations field describes an injury, significant pain, medical restriction, or similar concern, do not prescribe movements that might aggravate it. Instead give general non-prescriptive guidance and advise consultation with an appropriately qualified healthcare professional before selecting exercises.
9. Do not claim the user will achieve a specific physique or result by a target date.
10. Keep wording useful and concise. Avoid repeating the same exercise unnecessarily unless there is a clear programming reason.

OUTPUT FORMAT
# Your Personalized Plan
## A. Personalized Overview
Briefly explain the training approach, weekly schedule, suggested rest days, and main focus.

## B. Weekly Workout Dashboard
Create one subsection per training day, labelled Day 1, Day 2, etc. Each must have a title, focus, estimated duration, warm-up, exercise table, and cool-down. Identify sensible rest days in the overview.

## C. Training Guidance
Use short bullets for starting load, progression, rest/recovery, consistency, and weekly progression.

## D. Quick Summary
Summarize training days, rest days, session length, and goal. End with a grounded motivational sentence.

## Safety Note
State that this is general fitness information, not medical advice; users should use controlled technique and stop if they feel sharp or unusual pain.
Return Markdown only. Do not include code fences around the whole response.
""".strip()


def generate_plan(profile):
    api_key = get_api_key()
    if not api_key:
        raise ValueError(
            "Gemini API key not found. Add GEMINI_API_KEY to .streamlit/secrets.toml "
            "or to Streamlit Community Cloud → App settings → Secrets."
        )

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=build_prompt(profile),
        config={
            "temperature": 0.55,
            "max_output_tokens": 6500,
        },
    )
    result = (response.text or "").strip()
    if len(result) < 250:
        raise RuntimeError(
            "Gemini returned an empty or incomplete plan. Please try generating again."
        )
    return result


def friendly_api_error(exc):
    message = str(exc).lower()
    if any(word in message for word in ("api key", "unauthorized", "permission_denied", "401", "403")):
        return "The API key may be invalid or may not have access to this model. Check your Gemini API key and try again."
    if any(word in message for word in ("429", "resource_exhausted", "quota", "rate limit")):
        return "Gemini's request limit or quota has been reached. Wait a little, check your API quota, then try again."
    if any(word in message for word in ("404", "not found", "model")):
        return f"The configured model ({MODEL_NAME}) may not be available to your API project. Check the current Gemini model list and update MODEL_NAME in app.py."
    if any(word in message for word in ("timeout", "connection", "network", "503", "unavailable")):
        return "Gemini is temporarily unavailable or the network request failed. Check your internet connection and retry in a moment."
    return "Something went wrong while generating the plan. Check your API settings and connection, then try again."


# ---------- Header ----------
st.markdown(
    """
    <div class="brand">
      <div class="brand-mark">I</div>
      <div><div class="brand-name">IRONPLAN AI</div>
      <div class="brand-tag">Train with intent. Progress with a plan.</div></div>
    </div>
    <div class="hero">
      <div class="eyebrow">Your training, intelligently planned</div>
      <h1>Build a plan that works<br>for <span style="color:#b7f34a">your goals.</span></h1>
      <p class="hero-copy">A personalized weekly workout plan built around your goal, experience, equipment, and available time — powered by Gemini AI.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- Input form ----------
st.markdown('<div class="section-kicker">01 / Workout setup</div>', unsafe_allow_html=True)
st.write("Tell us about your training. The more relevant detail you provide, the more tailored your plan can be.")

with st.form("workout_form", clear_on_submit=False):
    left, right = st.columns(2, gap="large")
    with left:
        goal = st.selectbox(
            "Primary fitness goal",
            ["Muscle building", "Strength", "General fitness", "Endurance"],
            help="Choose the outcome you want your training to emphasize.",
        )
        experience = st.selectbox(
            "Training experience",
            ["Beginner", "Intermediate", "Advanced"],
            help="Choose the level that best reflects your current experience.",
        )
        days = st.select_slider("Training days per week", options=[2, 3, 4, 5, 6], value=4)
        location = st.radio("Where will you train?", ["Full gym", "Home"], horizontal=True)
        if location == "Full gym":
            equipment_options = [
                "Dumbbells", "Barbells and plates", "Cable machines", "Resistance machines",
                "Bench", "Pull-up bar", "Cardio machines",
            ]
            default_equipment = equipment_options[:]
        else:
            equipment_options = [
                "Bodyweight only", "Dumbbells", "Resistance bands", "Adjustable bench",
                "Pull-up bar", "Kettlebell",
            ]
            default_equipment = ["Bodyweight only", "Dumbbells"]
        equipment = st.multiselect(
            "Available equipment",
            equipment_options,
            default=default_equipment,
            help="Only select equipment you can reliably use.",
        )

    with right:
        duration = st.selectbox("Time per workout", [30, 45, 60, 90], index=2, format_func=lambda x: f"{x} minutes")
        preferences = st.text_input(
            "Preferred style or muscle groups (optional)",
            placeholder="e.g. upper-body focus, legs, full body",
            max_chars=180,
        )
        limitations = st.text_area(
            "Limitations or exercises to avoid (optional)",
            placeholder="e.g. avoid barbell squats; describe any relevant limitation",
            max_chars=500,
            height=105,
            help="If you have an injury, significant pain, or a medical restriction, seek qualified professional guidance before choosing exercises.",
        )
        target = st.text_input(
            "Target date or short-term goal (optional)",
            placeholder="e.g. prepare for a hiking trip in 8 weeks",
            max_chars=180,
        )
        st.caption("No account required. Your workout inputs are used to create this plan.")

    submitted = st.form_submit_button("Generate My Plan", use_container_width=True)

if submitted:
    if not equipment:
        st.error("Please select at least one piece of available equipment.")
    elif needs_professional_guidance(limitations):
        st.warning(
            "Your note may describe an injury, significant pain, or a medical restriction. "
            "For safety, this app will not generate an exercise prescription from that note. "
            "Please ask a qualified healthcare professional or physiotherapist to guide appropriate activity. "
            "You can return and create a general plan after you have suitable guidance."
        )
        st.session_state.pop("workout_plan", None)
        st.session_state.pop("workout_profile", None)
    else:
        profile = {
            "goal": goal,
            "experience": experience,
            "days": days,
            "location": location,
            "equipment": ", ".join(equipment),
            "duration": duration,
            "preferences": preferences.strip(),
            "limitations": limitations.strip(),
            "target": target.strip(),
        }
        try:
            with st.spinner("Building your plan… Gemini is tailoring your weekly training split."):
                plan = generate_plan(profile)
            st.session_state["workout_plan"] = plan
            st.session_state["workout_profile"] = profile
            st.success("Your workout plan is ready.")
        except ValueError as exc:
            st.error(str(exc))
        except genai_errors.APIError as exc:
            st.error(friendly_api_error(exc))
        except Exception as exc:
            st.error(friendly_api_error(exc))

# ---------- Results ----------
if st.session_state.get("workout_plan"):
    plan = st.session_state["workout_plan"]
    profile = st.session_state.get("workout_profile", {})
    st.divider()
    st.markdown('<div class="section-kicker">02 / Your plan</div>', unsafe_allow_html=True)
    st.title("Your training dashboard")
    st.caption("Review the plan, open each workout section, and download a copy for your records.")

    m1, m2, m3, m4 = st.columns(4)
    metrics = [
        (m1, "Training days", f"{profile.get('days', '—')} / week"),
        (m2, "Session length", f"{profile.get('duration', '—')} min"),
        (m3, "Primary goal", profile.get("goal", "Personalized")),
        (m4, "Experience", profile.get("experience", "—")),
    ]
    for column, label, value in metrics:
        with column:
            st.markdown(
                f'<div class="panel"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("")
    with st.expander("Your setup details", expanded=False):
        st.write(f"**Location:** {profile.get('location', '—')}")
        st.write(f"**Equipment:** {profile.get('equipment', '—')}")
        st.write(f"**Preferences:** {profile.get('preferences') or 'None supplied'}")
        st.write(f"**Limitations:** {profile.get('limitations') or 'None supplied'}")
        st.write(f"**Target:** {profile.get('target') or 'None supplied'}")

    st.markdown(plan)
    safe_name = re.sub(r"[^a-zA-Z0-9_-]+", "-", str(profile.get("goal", "workout")).lower()).strip("-")
    st.download_button(
        "Download My Workout Plan",
        data=f"# IRONPLAN AI — Your Workout Plan\n\nGenerated with Gemini AI ({MODEL_NAME}).\n\n{plan}\n\n---\nGeneral fitness information only; not medical advice.",
        file_name=f"ironplan-{safe_name or 'workout'}-plan.md",
        mime="text/markdown",
        use_container_width=True,
    )
    if st.button("Generate New Plan", use_container_width=True):
        st.session_state.pop("workout_plan", None)
        st.session_state.pop("workout_profile", None)
        st.rerun()

st.divider()
st.markdown(
    """
    <p class="small-note">IRONPLAN AI provides general fitness information, not medical advice. Start with manageable loads, prioritize controlled technique, and stop if you experience sharp or unusual pain. Consult a qualified professional about injuries or medical restrictions.</p>
    """,
    unsafe_allow_html=True,
)
