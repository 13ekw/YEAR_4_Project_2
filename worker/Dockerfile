# base on latest python image
FROM python:latest
# add our python program
ADD ./worker/worker.py ./
ADD infofile.py ./
# install dependent libraries
RUN pip install uproot awkward vector pika
# the command to run our program
CMD [ "python", "-u", "./worker.py"]

