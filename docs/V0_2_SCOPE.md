# MMPPE V0.2 RC2 — Generic Experiment Runtime

V0.2 adds a generic experiment execution runtime on top of the qualified V0.1 deployment foundation.

Implemented in this milestone:
- Experiment definitions remain external JSON configuration.
- Runtime instances are created from an experiment definition.
- Generic phase sequencing and repetitions.
- Runtime start/advance/completion state.
- Generic response submission on response-enabled phases.
- Standard in-memory SESSION_START, PHASE_START, STIMULUS_ONSET, RESPONSE, PHASE_END, SESSION_END events.
- Runtime state, events, and responses exposed through API endpoints.
- N=1 demonstration experiment executes without ARL-specific logic.
- Browser opening uses the Windows default browser; no Edge/Chrome/Firefox preference is hard-coded.

Not yet in V0.2:
- Automatic timed phase advancement.
- Full participant networking/UI.
- Persistent runtime/event/response storage.
- Physical LSL marker emission from runtime events.
- ARL migration.
- Media integration.
