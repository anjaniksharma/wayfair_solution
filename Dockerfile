
# This is a Python 3 image that uses the nginx, gunicorn, flask stack
# for serving inferences in a stable way.

FROM python:3

RUN apt-get update && apt-get install -y --no-install-recommends wget nginx 
RUN pip --no-cache-dir install pandas=='1.3.4' flask=='1.1.2' gunicorn=='20.1.0' requests=='2.25.1'

ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE
ENV PATH="/opt/ml:${PATH}"

WORKDIR /opt/ml/model
