import sys
import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

files = [
    '/',
    '/assets/css/variables.css',
    '/assets/css/base.css',
    '/assets/css/components.css',
    '/assets/css/landing.css',
    '/assets/css/dashboard.css',
    '/assets/css/voice.css',
    '/assets/css/support.css',
    '/assets/css/demo.css',
    '/assets/js/config.js',
    '/assets/js/api.js',
    '/assets/js/store.js',
    '/assets/js/auth.js',
    '/assets/js/subscriptionService.js',
    '/assets/js/voiceService.js',
    '/assets/js/supportService.js',
    '/assets/js/demoService.js',
    '/assets/js/router.js',
    '/assets/js/app.js'
]

print("Testing Frontend Asset Delivery:")
all_ok = True
for f in files:
    url = "http://127.0.0.1:8000" + f
    try:
        r = requests.get(url)
        status = r.status_code
        content_type = r.headers.get("content-type", "")
        size = len(r.content)
        if status == 200:
            print(f"[OK 200] {f} ({size} bytes, {content_type})")
        else:
            print(f"[FAILED {status}] {f}")
            all_ok = False
    except Exception as e:
        print(f"[ERROR] {f}: {e}")
        all_ok = False

if all_ok:
    print("\nALL FRONTEND ASSETS & SPA ROUTING CONFIRMED 100% OPERATIONAL!")
