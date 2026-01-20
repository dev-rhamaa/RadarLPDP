# Changelog

## 2025-10-03 — Refactoring & FMCW Simulation Update

### Added
- Realistic FMCW radar signal simulator in `dumy_gen.py` providing 11–13 MHz chirp generation with phase continuity for target detection workflows (`FMCW_SIMULATION.md`).
- Documentation of FMCW configuration parameters and usage guidance for analytics dashboards and UI validation.

### Changed
- Completed Phase 1 and Phase 2 refactors across `config.py`, `functions/data_processing.py`, `widgets/metrics.py`, `app/callbacks.py`, `app/setup.py`, `dumy_gen.py`, and `analytics.py`, yielding ~176 fewer lines, 85 % type coverage, and PEP 8 import ordering (`REFACTORING_SUMMARY.md`, `REFACTORING_PHASE2.md`, `REFACTORING_COMPLETE.md`).
- Consolidated FFT computation, peak analysis, and binary data loading into shared utilities in `functions/data_processing.py`, eliminating duplicate implementations in `analytics.py` and improving maintainability (`REDUNDANCY_FIX.md`).
- Enhanced developer ergonomics: helper functions, named threads, improved error handling, and comprehensive docstrings across the refactored modules.

### Developer Guidance
- Adopt the standardized workflow: type hints everywhere, reuse `functions.data_processing` helpers, follow PEP 8 import sections, and document with Google-style docstrings (`DEVELOPER_CHECKLIST.md`).
- Validate changes by running `python main.py`, `python dumy_gen.py`, and `python run_analytics.py`, plus optional tooling (`mypy`, `black`, `isort`, `pytest`) for quality gates.
- Focus upcoming efforts on unit testing (>80 % coverage), logging instead of prints, splitting `analytics.py` into submodules, and adding configuration validation to sustain refactoring gains.

### Removed
- Deprecated standalone markdown reports (`DEVELOPER_CHECKLIST.md`, `FMCW_SIMULATION.md`, `QUICK_SUMMARY.md`, `Readme_Dev.md`, `REDUNDANCY_FIX.md`, `REFACTORING_COMPLETE.md`, `REFACTORING_SUMMARY.md`, `REFACTORING_PHASE2.md`) in favor of this consolidated changelog.
