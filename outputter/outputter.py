import pika
import awkward as ak
import numpy as np
import math
import json
import zlib
import matplotlib.pyplot as plt # for plotting
from matplotlib.ticker import AutoMinorLocator # for minor ticks

#opens samples.json file and makes a dictionary of the samples
with open('samples.json') as json_file:
    samples = json.load(json_file)

#initalises and empty dictionary to hold the data
data_final = {key: [] for key in samples.keys()}

#declare variables
fraction = 1.0
GeV = 1.0
lumi = 10 # fb-1 # data_A,data_B,data_C,data_D
#note lumi will likely change if new data is added

#counts the number of elements in the samples dictionary
def count_elements(samples):
    count = 0
    for section in samples.values():
        if 'list' in section:
            count += len(section['list'])
    return count

def callback(ch, method, properties, body):    
    global counter
    #decompresses and decodes the data, stores and removes the last element which is the category
    body = zlib.decompress(body)
    body = json.loads(body)
    val = body[-1]
    body = body[:-1]

    counter += 1
    
    #print statements to check the data is being received
    print('OUTPUTTER Received ' + val)
    print("COUNTER = " + str(counter) + "of" + str(count_elements(samples)))

    #sorts the data into the correct category
    if val in samples['data']['list']:
        data_final['data'].append(ak.Array(body))
    elif val in samples[r'Background $Z,t\bar{t}$']['list']:
        data_final[r'Background $Z,t\bar{t}$'].append(ak.Array(body))
    elif val in samples['Background $ZZ^*$']['list']:
        data_final[r'Background $ZZ^*$'].append(ak.Array(body))
    elif val in samples['Signal ($m_H$ = 125 GeV)']['list']:
        data_final[r'Signal ($m_H$ = 125 GeV)'].append(ak.Array(body))

    #checks if all the data has been received, if so concatinates and plots
    if counter == count_elements(samples):
        for category,data in data_final.items():
            data_final[category] = ak.concatenate(data)
        channel.stop_consuming()
        print("Plotting data")
        plot_data(data_final)

