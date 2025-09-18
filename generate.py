import json
#1.) Extract all key information from flow.json. 
flowData = dict()
with open ("./data/flow.json", "r") as f:
    flowData = json.load(f)
#First, we want to easily reference the capturedEvents by ID by creating a dict
capturedEvents = flowData["capturedEvents"]
capturedEventsDict = dict()
for event in capturedEvents:
    idKey = event["type"] + "Id" 
    if idKey not in event.keys():
        #Edge case where the type + Id formula doesn't work.
        idKey = [key for key, value in event.items() if key[-2:] == "Id" and key != "frameId"][0]
        #Time, position are too low-level to keep here.
    capturedEventsDict[event[idKey]] = event["type"]
print(capturedEventsDict)
