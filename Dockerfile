FROM python:3.10.5-alpine3.15

RUN /sbin/apk add --no-cache libpq
RUN /usr/sbin/adduser -g python -D python

USER python
RUN /usr/local/bin/python -m venv /home/python/venv

COPY --chown=python:python requirements.txt /home/python/thycotic-scripts/requirements.txt
RUN /home/python/venv/bin/pip install --no-cache-dir --requirement /home/python/thycotic-scripts/requirements.txt

COPY --chown=python:python digicert-tls-rsa-sha256-2020-ca1.cer /home/python/thycotic-scripts/digicert-tls-rsa-sha256-2020-ca1.cer
RUN /bin/cat /home/python/thycotic-scripts/digicert-tls-rsa-sha256-2020-ca1.cer >> /home/python/venv/lib/python3.10/site-packages/certifi/cacert.pem

COPY --chown=python:python delete-obsolete-secrets.py /home/python/thycotic-scripts/delete-obsolete-secrets.py
COPY --chown=python:python list-secrets-to-data-lake.py /home/python/thycotic-scripts/list-secrets-to-data-lake.py
COPY --chown=python:python sync-ops-web-passwords.py /home/python/thycotic-scripts/sync-ops-web-passwords.py

WORKDIR /home/python/thycotic-scripts
ENTRYPOINT ["/bin/sh"]

ENV PATH="/home/python/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE="1" \
    PYTHONUNBUFFERED="1" \
    TZ="Etc/UTC"

LABEL org.opencontainers.image.authors="William Jackson <wjackson@informatica.com>" \
      org.opencontainers.image.source="https://github.com/informatica-na-presales-ops/thycotic-scripts"
