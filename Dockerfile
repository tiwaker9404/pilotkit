FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -e . && useradd -m pilot && chown -R pilot /app
USER pilot

# Default: run every acceptance gate, then print the pilot readout.
# Set ANTHROPIC_API_KEY to answer with Claude instead of the offline answerer.
CMD ["sh", "-c", "python -m unittest discover -s tests -t . && pilotkit redteam --gate && pilotkit eval --gate && pilotkit pilot"]
