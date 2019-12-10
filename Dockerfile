FROM python:3
RUN mkdir -p /app/config; mkdir /app/cache
WORKDIR /app/
VOLUME /app/config
VOLUME /app/cache
VOLUME /var/log/
COPY going_home.py .
COPY requirements.txt .
COPY config/* config/

EXPOSE 8000

# Install python dependencies:
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "going_home.py", "--server"]
