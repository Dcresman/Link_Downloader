FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DENO_INSTALL=/opt/deno
ENV PATH="/opt/deno/bin:${PATH}"

RUN apt-get update \
    && apt-get install -y \
        --no-install-recommends \
        ffmpeg \
        curl \
        ca-certificates \
        unzip \
        git \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deno.land/install.sh \
    | sh -s -- -y

# Install the matching BgUtils PO Token provider.
RUN git clone \
        --single-branch \
        --branch 1.3.1 \
        https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git \
        /root/bgutil-ytdlp-pot-provider \
    && cd /root/bgutil-ytdlp-pot-provider/server \
    && deno install --allow-scripts=npm:canvas --frozen

WORKDIR /app

COPY requirements.txt .

RUN pip install \
    --no-cache-dir \
    -r requirements.txt

COPY . .

RUN mkdir -p /app/downloads

EXPOSE 10000

# Start the BgUtils HTTP PO-token provider on its default
# localhost port 4416, then start the Flask app with Gunicorn.
CMD ["sh", "-c", "cd /root/bgutil-ytdlp-pot-provider/server/node_modules && deno run --allow-env --allow-net --allow-ffi=. --allow-read=. ../src/main.ts & sleep 2 && cd /app && exec gunicorn --workers 1 --threads 2 --timeout 600 --bind 0.0.0.0:${PORT:-10000} app:app"]