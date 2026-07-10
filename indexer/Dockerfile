# Use a base Python image
FROM python:3.9-slim
ARG http_proxy
ARG https_proxy
ARG no_proxy

ENV http_proxy=$http_proxy \
    https_proxy=$https_proxy \
    no_proxy=$no_proxy \
    HTTP_PROXY=$http_proxy \
    HTTPS_PROXY=$https_proxy \
    NO_PROXY=$no_proxy

# Set the working directory inside the container
WORKDIR /app/

# Copy the requirements.txt file to the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory into the container
COPY . .

USER 1000:1000

# Set the default command to run the Python script
CMD ["python", "index_programs.py"]