# MMPPE Research Studio · Integrated Demonstration

## Launch on Windows
1. Extract the ZIP to a local folder (preferably outside OneDrive).
2. Double-click `START_MMPPE.bat`. The bootstrap prepares the Python environment and starts the FastAPI server.
3. The home page `/` is the new Research Studio. If an old browser tab remains open, navigate to `http://127.0.0.1:8100/studio` (the actual port is printed by the launcher).
4. Use **Create a Study** to configure participant count, modalities and timeline. Save it.
5. Use **Built-in Studies** to launch a study in the Moderator Console.
6. Open Participant `/p1`, `/p2`, `/p3` and Observer `/observer` in other windows. Start, advance phases, submit browser responses, monitor, and export session ZIP.

## 30-second video storyboard
0–5s: Studio home and research workflow.
5–12s: Create a Study, modality checklist, add resting baseline/stimulus/response.
12–17s: Built-in studies and Launch in Moderator.
17–24s: Moderator starts/advances; participant submits response; observer updates.
24–30s: Export session ZIP and final platform overview.

## What is implemented
Study JSON builder, configurable participants, modality requirement metadata, phase editor/reordering, built-in study library, FastAPI runtime, Moderator/Participant/Observer browser UIs, response/event logs, session persistence, pause/resume, session ZIP with CSV and JSON, LSL discovery/preflight endpoints (when available).

## What is not implemented/validated in this generic demo
Physical sensor recording, live physiological data display, continuous audio/video capture, XDF recording/conversion, automatic phase timing, participant authentication, robust restart/resume, complete multi-PC validation. Duration is protocol metadata; Moderator advances phases manually. Do not present the optional stream requirements as recorded data.

The ARL V13.6 experiment controller is not modified by this package.
