FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the FastAPI application files
COPY ./app ./app

# Copy the requirements and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Expose the port that FastAPI will run on
EXPOSE 8000

# Command to run the FastAPI app using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
