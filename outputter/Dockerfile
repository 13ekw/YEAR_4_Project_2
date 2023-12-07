# base on latest python image
FROM python:latest
# add our python program
ADD ./outputter/outputter.py ./
ADD infofile.py ./
ADD samples.json ./
# install dependent libraries
RUN pip install numpy matplotlib awkward pika
# the command to run our program
CMD [ "python", "./outputter.py", "-o", "output.png"]

