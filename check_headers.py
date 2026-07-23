"""The issue: clicking username doesn't show profile modal until 
switching to API docs tab first.

Hypothesis: The profileModal div or its children are being hidden by CSS 
inheritance. The tab-page system uses .tab-page{display:none}. If profileModal
is somehow nested inside a tab-page element...

But we know it's after all scripts and outside any tab-page.

Another hypothesis: The inline style `style="display:none"` on profileModal 
gets overridden by the openProfile function setting `style.display='flex'`.
But maybe there's a CSS rule with higher specificity.

Let me check if the pwdModal (which user management uses) has the same issue.
If pwdModal doesn't work either, it's a systemic CSS problem.

ROOT CAUSE: Let me check if the server serves a Content-Security-Policy that
blocks inline event handlers like onclick="openProfile()".
"""
import requests, json, base64

# Check response headers
r = requests.get('https://qiezidata-production.up.railway.app/')
print('Headers:')
for k, v in r.headers.items():
    if 'content' in k.lower() or 'security' in k.lower() or 'policy' in k.lower():
        print(f'  {k}: {v}')
