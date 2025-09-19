import json
import os
from openai import OpenAI
from dotenv import load_dotenv

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
        stepInformation["Note"] = "This action is the beginning of a sequence of steps."
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
    #These seem to be short, information-sparse clips that make the user experience more smooth. In the use example, however, these aren't really "actions".
    elif step["type"] == "VIDEO":
        stepInformation["Image Url"] = step["url"]
        if "hotspots" in step.keys():
            stepInformation["User Action"] = step["hotspots"][0]["label"]
    coreInformation.append(stepInformation)

# for info in coreInformation:
#     print(info)
#     print("")

#2.) 
load_dotenv()
api_key = os.getenv("API_KEY")
model = OpenAI(api_key = api_key)

responses = []
for info in coreInformation:
    #Since responses are so short, there is no need to use the strongest model.
    response = model.chat.completions.create(
        model = "gpt-4o-mini",
        messages = [
            {"role": "system", "content": "You are an assistant that will concisely refine flow data."},
            {"role": "user", "content": 
            f"""
            Given the json-formatted information regarding an action that a user took on a flow model, 
            return a short, human-readable (5-9 words maximum) summary of what they did. 
            Your summary should be to the point, and provide a clear overview of what the user did, starting with an action verb. Return the response in past tense.

            Here are some examples: Clicked on Wallet Image. Typed in Search Bar. Checked Box for Prices Under 50$. Pressed button to purchase item.
            Do not surround the output in quotes.

            Here is exactly how to process the json data to complete the request:
            First, see if there is a "User Action" field. This action is the MAIN field you need to summarize. 
            If this field does not exist, look to find a "Title," "Subtitle," and "Notes" field. 
            Finally, to learn more details about the action, read the Page Description and Image Url fields. 
            Skim over all other fields.

            Here is an example: 'Image Url': 'test_url.com/image/myimage.png', 'User Action': 'Enter the side menu through clicking the hamburger bar', 'Page Url': 'test_url_2.com', 'Page Description': 'test_url_2.com/wallet_developer_test'

            In this case, you would first read the User Action. Then, you would follow up by reading the Page Description and Image Url. Finally, you would skim through the Page Url.

            This should give you enough information to say (example): "Clicked hamburger menu on wallet page"

            If you are on the edge of adding more versus less context, *add the context.* Make sure to read all information at least once before returning a response. 

            Now, it is your turn. Here is the necessary json data:
            {info}
            """
            }]
    )
    responses.append(response.choices[0].message.content)

refined_list = model.chat.completions.create(
    model = "chatgpt-4o-latest",
    messages = [
        {"role": "system", "content": "You are an assistant that will refine flow data."},
        {"role": "user", "content": 
        f"""
        Given the json-formatted information regarding an action that a user took on a flow model, refine the summary items of user actions. 
        
        Importantly, you should ONLY remove CONTEXT that has been repeated. Your goal is to find this context and remove it so that the text is nicer to read. 

        Here's an example of repeated context that you could remove
        Input:
        [
        "Clicked on wallet image at wallets_test.com"
        "On wallets_test.com, clicked on reviews"
        "Typed review regarding luxury wallet on wallets_test.com" 
        ]
        Output:
        [
        "Clicked on wallet image at wallets_test.com"
        "Clicked on reviews section"
        "Typed review regarding luxury wallet" 
        ]

        Again, only remove REPEATED context. Do not remove words descriptor words. For example, "luxury" above was not removed. 

        Here's another example:
        Input:
        [
        "Clicked on wallet image at wallets_test.com"
        "Clicked on a wallet image at wallets_test.com"
        "User clicks on wallet image at wallets_test.com" 
        ]
        Output:
        [
        Clicked on wallet image at wallets_test.com
        Clicked on wallet image.
        User clicked on wallet image.
        ]
        
        Now, it is your turn. The only things you can do are 
        1.) Remove REPEATED context
        2.) Make the texts EASIER and NICER to read.
        3.) Convert all text to past tense, if it is not already in past tense.

        You may NOT change the amount of items in the list.

        Return the items as bullet points in a markdown list.

        Now, it is your turn. Here is your list:
        {responses}
        """
    }]
)
# 
summarized_markdown = model.chat.completions.create(
    model = "chatgpt-4o-latest",
    messages = [
        {"role": "system", "content": "You are an assistant that will summarize and format user actions into markdown."},
        {"role": "user", "content": 
        f"""

        You will be given a list of user actions that have been nicely formatted into markdown.
        Given this list, you are to add a markdown summary that explains in a concise, readable way what the user did throughout the list actions. 
        Further, you must add the "User Interactions" header to the original input, and the "Summary" header to the summary.

        Here's an example:
        Input: 
        - Clicked on wallet image at wallets_test.com
        - Highlighted description of wallet under image.
        - Highlighted wallet rating.
        - Clicked on section for wallet comments.
        - Typed in wallet question box.
        - Submitted question regarding wallet. 
        Output:
        ##User Interactions
        - Clicked on wallet image at wallets_test.com
        - Highlighted description of wallet under image.
        - Highlighted wallet rating.
        - Clicked on section for wallet comments.
        - Typed in wallet question box.
        - Submitted question regarding wallet. 
        ##User Summary
        The user explored a wallet product page by viewing the image, highlighting key details (description and rating), checking the comments section, and finally typing and submitting a question about the wallet.

        
        Notice how the example summary avoids complex words and overall wordiness.
        Note: You may NOT change the input at all.
        The only things you can do are:
        1.) Give a summary of the user's actions. (must do)
        2.) Add "User Interactions" and "Summary" Headers (must do)
        2.) Make the entire markdown style consistent and visually aesthetic. That is, after deciding what the best style is for the user to visually understand the input, you should apply this style to the entire markdown before returning the result.

        
        Now, it is your turn. Return the original input followed by the user summary in markdown. Here is the input list:
        {responses}
        """
    }]
)
summarized_markdown = summarized_markdown.choices[0].message.content
with open ("./output/summary.md", "w") as f:
    f.write(summarized_markdown) 
