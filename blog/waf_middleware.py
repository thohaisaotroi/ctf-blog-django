import re
from django.http import HttpResponse

_BLOCKED = re.compile(
    r'(sleep\s*\('
    r'|select\s+'
    r'|union\s+select'
    r'|extractvalue\s*\('
    r'|information_schema'
    r'|load_file\s*\('
    r'|into\s+outfile)',
    re.IGNORECASE,
)

_WAF_PAGE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>403 Forbidden — NEURAL_FEED</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0 }}
    body {{
      background: #060606;
      color: #39ff14;
      font-family: 'Courier New', Courier, monospace;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      padding: 24px;
    }}
    .card {{
      border: 1px solid #39ff14;
      padding: 48px 40px;
      max-width: 600px;
      width: 100%;
      box-shadow: 0 0 32px #39ff1430;
    }}
    h1 {{
      color: #ff3131;
      font-size: 1.25rem;
      letter-spacing: 3px;
      margin-bottom: 24px;
    }}
    p {{ line-height: 1.7; color: #aaa }}
    .label {{
      color: #555;
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 2px;
      margin-top: 28px;
      margin-bottom: 8px;
    }}
    code {{
      display: block;
      background: #111;
      color: #ffe600;
      padding: 12px 16px;
      font-size: 0.82rem;
      word-break: break-all;
      border-left: 3px solid #ffe600;
    }}
    .footer {{
      color: #333;
      font-size: 0.68rem;
      margin-top: 32px;
      padding-top: 16px;
      border-top: 1px solid #1a1a1a;
    }}
  </style>
</head>
<body>
  <div class="card">
    <h1>[ 403 :: ACCESS_DENIED ]</h1>
    <p>A suspicious pattern was detected in your request and has been blocked.</p>

    <div class="label">Blocked Input</div>
    <code>{raw}</code>

    <div class="footer">
      Security Filter &mdash; NEURAL_FEED
    </div>
  </div>
</body>
</html>"""


class SimpleWAFMiddleware:
    """Django middleware — attach in settings.MIDDLEWARE before CommonMiddleware."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/posts/':
            raw_qs = request.META.get('QUERY_STRING', '')
            if 'sort' in raw_qs:
                m = _BLOCKED.search(raw_qs)
                if m:
                    return HttpResponse(
                        _WAF_PAGE.format(raw=raw_qs[:400]),
                        status=403,
                        content_type='text/html; charset=utf-8',
                    )
        return self.get_response(request)
