import infofile # local file containing cross-sections, sums of weights, dataset IDs
import pika

samples = {

    'data': {
        'list' : ['data_A','data_B','data_C','data_D'],
    },

    r'Background $Z,t\bar{t}$' : { # Z + ttbar
        'list' : ['Zee','Zmumu','ttbar_lep'],
        'color' : "#6b59d3" # purple
    },

    r'Background $ZZ^*$' : { # ZZ
        'list' : ['llll'],
        'color' : "#ff0000" # red
    },

    r'Signal ($m_H$ = 125 GeV)' : { # H -> ZZ -> llll
        'list' : ['ggH125_ZZ4lep','VBFH125_ZZ4lep','WH125_ZZ4lep','ZH125_ZZ4lep'],
        'color' : "#00cdff" # light blue
    },

}

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

params = pika.ConnectionParameters('year_4_project_2-rabbitmq-1')
connection = pika.BlockingConnection(params)
channel = connection.channel()
channel.queue_declare(queue='filestring')

for i in list_filestring:
    channel.basic_publish(exchange='', routing_key='filestring', body=i)
    print("INPUTTER Sent "+i)
