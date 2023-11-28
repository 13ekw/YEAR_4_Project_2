# base on latest python image
FROM python:latest
# add our python program
ADD proj_code.py ./
# install dependent libraries
RUN pip install numpy matplotlib uproot awkward vector
# the command to run our program
CMD [ "python", "./proj_code.py"]

