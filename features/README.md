# Feature map - SmartCityIoT

What this repo promises (from README.md) and where each promise is proven.

| Feature | Entry point | Proven by |
| --- | --- | --- |
| Unified dashboard home linking all modules | `GET /` | verify.py "home links to all four module dashboards" |
| Traffic monitoring + manual override + emergency preemption | `GET /traffic/`, `/traffic/signals*` | verify.py traffic checks; `traffic_management/tests` |
| Energy / streetlight management | `GET /energy/dashboard`, `/energy/streetlights*` | verify.py energy checks; `energy_management/tests` |
| Citizen issue reporting + tracking | `GET /citizen/dashboard`, `/citizen/issues*` | verify.py citizen checks; `citizen_reporting/tests` |
| Waste bin monitoring + route generation | `GET /waste/dashboard`, `/waste/bins*`, `/waste/routes*` | verify.py waste checks; `waste_management/tests` |

The automated proof lives in `.cursor/skills/verify-smart-city-iot/`.
