# base on latest python image
FROM python:latest
# add our python program
ADD ./inputter/inputter.py ./
ADD infofile.py ./
ADD samples.json ./
# install dependent libraries
RUN pip install pika
# the command to run our program
CMD [ "python", "./inputter.py"]

