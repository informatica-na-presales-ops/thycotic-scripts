FROM python:3.10.3-alpine3.15

RUN /usr/sbin/adduser -g python -D python

USER python
RUN /usr/local/bin/python -m venv /home/python/venv

COPY --chown=python:python requirements.txt /home/python/thycotic-scripts/requirements.txt
RUN /home/python/venv/bin/pip install --no-cache-dir --requirement /home/python/thycotic-scripts/requirements.txt

WORKDIR /home/python/thycotic-scripts
ENTRYPOINT ["/bin/sh"]

ENV PATH="/home/python/venv/bin:${PATH}" \
    PYTHONUNBUFFERED="1" \
    TZ="Etc/UTC"

LABEL org.opencontainers.image.authors="William Jackson <wjackson@informatica.com>" \
      org.opencontainers.image.source="https://github.com/informatica-na-presales-ops/thycotic-scripts"
