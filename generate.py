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

steps = flowData["steps"]
coreInformation = []
stepsCount = len(steps)
for i, step in enumerate(steps):
    stepInformation = dict()
    id = step["id"]
    if id not in capturedEventsDict.keys() and step["type"] != "CHAPTER":
        continue
    #These generally capture a broad user choice (e.g. starting/restarting activity). This is a good anchor point to begin.
    if step["type"] == "CHAPTER":
        #on last slide, we can exit.
        if i == stepsCount-1: 
            break
        stepInformation["Title"] = step["title"]
        if step["subtitle"]:
            stepInformation["Subtitle"] = step["subtitle"]
        #Assuming there is only one path here for the user, since there is no log in capturedEvents of the user's action.
        if "paths" in step.keys():
            if step["paths"][0]["buttonText"]:
                stepInformation["Next Button - Text"] = "Click Button Text: " + step["paths"][0]["buttonText"]
            if step["paths"][0]["buttonColor"]:
                stepInformation["Next Button - Color"] = "Click Button Color: " + step["paths"][0]["buttonColor"]
    #These seem to often be checkpoints that the user interacts with in some way.
    elif step["type"] == "IMAGE":
        stepInformation["Image Url"] = step["url"]
        if "hotspots" in step.keys():
            stepInformation["User Action"] = step["hotspots"][0]["label"]
        if "pageContext" in step.keys():
            stepInformation["Page Url"] = step["pageContext"]["url"]
            stepInformation["Page Description"] = step["pageContext"]["url"]
        pass
    #These seem to be short, information-sparse clips that make the user experience more smooth.
    elif step["type"] == "VIDEO":
        stepInformation["Image Url"] = step["url"]
        if "hotspots" in step.keys():
            stepInformation["User Action"] = step["hotspots"][0]["label"]
    coreInformation.append(stepInformation)

for info in coreInformation:
    print(info)
    print("")