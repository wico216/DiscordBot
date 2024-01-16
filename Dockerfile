# Use an official Python runtime as a parent image
FROM python:3.12.1

#Install ffmpeg
RUN apt-get -y update
RUN apt-get install ffmpeg libsm6 libxext6  -y
# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
# (Uncomment if your bot uses a web server or similar)
# EXPOSE 80

# Define environment variable
# (Uncomment and use if you have other environment variables)
# ENV NAME=Value

# Run bot.py when the container launches
CMD ["python", "./bot.py"]
