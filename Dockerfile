# base on latest python image
FROM python:latest
# add our python program
ADD HZZAnalysis.py ./
# install dependent libraries
RUN pip install numpy matplotlib uproot awkward vector
# the command to run our program
CMD [ "python", "./HZZAnalysis.py"]

