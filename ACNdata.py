import json
import numpy as np
import requests
# Opening JSON file
with open('ThousansSessions.txt') as json_file:
    data = json.load(json_file)
    ignored_values = set(["null", "", None])
    data = [elem for elem in data['_items'] if elem['doneChargingTime'] and  elem['userID'] not in ignored_values]
    scenario = "L"
    max_n = 1000
    step_n = 50
    start_n = 100
    reps = 40
    capacity = 1000000
    dump_dir = "results/dump/"
    name = "EV2[%s]__fixed_int_max_n=%d_step_n=%d_start_n=%d_reps=%d_capacity=%d" % (
        scenario, max_n, step_n, start_n, reps, capacity)
    x=5
    #np.savez(dump_dir + name ,x)
    print(dump_dir + name)
    np.savez(dump_dir + name,x)



    # Print the type of data variable
    # print("Type:", type(data))
    #EnergyReq = (float(json.dumps(data[999]["userInputs"][0]["kWhRequested"])) * 1000) / (
     #           (float(json.dumps(data[999]["userInputs"][0]["minutesAvailable"]))) / 60)
    #print(EnergyReq)
    # Print the data of dictionary
    #Hours = list(range(1000))
    #Minutes = []
    # print d['connectionTime']
    # print(data['session1'])
    # Hours_done= json.dumps(data['_items'][100]["connectionTime"][17:19])
    # Hours_done= Hours_done.strip('""')
    # Hours_done=float(Hours_done)
    # Minutes_done= json.dumps(data['_items'][100]["connectionTime"][20:22])
    # Minutes_done= Minutes_done.strip('""')
    # Minutes_done=float(Minutes_done)
    # StartSession=int((int((Hours/.25))+(Minutes+15)/15))
    # doneSession_done=int((int((Hours_done/.25))+(Minutes_done+15)/15))
    #for k in np.arange(1):
     #   print(k)
    #Hours_done = json.dumps(data[4]["doneChargingTime"][17:19])
    #Hours_done = Hours_done.strip('""')
    #Hours_done = float(Hours_done)
    #Minutes_done = json.dumps(data[4]["doneChargingTime"][20:22])
    #Minutes_done = Minutes_done.strip('""')
   # Minutes_done = float(Minutes_done)
        # ins.customer_charge_start_at_time[k] = int((int((Hours[k] / step_length)) + (Minutes[k] + 15) / 15))  # 15 MINUTES
# print(float(Hours_done))

# print(float(Minutes_done))
# print(float(doneSession_done))
#customer_usage = (float(json.dumps(data['_items'][1]["userInputs"][0]["kWhRequested"])))
 #/ (
            #(float(json.dumps(data['_items'][1]["userInputs"][1]["minutesAvailable"]))) / 60)

#print(customer_usage)


# print(type(json.dumps(data['_items'][0]["connectionTime"][17:19])))
