import json
import os
import time
import urllib.request
import urllib.error

REPO = "catxyros-cyber/lithium-keys"
TOKEN = os.environ["GH_TOKEN"]
RESET_COOLDOWN_MS = 24 * 60 * 60 * 1000


def api(path, method="GET", body=None):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "lithium-license-bot",
        },
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def close_issue(number, comment):
    try:
        api(f"/repos/{REPO}/issues/{number}/comments", "POST", {"body": comment})
    except Exception as e:
        print(f"comment failed on #{number}: {e}")
    try:
        api(f"/repos/{REPO}/issues/{number}", "PATCH", {"state": "closed"})
    except Exception as e:
        print(f"close failed on #{number}: {e}")


with open("keys.json") as f:
    registry = json.load(f)

issues = api(f"/repos/{REPO}/issues?state=open&per_page=100")
changed = False
now = int(time.time() * 1000)

for issue in issues:
    if "pull_request" in issue:
        continue
    title = (issue.get("title") or "").strip()
    number = issue["number"]
    parts = title.split()
    if len(parts) != 3 or parts[0] not in ("LITHIUM-BIND", "LITHIUM-RESET"):
        continue
    action, key_hash, hwid_hash = parts[0], parts[1].lower(), parts[2].lower()
    entry = registry.get(key_hash)
    if entry is None:
        close_issue(number, "unknown key.")
        continue
    if not entry.get("active", True):
        close_issue(number, "this key is disabled.")
        continue

    if action == "LITHIUM-BIND":
        bound = entry.get("hwid", "")
        if bound == "":
            entry["hwid"] = hwid_hash
            changed = True
            close_issue(number, "key bound to this machine.")
            print(f"#{number}: bound {key_hash[:8]}...")
        elif bound == hwid_hash:
            close_issue(number, "already bound to this machine.")
        else:
            close_issue(
                number,
                "key is bound to another machine. use LITHIUM-RESET "
                "(24h cooldown between resets).",
            )

    elif action == "LITHIUM-RESET":
        last = entry.get("last_reset", 0)
        if last and now - int(last) < RESET_COOLDOWN_MS:
            remaining = int((RESET_COOLDOWN_MS - (now - int(last))) / 60000)
            close_issue(number, f"reset cooldown active - {remaining} minutes remaining.")
            continue
        if entry.get("hwid", "") == "":
            close_issue(number, "key is not bound to anything - nothing to reset.")
            continue
        entry["hwid"] = ""
        entry["last_reset"] = now
        changed = True
        close_issue(number, "hwid reset. activate on the new machine to re-bind.")
        print(f"#{number}: reset {key_hash[:8]}...")

if changed:
    with open("keys.json", "w") as f:
        json.dump(registry, f, indent=2)
        f.write("\n")
    print("registry updated")
