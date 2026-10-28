# IRONPLAN AI — AI Gym Workout Planner

IRONPLAN AI is a beginner-friendly fitness web application built with Python, Streamlit, and Google's Gemini API. It creates a personalized weekly workout plan based on a user's goal, experience, training days, available equipment, session length, preferences, and stated limitations.

> **Safety note:** This app provides general fitness information, not medical advice. It is not a substitute for an exercise professional or healthcare professional. Do not train through sharp or unusual pain.

## Features

- Premium dark interface with lime-green accents.
- Personalized plans for muscle building, strength, general fitness, and endurance.
- Beginner, intermediate, and advanced experience options.
- Home or full-gym equipment selection.
- Session durations of 30, 45, 60, or 90 minutes.
- Workout-day tables with sets, reps, rest, technique cues, and alternatives.
- Warm-up, cool-down, progression, and recovery guidance.
- Conservative handling of injury/medical-restriction disclosures.
- Session-state storage, progress spinner, friendly error messages, and Markdown download.
- No database, login, or external fitness service required.

## Project files

```text
ironplan-ai/
├── app.py
├── requirements.txt
├── README.md
└── .streamlit/
    └── secrets.toml   # local only; never commit this file
```

## Prerequisites

- Python 3.10 or newer.
- VS Code (recommended) or another Python editor.
- Internet access for Gemini API calls.
- A Gemini API key from Google AI Studio, subject to current account availability, quota, and terms.

