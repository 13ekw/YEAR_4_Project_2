import uproot # for reading .root files
import awkward as ak # to represent nested data in columnar format
import vector # for 4-momentum calculations
import pika
import time
import pickle
import infofile # local file containing cross-sections, sums of weights, dataset IDs

tuple_path = "https://atlas-opendata.web.cern.ch/atlas-opendata/samples/2020/4lep/" # web address of data
lumi = 10 # fb-1 # data_A,data_B,data_C,data_D
fraction = 0.1 # reduce this is if you want the code to run quicker
MeV = 0.001 # Units, as stored in the data files

# define function to calculate weight of MC event
def calc_weight(xsec_weight, events):
    return (
        xsec_weight
        * events.mcWeight
        * events.scaleFactor_PILEUP
        * events.scaleFactor_ELE
        * events.scaleFactor_MUON 
        * events.scaleFactor_LepTRIGGER
    )

# define function to get cross-section weight
def get_xsec_weight(sample):
    info = infofile.infos[sample] # open infofile
    xsec_weight = (lumi*1000*info["xsec"])/(info["sumw"]*info["red_eff"]) #*1000 to go from fb-1 to pb-1
    return xsec_weight # return cross-section weight

# define function to calculate 4-lepton invariant mass.
def calc_mllll(lep_pt, lep_eta, lep_phi, lep_E):
    # construct awkward 4-vector array
    p4 = vector.zip({"pt": lep_pt, "eta": lep_eta, "phi": lep_phi, "E": lep_E})
    # calculate invariant mass of first 4 leptons
    # [:, i] selects the i-th lepton in each event
    # .M calculates the invariant mass
    return (p4[:, 0] + p4[:, 1] + p4[:, 2] + p4[:, 3]).M * MeV

# cut on lepton charge
# paper: "selecting two pairs of isolated leptons, each of which is comprised of two leptons with the same flavour and opposite charge"
def cut_lep_charge(lep_charge):
# throw away when sum of lepton charges is not equal to 0
# first lepton in each event is [:, 0], 2nd lepton is [:, 1] etc
    return lep_charge[:, 0] + lep_charge[:, 1] + lep_charge[:, 2] + lep_charge[:, 3] != 0

# cut on lepton type
# paper: "selecting two pairs of isolated leptons, each of which is comprised of two leptons with the same flavour and opposite charge"
def cut_lep_type(lep_type):
# for an electron lep_type is 11
# for a muon lep_type is 13
# throw away when none of eeee, mumumumu, eemumu
    sum_lep_type = lep_type[:, 0] + lep_type[:, 1] + lep_type[:, 2] + lep_type[:, 3]
    return (sum_lep_type != 44) & (sum_lep_type != 48) & (sum_lep_type != 52)

def read_file(path,sample):
    start = time.time() # start the clock
    print("\tProcessing: "+sample) # print which sample is being processed
    data_all = [] # define empty list to hold all data for this sample
    
    # open the tree called mini using a context manager (will automatically close files/resources)
    with uproot.open(path + ":mini") as tree:
        numevents = tree.num_entries # number of events
        if 'data' not in sample: xsec_weight = get_xsec_weight(sample) # get cross-section weight
        for data in tree.iterate(['lep_pt','lep_eta','lep_phi',
                                  'lep_E','lep_charge','lep_type', 
                                  # add more variables here if you make cuts on them 
                                  'mcWeight','scaleFactor_PILEUP',
                                  'scaleFactor_ELE','scaleFactor_MUON',
                                  'scaleFactor_LepTRIGGER'], # variables to calculate Monte Carlo weight
                                 library="ak", # choose output type as awkward array
                                 entry_stop=numevents*fraction): # process up to numevents*fraction

            nIn = len(data) # number of events in this batch

            if 'data' not in sample: # only do this for Monte Carlo simulation files
                # multiply all Monte Carlo weights and scale factors together to give total weight
                data['totalWeight'] = calc_weight(xsec_weight, data)

            # cut on lepton charge using the function cut_lep_charge defined above
            data = data[~cut_lep_charge(data.lep_charge)]

            # cut on lepton type using the function cut_lep_type defined above
            data = data[~cut_lep_type(data.lep_type)]

            # calculation of 4-lepton invariant mass using the function calc_mllll defined above
            data['mllll'] = calc_mllll(data.lep_pt, data.lep_eta, data.lep_phi, data.lep_E)

            # array contents can be printed at any stage like this
            #print(data)

            # array column can be printed at any stage like this
            #print(data['lep_pt'])

            # multiple array columns can be printed at any stage like this
            #print(data[['lep_pt','lep_eta']])

            nOut = len(data) # number of events passing cuts in this batch
            data_all.append(data) # append array from this batch
            elapsed = time.time() - start # time taken to process
            #print("\t\t nIn: "+str(nIn)+",\t nOut: \t"+str(nOut)+"\t in "+str(round(elapsed,1))+"s") # events before and after
    
        data_final = ak.concatenate(data_all) # return array containing events passing all cuts
    return data_final.to_list()

# Establish a connection to the RabbitMQ server
params = pika.ConnectionParameters('year_4_project_2-rabbitmq-1')
connection = pika.BlockingConnection(params)
# Create a channel for communication
channel = connection.channel()
# Declare a queue named 'filestring'
channel.queue_declare(queue='filestring')
# Set QoS to limit the number of unacknowledged messages to 1
channel.basic_qos(prefetch_count=1)

# Define the callback function to handle received messages
def callback(ch, method, properties, body):
    # Acknowledge the message received
    channel.basic_ack(delivery_tag=method.delivery_tag)
    # Decode the message body
    body = body.decode("utf-8")
    #print statements to check the data is being received
    print('WORKER Received '+body)
    # Split the message into prefix and value
    prefix_val = body.split()
    prefix = prefix_val[0]
    val = prefix_val[1]
    # Construct the URL to the .root file
    url = tuple_path+prefix+val+".4lep.root"
    # Read the file and append the value
    temp = read_file(url,val)
    temp.append(val)
    # Serialize the data using pickle
    temp = pickle.dumps(temp)
    # Publish the serialized data to the 'output' queue
    channel.basic_publish(exchange='', routing_key='output', body=temp)
    #print statements to check the data is being sent
    print(" WORKER Sent " + val)

# Set up a consumer to receive messages from the 'filestring' queue
channel.basic_consume(queue='filestring', auto_ack=False, on_message_callback=callback)
# Declare the 'output' queue
channel.queue_declare(queue='output')
# Start consuming messages from the 'filestring' queue
channel.start_consuming()