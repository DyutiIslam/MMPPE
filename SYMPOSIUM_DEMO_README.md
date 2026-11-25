# MMPPE Symposium Demo — Software Control Only

**This is a separate copy of MMPPE V0.4.1. ARL V13.6 is unchanged.**

## Windows setup
1. Extract ZIP to a folder. Use the existing START_MMPPE.bat if Python environment is not installed (it bootstraps dependencies). Otherwise run START_SYMPOSIUM_DEMO.bat.
2. The server chooses port 8100–8110, avoiding the ARL port 8000.
3. Open `http://127.0.0.1:8100/showcase` (substitute the printed port) for Moderator. Open `/observer` in another tab/window.
4. Select **Social Influence and Judgment**, click **Load selected experiment**, then **Start**. Click **Next Phase** to progress. Open /p1, /p2 and /p3 and submit demonstration responses on the participant pages (the Moderator does not enter participant responses). Observe feedback, pause/resume, and event history.
5. Select the existing **3-Participant Collaborative Rating Demo** to show that a different JSON experiment package uses the same generic runtime.

## Truthful demonstration scope
- Real backend: experiment selection, generic phase progression, pause/resume, response capture, UTC event logging, observer state polling.
- Simulated: participant responses entered by the presenter. No live participant PCs, EEG, ECG, EMG, EDA, or LSL streams.
- No physiological acquisition, LabRecorder recording, media capture, or cross-device timing is validated by this demo.
- No human-subject research is conducted in this showcase. The scenario and ratings are illustrative.
- Session records are automatically saved to data/sessions/<runtime_id>.json after every logged event. Running sessions are still in-memory, so restarting the server does not resume an interrupted session. Saved JSON files remain available after restart. Use the Moderator Download session data button to export session.json, events.csv, responses.csv, and experiment_config.json as a ZIP. No sensor data/XDF conversion is available without recorded sensor data.
- Phase progression is Moderator-controlled; no automatic timer is used in the showcase.
- The original researcher workflow remains at `/`.

## Technical checks
`python -m pytest tests -q` (if pytest installed), or use the provided `tests/test_symposium_demo.py`.

## What is implemented vs not implemented
**Implemented and testable in this ZIP:** JSON experiment library; generic phase runtime; moderator start/next/pause/resume; participant browser windows P01-P03; participant response submission with duplicate protection; observer state; event log; automatic JSON persistence; CSV/JSON ZIP export.

**Prototype limitations:** participant connection status is a one-time browser registration, not a live heartbeat; no authentication or secure participant identity; no automatic phase timer or auto-advance (even if an experiment definition specifies `advance_when`); no response-value range validation; no persisted runtime recovery after restart; no sensor acquisition/LSL recording, LabRecorder/XDF conversion, or actual media recording in the symposium demo. The experiment library lists configuration, not proof of a completed study.

## 90-second rehearsal
1. Start server; open Moderator `/showcase`, Participant `/p1` and Observer `/observer` in separate browser windows.
2. Moderator: select Social Influence and Judgment → Load → Start → Next Phase twice to reach Independent Judgment.
3. Participant P01: choose a rating. Open `/p2` and `/p3` to submit two more ratings if time permits.
4. Moderator: advance to Group Feedback and Revised Judgment; Observer: verify response count and event log update.
5. Moderator: download ZIP; inspect `events.csv`, `responses.csv`, `session.json`.
6. If restarting, load a **new** session; previously saved files remain in `data/sessions/`, but interrupted sessions cannot resume.
