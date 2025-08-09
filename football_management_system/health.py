import time
from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError


def healthz(request):
    started = time.time()
    db_status = 'ok'
    try:
        conn = connections['default']
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        cursor.fetchone()
    except OperationalError:
        db_status = 'error'

    elapsed = round((time.time() - started) * 1000, 2)
    overall = 'ok' if db_status == 'ok' else 'degraded'
    return JsonResponse({
        'status': overall,
        'db': db_status,
        'elapsed_ms': elapsed,
        'app': 'tyfc-team-manus',
    })
