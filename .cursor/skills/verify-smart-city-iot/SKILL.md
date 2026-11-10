---
name: verify-smart-city-iot
description: Launches the SmartCityIoT unified dashboard and verifies every module against the behavior the README promises - the home links, all four module dashboards, and the core traffic/energy/citizen/waste API flows - with machine-readable evidence.
---

# Verify SmartCityIoT

One command answers "does this app still do what it says it does?"

## Launch

```bash
python3 -m venv .venv && .venv/bin/pip install flask   # first run only
.venv/bin/python .cursor/skills/verify-smart-city-iot/verify.py
```

The runner is standard-library Python. It spawns `main_dashboard.py` as a
child process on port 5005, waits for it to answer, drives the app over
HTTP, then kills the process group. It refuses to run when port 5005 is
already occupied rather than probing someone else's server.

Exit code 0 and `FAILURES=0` mean every promised behavior held. Any other
result prints the failing checks and still writes the evidence bundle.

## Doctor

The first checks are environment gates: flask must be importable by the
interpreter running the script (use the venv interpreter), and port 5005
must be free. Fix what the FAIL line says and re-run; no other setup,
database, or service is needed - all module state is in memory.

## Drive

The checks walk the app the way the README says a user would:

1. The home page renders and links to all four module dashboards.
2. Traffic: dashboard HTML renders, signals are listed, and a manual
   per-aspect override (`POST /traffic/signals/<id>/set_state`) takes effect.
3. Energy: dashboard renders and streetlights are listed.
4. Citizen reporting: an issue is created, listed, and moved to
   IN_PROGRESS through the API; the dashboard page renders.
5. Waste: a bin is created, driven to FULL through the sensor endpoint,
   and a collection route generated for it; the dashboard page renders.
6. An unknown URL returns 404.
7. The four module unit-test suites are discovered and run
   (`python -m unittest discover -s <module>/tests -t .`).

## Evidence

Every run writes a fresh `EVIDENCE_DIR` (printed at the end) containing
`evidence.json`: one record per check with its pass/fail and the detail
observed. `FAILURES=n` is the final line; the exit code mirrors it.

## Cleanup

The child server runs in its own process group and is terminated when the
run ends, pass or fail. Nothing is written outside the evidence directory
and `/tmp`; module state dies with the server.

## Helpers

- `.venv/bin/python main_dashboard.py` - run the dashboard by hand
  (`PORT=<n>` overrides the default 5005).
- `.venv/bin/python -m unittest discover -s <module>/tests -t .` - one
  module's unit tests; the `-t .` is required so package-relative imports
  resolve.

## Maintenance

When a module gains or changes an endpoint the README promises, extend the
matching block in `verify.py` in the same commit. Keep one check per
promised behavior; do not assert implementation details.

## Known boundaries

- All module state is in memory and resets on restart; the skill creates
  its own probe records (issue, bin, route) each run.
- The traffic manual-override API sets individual aspects exactly as told
  and has no safety interlock between directions - that is the documented
  contract of the simulation, not a bug the skill should flag.
- Citizen and waste modules also run standalone
  (`python -m citizen_reporting.api`, `python -m waste_management.api`);
  standalone mode mounts the same blueprints at the same `/citizen` and
  `/waste` prefixes the unified dashboard uses.