The app uses the official `google-genai` SDK and the model identifier `gemini-3.8-flash`. Model availability can vary by API project and change over time. If Google changes availability, verify the current model name in the [Gemini model list](https://ai.google.dev/gemini-api/docs/models) and update `MODEL_NAME` near the top of `app.py`.

## Installation and local setup

### 1. Open the project

Create a folder named `ironplan-ai`, then put `app.py`, `requirements.txt`, and `README.md` inside it.

### 2. Create a virtual environment

Open the VS Code terminal in the project folder.

**Windows PowerShell:**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, either use Command Prompt:

```bat
.venv\Scripts\activate.bat
```

or run the app using the virtual environment's Python executable without activating it.

### 3. Install packages

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Create the local secrets file

Create a folder named `.streamlit` in the project folder. Inside it, create `secrets.toml` with this content:

```toml
GEMINI_API_KEY = "paste_your_real_api_key_here"
```

Get a key through [Google AI Studio](https://aistudio.google.com/), following Google's current account and API-key instructions.

**Never commit or upload `.streamlit/secrets.toml`, your API key, or any other credential to GitHub.** Do not put the key directly in `app.py`.

### 5. Run the app

```bash
python -m streamlit run app.py
```

Streamlit should open a local browser tab. If it does not, use the local URL printed in the terminal, usually `http://localhost:8501`.

## Test with sample inputs

Try the following example:

- **Goal:** Muscle building
- **Experience:** Beginner or Intermediate
- **Training days:** 4
- **Location:** Full gym
- **Equipment:** Select the equipment you can actually use
- **Duration:** 60 minutes
- **Preferences:** Balanced full-body development
- **Limitations:** Leave blank if none
- **Target:** Build a consistent training routine over the next 8 weeks

Click **Generate My Plan**. Check that the plan contains the requested number of workout days, exercise tables, warm-ups, cool-downs, rest days, progression guidance, and a safety note. Then test **Download My Workout Plan** and open the downloaded Markdown file.

Also test home/bodyweight equipment, a shorter session, and an empty equipment selection. Do not enter a real injury or medical condition merely to test the interface; the app may intentionally block plan generation when it detects a safety-related disclosure.

## Upload to GitHub using GitHub Desktop

1. Install and open [GitHub Desktop](https://desktop.github.com/), then sign in.
2. Select **File → Add Local Repository** if you have already initialized the project folder. If it is not a repository yet, select **File → New Repository** and choose the project folder.
3. Check the file list before committing. Ensure `.streamlit/secrets.toml` is excluded.
4. If needed, create a `.gitignore` file in the project root with:

   ```gitignore
   .venv/
   __pycache__/
   .streamlit/secrets.toml
   .env
   *.pyc
   ```

5. Enter a summary such as `Build IRONPLAN AI workout planner`.
6. Click **Commit to main**.
7. Click **Publish repository** (or **Push origin** if the repository already exists). For a class project, a public repository is convenient, but first verify that no secrets are included.

If you accidentally commit a real API key, remove it from the repository and rotate/revoke that key immediately. Deleting it from the latest commit alone may not remove it from Git history.

## Deploy on Streamlit Community Cloud

1. Push your project to GitHub.
2. Open [Streamlit Community Cloud](https://share.streamlit.io/) and sign in using GitHub.
3. Choose **Create app**, select your repository and branch, and set the main file path to `app.py`.
4. Open the app's **Settings → Secrets** section.
5. Add the secret in TOML format:

   ```toml
   GEMINI_API_KEY = "paste_your_real_api_key_here"
   ```

6. Save the secrets and deploy/reboot the app if needed.

Do not upload the local `secrets.toml` file. Streamlit Community Cloud secrets are configured in the app settings, separately from your source code.

## Troubleshooting

### `GEMINI_API_KEY` not found
- Confirm `.streamlit/secrets.toml` is inside the project root and the key is spelled exactly `GEMINI_API_KEY`.
- Confirm the TOML syntax uses quotes around the key value.
- On Community Cloud, configure the key in **App settings → Secrets**, not in GitHub.

### Invalid key, 401, or permission error
- Confirm the key is active and copied correctly.
- Check the current API project and Google AI Studio instructions.
- Never paste the key into public issue reports or screenshots.

### Quota, rate-limit, or 429 error
- Check the project's current quota and billing/usage requirements.
- Wait and try again later; do not repeatedly click Generate.

### Model unavailable or 404
- Check the current [Gemini models documentation](https://ai.google.dev/gemini-api/docs/models).
- Update `MODEL_NAME` in `app.py` to a Flash model available to your API project.

### Network, timeout, or temporary server error
- Check your internet connection and retry after a short wait.
- A temporary service issue may resolve without a code change.

### `ModuleNotFoundError`
- Activate the correct virtual environment and run `pip install -r requirements.txt` using that environment's Python.

### App deploys locally but not on Community Cloud
- Review the deployment logs.
- Confirm `app.py` is the selected main file and `requirements.txt` is in the repository root.
- Confirm the API secret is configured in the cloud app settings.

### The plan looks incomplete
- Try generating again, or use a shorter set of preferences.
- Check for quota or output-limit errors. The app rejects very short responses instead of presenting them as a complete plan.

## How the application works

1. Streamlit collects and validates the user's workout preferences.
2. The app checks whether the limitations field appears to disclose an injury, significant pain, or medical restriction. If detected, it avoids generating an exercise prescription.
3. The app reads the API key from Streamlit secrets (or an environment variable for local alternatives).
4. The official Google Gen AI Python SDK sends a detailed prompt to Gemini Flash.
5. Gemini returns a Markdown workout plan, which Streamlit renders.
6. The result is saved in Streamlit session state and can be downloaded as a `.md` file.

The AI is generative, so outputs can vary and are not guaranteed to be error-free. Users should review exercise suitability and seek professional guidance when needed.

## Short university presentation

**Problem statement:** People often struggle to organize workouts around their goal, experience, available equipment, and schedule.

**Objective:** Build a simple AI-powered web app that generates a personalized and readable weekly workout plan.

**Technologies:** Python, Streamlit, Google Gen AI SDK, Gemini Flash, TOML secrets, GitHub, and Streamlit Community Cloud.

**AI workflow:** User inputs → validation and safety check → prompt construction → Gemini API request → Markdown response → display and download.

**Demonstration:** Choose muscle building, intermediate experience, four days per week, full gym, and 60 minutes. Generate the plan, inspect a workout table and progression advice, then download it.

**Limitations:** It relies on internet access and API quota; AI-generated exercise guidance may need review; it does not track workouts, store a user history, or replace professional assessment.

**Future improvements:** Add workout completion tracking, exercise illustrations, adjustable progression based on logged performance, export to PDF, and optional user profiles (with appropriate privacy safeguards).

**Conclusion:** IRONPLAN AI demonstrates how a generative AI API can be integrated into a beginner-friendly Python web application to produce useful, personalized output.

## Likely viva questions

**1. What is IRONPLAN AI?**  
An AI-powered web app that generates workout plans from user preferences.

**2. Why did you use Streamlit?**  
It lets me build a Python web interface quickly without a separate frontend framework.

**3. Which AI model does the project use?**  
Gemini Flash through Google's official `google-genai` Python SDK.

**4. What is an API?**  
An API allows two software systems to communicate. Here, the app sends a prompt to Gemini and receives generated text.

**5. What is prompt engineering?**  
Writing clear instructions and context so the AI returns more relevant, structured output.

**6. Why do you use Streamlit secrets?**  
To keep the API key separate from the source code.

**7. What does session state do?**  
It preserves the generated plan across normal Streamlit reruns during the current session.

**8. Why is input validation important?**  
It prevents incomplete or unsuitable input from being sent to the AI and helps the user correct mistakes.

**9. How is the plan personalized?**  
The prompt includes the user's goal, experience, training days, equipment, duration, preferences, and limitations.

**10. What happens if the API fails?**  
The app shows a friendly error message and suggests likely next steps.

**11. What is a limitation of generative AI?**  
Its output can be incorrect or unsuitable, so it must be reviewed and cannot replace professional advice.

**12. How did you deploy the project?**  
I pushed the source code to GitHub and connected the repository to Streamlit Community Cloud, where I configured the API key in app secrets.
