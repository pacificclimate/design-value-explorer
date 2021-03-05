
#/app/.local/bin/gunicorn --config /app/docker/production/gunicorn.conf --log-config /app/docker/production/logging.conf wsgi:server
#/app/.local/bin/gunicorn \
#  --config /app/docker/production/gunicorn.conf \
#  --log-config /app/docker/production/logging.conf \
#  wsgi:server
# /app/.local/bin/gunicorn -w 4 -b 0.0.0.0:5000 wsgi:server
# /app/.local/bin/gunicorn -w 1 --log-level DEBUG --timeout 60 -b 0.0.0.0:5000 wsgi:server
/bin/bash
