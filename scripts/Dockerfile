# Use a base Python image
FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt file to the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory (scripts) into the container
COPY . .

# Set the default command to run the Python script
CMD ["python", "index_programs.py"]
