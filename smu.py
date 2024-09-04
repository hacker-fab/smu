from WF_SDK import device, scope, wavegen   # import instruments

import matplotlib.pyplot as plt   # needed for plotting

import csv #needed for generating CSV files for graphing later
import ctypes
from sys import platform, path    # this is needed to check the OS type and get the PATH
from os import sep                # OS specific file path separators
 
"""-----------------------------------------------------------------------"""
# assign dwf to be used later
# load the dynamic library, get constants path (the path is OS specific)
if platform.startswith("win"):
    # on Windows
    dwf = ctypes.cdll.dwf
    constants_path = "C:" + sep + "Program Files (x86)" + sep + "Digilent" + sep + "WaveFormsSDK" + sep + "samples" + sep + "py"
elif platform.startswith("darwin"):
    # on macOS
    lib_path = sep + "Library" + sep + "Frameworks" + sep + "dwf.framework" + sep + "dwf"
    dwf = ctypes.cdll.LoadLibrary(lib_path)
    constants_path = sep + "Applications" + sep + "WaveForms.app" + sep + "Contents" + sep + "Resources" + sep + "SDK" + sep + "samples" + sep + "py"
else:
    # on Linux
    dwf = ctypes.cdll.LoadLibrary("libdwf.so")
    constants_path = sep + "usr" + sep + "share" + sep + "digilent" + sep + "waveforms" + sep + "samples" + sep + "py"

# import constants
path.append(constants_path)
 
drain_resistance = 100#float(input("Enter the resistance in Ohms of the resistor in series with the mosfet DRAIN: "))
gate_resistance = 100#float(input("Enter the resistance in Ohms of the resistor in series with the mosfet GATE: "))
chip_number = "305"#input("Enter your chip number (ex. 305): ")
device_id = "2b1"#input("Enter the device being tested (ex. 2b1): ")
gate_voltages = input("Enter the gate voltages to test as a comma-separated list (Ex. 1, 1.5, 1.6, 3): ").replace(" ", "").split(",")
# name of csv files
filename_currents = f"csvfiles/{chip_number}_{device_id}_currents.csv"
filename_voltages = f"csvfiles/{chip_number}_{device_id}_voltages.csv"
# connect to the device
ad3_data1 = device.open() #open the first analog discovery 3 to measure Id and Vds
#ad3_data2 = device.open() #open the second analog discovery 3 to measure Ig and Vds
#ad3_data3 = device.open() #open the third analog discovery 3 to measure Ib and Vds TODO
 
"""-----------------------------------"""

# writing to csv file  
for filename in [filename_currents, filename_voltages]:
    with open(filename, 'w') as csvfile: # opens csv files
        csvwriter = csv.writer(csvfile)  # creating a csv writer object 
        csvwriter.writerow(gate_voltages) # writes header row (gate voltages)
 
# initialize the scope with default settings
scope.open(ad3_data1, sampling_frequency=10e5)

wavegen.generate(ad3_data1, channel=1, function=wavegen.function.sine, offset=5, frequency=100, amplitude=5) #generation sine waveform to drain

#set voltage peak to peak input range to 50 V on both channels
dwf.FDwfAnalogInChannelRangeSet(ad3_data1.handle, 0, ctypes.c_double(50.0))
dwf.FDwfAnalogInChannelRangeSet(ad3_data1.handle, 1, ctypes.c_double(50.0))

# generate a 10KHz sine signal with 2V amplitude on channel 1
current_dict = {}
volt_dict = {}
#for VB in body_voltages: #TODO loop through body as well
for VG in gate_voltages:
    VG = float(VG)
    wavegen.generate(ad3_data1, channel=2, function=wavegen.function.dc, offset=VG, frequency=10e2, amplitude=1) #generate dc signal to gate voltage at voltage i
    [drain_voltages, ds_voltages1] = scope.record2(ad3_data1) # get data with first AD3 oscilloscope
    #[gate_voltages, ds_voltages2] = scope.record2(ad3_data2) # get data with second AD3 oscilloscope
    drain_currents = []
    gate_currents = []
    for i in range(len(drain_voltages)):
        drain_currents.append(drain_voltages[i]/drain_resistance) # calculate current with ohms law
        #gate_currents.append(gate_voltages[i]/gate_resistance) # calculate current with ohms law
    for filename in [filename_currents, filename_voltages]: #outputs currents and voltages to csv TODO add second AD3 data maybe to XLS
        with open(filename,'a') as csvfile:
            writer = csv.writer(csvfile)
            if "current" in filename:
                writer.writerow(drain_currents)
            elif "voltage" in filename:
                writer.writerow(ds_voltages1)
    plt.plot(ds_voltages1, drain_currents, label = f"Id with Vg = {VG}") #plot curve of Id vs. Vds    
    #plt.plot(ds_voltages2, gate_currents, label = f"Ig with Vg = {VG}") #plot curve of Id vs. Vds   
    #TODO figure out how to 3d plot agains Ib as well 


#plot labels and show
leg = plt.legend(loc='upper center')
#plt.xlim(0, 10)
#plt.ylim(-0.001, 0.03)
plt.xlabel("Voltage (V_DS) [V]")
plt.ylabel("Current [A]")
plt.show()

#TODO only save data to csv if plot looks good

# reset the scope
scope.close(ad3_data1)
 
# reset the wavegen
wavegen.close(ad3_data1)
 
# close the connection
device.close(ad3_data1)