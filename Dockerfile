# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# Final stage
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY pdf_operations.py web_app.py ./
COPY templates/ templates/

# Expose the port the app listens on
EXPOSE 5000

# Run with Gunicorn (production WSGI server)
# WORKERS defaults to 2; override with: docker run -e WORKERS=4 ...
ENV WORKERS=2
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:5000 --workers ${WORKERS} --timeout 120 --access-logfile - web_app:app"]
