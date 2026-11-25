# MMPPE V0.4.1 RC1 — Researcher Workflow

This build reorganizes the existing V0.4 platform capabilities into a researcher-facing workflow:

1. Create a Study
2. Run a Study
3. Confirm participants
4. Find and assign required data sources
5. Check study readiness
6. Run the experiment
7. View a human-readable session summary

## Important boundary

This release does **not** yet record live LSL samples into the final synchronized dataset. It validates the experiment package, 1–N participant runtime, device-independent LSL discovery/mapping, readiness workflow, and researcher-facing UI. Live acquisition/storage is the next major block.

## Device independence

Study definitions specify semantic modalities (EEG, ECG, EDA, EMG, PPG, eye tracking, IMU, audio, video, etc.), not manufacturers. During session setup, compatible LSL streams are mapped to those requirements.

## Prototype participant readiness

Participant readiness is still confirmed from the moderator screen in this release. Dedicated participant-station joining is not yet implemented and is explicitly labeled in the UI.