def plot_data(data):
    xmin = 80 * GeV
    xmax = 250 * GeV
    step_size = 5 * GeV

    bin_edges = np.arange(start=xmin, # The interval includes this value
                     stop=xmax+step_size, # The interval doesn't include this value
                     step=step_size ) # Spacing between values
    bin_centres = np.arange(start=xmin+step_size/2, # The interval includes this value
                            stop=xmax+step_size/2, # The interval doesn't include this value
                            step=step_size ) # Spacing between values

    data_x,_ = np.histogram(ak.to_numpy(data['data']['mllll']), 
                            bins=bin_edges ) # histogram the data
    data_x_errors = np.sqrt( data_x ) # statistical error on the data

    signal_x = ak.to_numpy(data[r'Signal ($m_H$ = 125 GeV)']['mllll']) # histogram the signal
    signal_weights = ak.to_numpy(data[r'Signal ($m_H$ = 125 GeV)'].totalWeight) # get the weights of the signal events
    signal_color = samples[r'Signal ($m_H$ = 125 GeV)']['color'] # get the colour for the signal bar

    mc_x = [] # define list to hold the Monte Carlo histogram entries
    mc_weights = [] # define list to hold the Monte Carlo weights
    mc_colors = [] # define list to hold the colors of the Monte Carlo bars
    mc_labels = [] # define list to hold the legend labels of the Monte Carlo bars

    for s in samples: # loop over samples
        if s not in ['data', r'Signal ($m_H$ = 125 GeV)']: # if not data nor signal
            mc_x.append( ak.to_numpy(data[s]['mllll']) ) # append to the list of Monte Carlo histogram entries
            mc_weights.append( ak.to_numpy(data[s].totalWeight) ) # append to the list of Monte Carlo weights
            mc_colors.append( samples[s]['color'] ) # append to the list of Monte Carlo bar colors
            mc_labels.append( s ) # append to the list of Monte Carlo legend labels
    


    # *************
    # Main plot 
    # *************
    main_axes = plt.gca() # get current axes
    
    # plot the data points
    main_axes.errorbar(x=bin_centres, y=data_x, yerr=data_x_errors,
                       fmt='ko', # 'k' means black and 'o' is for circles 
                       label='Data') 
    
    # plot the Monte Carlo bars
    mc_heights = main_axes.hist(mc_x, bins=bin_edges, 
                                weights=mc_weights, stacked=True, 
                                color=mc_colors, label=mc_labels )
    
    mc_x_tot = mc_heights[0][-1] # stacked background MC y-axis value
    
    # calculate MC statistical uncertainty: sqrt(sum w^2)
    mc_x_err = np.sqrt(np.histogram(np.hstack(mc_x), bins=bin_edges, weights=np.hstack(mc_weights)**2)[0])
    
    # plot the signal bar
    main_axes.hist(signal_x, bins=bin_edges, bottom=mc_x_tot, 
                   weights=signal_weights, color=signal_color,
                   label=r'Signal ($m_H$ = 125 GeV)')
    
    # plot the statistical uncertainty
    main_axes.bar(bin_centres, # x
                  2*mc_x_err, # heights
                  alpha=0.5, # half transparency
                  bottom=mc_x_tot-mc_x_err, color='none', 
                  hatch="////", width=step_size, label='Stat. Unc.' )

    # set the x-limit of the main axes
    main_axes.set_xlim( left=xmin, right=xmax ) 
    
    # separation of x axis minor ticks
    main_axes.xaxis.set_minor_locator( AutoMinorLocator() ) 
    
    # set the axis tick parameters for the main axes
    main_axes.tick_params(which='both', # ticks on both x and y axes
                          direction='in', # Put ticks inside and outside the axes
                          top=True, # draw ticks on the top axis
                          right=True ) # draw ticks on right axis
    
    # x-axis label
    main_axes.set_xlabel(r'4-lepton invariant mass $\mathrm{m_{4l}}$ [GeV]',
                        fontsize=13, x=1, horizontalalignment='right' )
    
    # write y-axis label for main axes
    main_axes.set_ylabel('Events / '+str(step_size)+' GeV',
                         y=1, horizontalalignment='right') 
    
    # set y-axis limits for main axes
    main_axes.set_ylim( bottom=0, top=np.amax(data_x)*1.6 )
    
    # add minor ticks on y-axis for main axes
    main_axes.yaxis.set_minor_locator( AutoMinorLocator() ) 

    # Add text 'ATLAS Open Data' on plot
    plt.text(0.05, # x
             0.93, # y
             'ATLAS Open Data', # text
             transform=main_axes.transAxes, # coordinate system used is that of main_axes
             fontsize=13 ) 
    
    # Add text 'for education' on plot
    plt.text(0.05, # x
             0.88, # y
             'for education', # text
             transform=main_axes.transAxes, # coordinate system used is that of main_axes
             style='italic',
             fontsize=8 ) 
    
    # Add energy and luminosity
    lumi_used = str(lumi*fraction) # luminosity to write on the plot
    plt.text(0.05, # x
             0.82, # y
             r'$\sqrt{s}$=13 TeV,$\int$L dt = '+lumi_used+' fb$^{-1}$', # text
             transform=main_axes.transAxes ) # coordinate system used is that of main_axes

    # Add a label for the analysis carried out
    plt.text(0.05, # x
             0.76, # y
             r'$H \rightarrow ZZ^* \rightarrow 4\ell$', # text 
             transform=main_axes.transAxes ) # coordinate system used is that of main_axes

    # draw the legend
    main_axes.legend( frameon=False ) # no box around the legend
    plt.savefig("/app/data/output.png")
    print("SAVED FILE")

counter = 0

# Establishing a connection to the RabbitMQ server using the specified parameters
params = pika.ConnectionParameters('year_4_project_2-rabbitmq-1')
connection = pika.BlockingConnection(params)
# Creating a channel for communication with the RabbitMQ server
channel = connection.channel()
# Declaring a queue named 'output' to receive messages
channel.queue_declare(queue='output')
# Setting up a consumer to receive messages from the 'output' queue
# The 'callback' function will be called for each received message
channel.basic_consume(queue='output', auto_ack=True, on_message_callback=callback)
# Start consuming messages from the 'output' queue
channel.start_consuming()

