import infofile # local file containing cross-sections, sums of weights, dataset IDs
import json
import pika

#opens samples.json file and makes a dictionary of the samples
with open('samples.json') as json_file:
    samples = json.load(json_file)

list_filestring = [] # define empty list to hold filestrings
for s in samples: # loop over samples
    print('Processing '+s+' samples') # print which sample
    frames = [] # define empty list to hold data
    for val in samples[s]['list']: # loop over each file
        if s == 'data': prefix = "Data/" # Data prefix
        else: # MC prefix
            prefix = "MC/mc_"+str(infofile.infos[val]["DSID"])+"."
        fileString = prefix+" "+val # file name to open
        list_filestring.append(fileString)

# Establishing a connection to the RabbitMQ server using the specified parameters
params = pika.ConnectionParameters('year_4_project_2-rabbitmq-1')
connection = pika.BlockingConnection(params)
# Creating a channel for communication with the RabbitMQ server
channel = connection.channel()
# Declaring a queue named 'filestring' to receive messages
channel.queue_declare(queue='filestring')

#loop through list of filestrings
for i in list_filestring:
    #send filestring to filestring queue
    channel.basic_publish(exchange='', routing_key='filestring', body=i)
    #print statements to check the data is being sent
    print("INPUTTER Sent "+i)