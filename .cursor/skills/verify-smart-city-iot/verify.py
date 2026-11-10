#!/usr/bin/env python3
"""Purpose-fit verification for SmartCityIoT.

Launches the unified dashboard as a child process on its own port and
drives every module the way the README says a user would: the home page
links, the four module dashboards, and the core API flows behind them.
Standard library only. Refuses to run when the port is occupied.

Exit 0 and FAILURES=0 mean the app matched its promised behavior.
"""
import http.client
import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
PORT = 5005
MODULES = ['citizen_reporting', 'waste_management', 'traffic_management', 'energy_management']

checks = []
failures = []


def record(name, ok, detail=''):
    checks.append({'name': name, 'ok': bool(ok), 'detail': detail})
    print(('PASS' if ok else 'FAIL') + ' ' + name + (' :: ' + detail if detail else ''))
    if not ok:
        failures.append(name)


def req(method, path, payload=None):
    conn = http.client.HTTPConnection('127.0.0.1', PORT, timeout=10)
    body = json.dumps(payload) if payload is not None else None
    headers = {'Content-Type': 'application/json'} if payload is not None else {}
    conn.request(method, path, body=body, headers=headers)
    resp = conn.getresponse()
    text = resp.read().decode('utf-8', 'replace')
    conn.close()
    try:
        parsed = json.loads(text)
    except ValueError:
        parsed = None
    return resp.status, parsed, text


def wait_up(proc, timeout=20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            return False
        try:
            status, _, _ = req('GET', '/')
            if status:
                return True
        except OSError:
            time.sleep(0.4)
    return False


def main():
    if subprocess.run([sys.executable, '-c', 'import flask'], cwd=REPO_ROOT,
                      capture_output=True).returncode != 0:
        record('doctor: flask importable', False,
               'run: python3 -m venv .venv && .venv/bin/pip install flask, then re-run with .venv/bin/python')
        finish(None, None)
        return 1
    record('doctor: flask importable', True)

    with socket.socket() as s:
        if s.connect_ex(('127.0.0.1', PORT)) == 0:
            record('launch: port free', False, 'port %d is occupied; refusing to disturb it' % PORT)
            finish(None, None)
            return 1
    record('launch: port free', True, 'port %d' % PORT)

    log = open(os.devnull, 'wb')
    env = dict(os.environ, PORT=str(PORT))
    proc = subprocess.Popen([sys.executable, 'main_dashboard.py'], cwd=REPO_ROOT,
                            env=env, stdout=log, stderr=subprocess.STDOUT,
                            start_new_session=True)
    try:
        if not wait_up(proc):
            record('launch: dashboard serves', False, 'server did not come up in 20s')
            return 1
        record('launch: dashboard serves', True, 'GET / answered on port %d' % PORT)

        status, _, home = req('GET', '/')
        missing = [p for p in ['/traffic/', '/energy/dashboard', '/citizen/dashboard', '/waste/dashboard']
                   if p not in home]
        record('home links to all four module dashboards', status == 200 and not missing,
               'missing: %s' % missing if missing else 'all four links present, status %d' % status)

        status, _, body = req('GET', '/traffic/')
        record('traffic dashboard renders', status == 200 and 'traffic' in body.lower(),
               'status %d' % status)

        status, signals, _ = req('GET', '/traffic/signals')
        sig_list = signals if isinstance(signals, list) else list(signals.values()) if isinstance(signals, dict) else []
        record('traffic signals listed', status == 200 and len(sig_list) > 0,
               '%d signals' % len(sig_list))
        if sig_list:
            first = sig_list[0]
            sid = first.get('signal_id') or first.get('id') if isinstance(first, dict) else first
            status, resp, _ = req('POST', '/traffic/signals/%s/set_state' % sid, {'north_south': 'yellow'})
            got = (resp or {}).get('new_state', {}).get('north_south')
            record('traffic signal manual override', status == 200 and got == 'yellow',
                   'signal %s north_south -> %s' % (sid, got))

        status, _, body = req('GET', '/energy/dashboard')
        record('energy dashboard renders', status == 200, 'status %d' % status)
        status, lights, _ = req('GET', '/energy/streetlights')
        record('energy streetlights listed', status == 200 and lights is not None, 'status %d' % status)

        issue = {'category': 'Pothole', 'description': 'verify-skill probe',
                 'location': {'lat': 13.08, 'lon': 80.27}}
        status, created, _ = req('POST', '/citizen/issues', issue)
        iid = (created or {}).get('issue_id', '')
        record('citizen issue created', status == 201 and iid, 'status %d' % status)
        status, issues, _ = req('GET', '/citizen/issues')
        record('citizen issue listed', status == 200 and any(i.get('issue_id') == iid for i in (issues or [])),
               'status %d' % status)
        status, updated, _ = req('PUT', '/citizen/issues/%s/status' % iid, {'status': 'IN_PROGRESS'})
        record('citizen issue status updated', status == 200 and (updated or {}).get('status') == 'IN_PROGRESS',
               'status %d' % status)
        status, _, _ = req('GET', '/citizen/dashboard')
        record('citizen dashboard renders', status == 200, 'status %d' % status)

        status, _, _ = req('GET', '/waste/dashboard')
        record('waste dashboard renders', status == 200, 'status %d' % status)
        status, _, _ = req('POST', '/waste/bins', {'bin_id': 'verify_bin_1',
                           'location': {'lat': 13.08, 'lon': 80.27}, 'capacity_gallons': 100})
        record('waste bin created', status == 201, 'status %d' % status)
        status, b, _ = req('PUT', '/waste/bins/verify_bin_1/sensor_data', {'fill_level': 95})
        record('waste bin reports FULL at 95/100', status == 200 and (b or {}).get('status') == 'FULL',
               'status %s -> %s' % (status, (b or {}).get('status')))
        status, route, _ = req('POST', '/waste/routes/generate', {'assigned_truck_id': 'verify_truck'})
        bins_on_route = (route or {}).get('bin_ids_to_collect', [])
        record('waste collection route generated for FULL bin',
               status == 201 and 'verify_bin_1' in bins_on_route,
               'status %d, route bins: %s' % (status, bins_on_route))

        status, _, _ = req('GET', '/definitely-not-a-route')
        record('unknown route returns 404', status == 404, 'status %d' % status)

        total, failed_suites = 0, []
        for m in MODULES:
            r = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', m + '/tests', '-t', '.'],
                               cwd=REPO_ROOT, capture_output=True, text=True)
            out = r.stdout + r.stderr
            if r.returncode != 0:
                failed_suites.append(m)
            for line in out.splitlines():
                if line.startswith('Ran '):
                    total += int(line.split()[1])
        record('module unit tests green', not failed_suites and total >= 68,
               '%d tests across %d suites; failed: %s' % (total, len(MODULES), failed_suites or 'none'))
    finally:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(timeout=5)
        except Exception:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except Exception:
                pass
        log.close()
    return finish()


def finish(proc=None, log=None):
    evidence_dir = tempfile.mkdtemp(prefix='verify-smart-city-iot-')
    with open(os.path.join(evidence_dir, 'evidence.json'), 'w') as f:
        json.dump({'repo': 'SmartCityIoT', 'port': PORT, 'checks': checks,
                   'failures': failures}, f, indent=2)
    print('EVIDENCE_DIR=' + evidence_dir)
    print('FAILURES=%d' % len(failures))
    return 0 if not failures else 1


if __name__ == '__main__':
    sys.exit(main() or 0)
