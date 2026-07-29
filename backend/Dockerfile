FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ARG BACKEND_CONTAINER_PORT=8000
ENV BACKEND_HOST=0.0.0.0 \
    BACKEND_PORT=${BACKEND_CONTAINER_PORT} \
    BACKEND_RELOAD=true
EXPOSE ${BACKEND_CONTAINER_PORT}
CMD ["sh", "-c", "uvicorn app.main:app --host \"$BACKEND_HOST\" --port \"$BACKEND_PORT\" $(if [ \"$BACKEND_RELOAD\" = \"true\" ]; then printf '%s' '--reload'; fi)"]
