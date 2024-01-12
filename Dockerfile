FROM ubuntu:20.04

# Set environment variable to ensure non-interactive mode for apt-get
ENV DEBIAN_FRONTEND=noninteractive

# Update and install necessary packages
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --fix-missing ffmpeg python3 python3-pip

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file
COPY requirements.txt requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

CMD ["python3", "bot.py"]
