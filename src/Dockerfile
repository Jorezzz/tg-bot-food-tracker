FROM python:3.11-slim-buster

WORKDIR /app

COPY . ./

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

EXPOSE 80

CMD ["python", "bot.py"]