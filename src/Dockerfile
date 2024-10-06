FROM python:3.11-slim-buster

WORKDIR /app

COPY . ./

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 80

CMD ["python", "bot.py"]