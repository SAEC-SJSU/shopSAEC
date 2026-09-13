FROM ghcr.io/astral-sh/uv:python3.14-alpine

WORKDIR /app

COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

COPY . .

EXPOSE 7676

# Trust X-Forwarded-* only from the reverse proxy. "*" let any client forge its
# own source IP, which defeated the per-IP login throttle in auth.py. The
# default covers Docker's private bridge subnets; override it to the proxy's
# exact address if you know it.
ENV FORWARDED_ALLOW_IPS="127.0.0.1,172.16.0.0/12"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7676", "--proxy-headers"]
