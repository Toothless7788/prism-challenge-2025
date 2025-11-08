import os
import json
import logging
import random
import requests
from dotenv import load_dotenv
from PALGO import compute, calculate_risk, extract_preferences
load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(filename='log3.txt', encoding='utf-8', level=logging.DEBUG)

URL = "www.prism-challenge.com"
PORT = 8082

# Please do NOT share this information anywhere, unless you want your team to be cooked.
TEAM_API_CODE = os.getenv("TEAM_API_CODE")
# @cyrus or @myguysai on Discord if you need an API key

def send_get_request(path):
    """
    Sends a HTTP GET request to the server.
    Returns:
        (success?, error or message)
    """
    headers = {"X-API-Code": TEAM_API_CODE}
    response = requests.get(f"http://{URL}:{PORT}/{path}", headers=headers)

    # Check whether there was an error sent from the server.
    # 200 is the HTTP Success status code, so we do not expect any
    # other response code.
    if response.status_code != 200:
        return (
            False,
            f"Error - something went wrong when requesting [CODE: {response.status_code}]: {response.text}",
        )
    return True, response.text


def send_post_request(path, data=None):
    """
    Sends a HTTP POST request to the server.
    Pass in the POST data to data, to send some message.
    Returns:
         (success?, error or message)
    """
    headers = {"X-API-Code": TEAM_API_CODE, "Content-Type": "application/json"}

    # Convert the data from python dictionary to JSON string,
    # which is the expected format to be passed
    data = json.dumps(data)
    response = requests.post(f"http://{URL}:{PORT}/{path}", data=data, headers=headers)

    # Check whether there was an error sent from the server.
    # 200 is the HTTP Success status code, so we do not expect any
    # other response code.
    if response.status_code != 200:
        return (
            False,
            f"Error - something went wrong when requesting [CODE: {response.status_code}]: {response.text}",
        )
    return True, response.text


def get_context():
    """
    Query the challenge server to request for a client to design a portfolio for.
    Returns:
        (success?, error or message)
    """
    return send_get_request("/request")


def get_my_current_information():
    """
    Query your team information.
    Returns:
        (success?, error or message)
    """
    return send_get_request("/info")


def send_portfolio(weighted_stocks):
    """
    Send portfolio stocks to the server for evaluation.
    Returns:
        (success?, error or message)
    """
    # NOTE: Here
    if weighted_stocks:
        data = [
            {"ticker": weighted_stock[0], "quantity": weighted_stock[1]}
            for weighted_stock in weighted_stocks
        ]
        return send_post_request("/submit", data=data)
    else:
        return (True, "Not sent")

while True:
    success, context = get_context()
    if not success:
        logging.error(f"Error: {context}")
        exit(-1)

    print(f"==================")
    print(f"Context received: {context}")

    with open("log3.txt", "at") as f:
        try:
            input_message = json.loads(context)["message"]
            print("INPUT MESSAGE:", input_message)
            input_message = extract_preferences(input_message)
            print(f"\ninput_message: {input_message}")

            if input_message is False:
                f.write(f"Preferences extraction failed for context: {context}\n")
                print("Failed to extract preferences. See log3.txt for details.")
                continue

            portfolio = compute(input_message)
        except Exception as e:
            f.write(f"Error during extraction/computation: {e}\n")
            print(f"Error: {e}\n")
            continue

        print(f"portfolio: {portfolio}")
        print(f'portfolio value: {sum([p[1] for p in portfolio])}')
        success, response = send_portfolio(portfolio)
        if not success:
            f.write(f"Error: {response}\n")
            f.write(f"Evaluation response: {response}\n")
            continue
        f.write(f"Evaluation response: {response}\n")
        ctx = json.loads(context)
        try:
            f.write("RISK:" + str(calculate_risk(input_message["age"], input_message["employed"], input_message.get("budget", 0))) + "\n")
        except ZeroDivisionError:
            f.write("RISK:" + str(calculate_risk(input_message["age"], input_message["employed"], 0)) + "\n")
            pass
        f.write("PORTF:" + str(portfolio) + "\n")
# if __name__ == "__main__":
#     print(f"Running main.py")

#     while True:
#         success, context = get_context()
#         if not success:
#             logging.error(f"Error: {context}")
#             exit(-1)

#         print(f"==================")
#         print(f"Context received: {context}")

#         with open("log3.txt", "at") as f:
#             try:
#                 input_message = eval(context)["message"]

#                 # Process input_message
#                 input_message = extract_preferences(input_message)

#                 print(f"\ninput_message: {input_message}")

#                 if input_message == False:
#                     print("Failed to extract preferences")
#                     f.write("ERROR: Failed to extract preferences\n")
#                     continue  # Changed from exit() to continue

#                 portfolio = compute(input_message)
                
#                 # Check if portfolio is None
#                 if portfolio is None:
#                     print("ERROR: Portfolio is None - failed to generate portfolio")
#                     f.write("ERROR: Portfolio generation failed\n")
#                     continue  # Changed from exit(-1) to continue
                
#                 print(f"portfolio: {portfolio}")
                
#                 # Now safe to calculate portfolio value
#                 portfolio_value = sum([p[1] for p in portfolio])
#                 print(f'portfolio value: {portfolio_value}')

#                 success, response = send_portfolio(portfolio)

#                 # REMOVED: exit(-1)  <-- This was causing it to exit after each buy

#                 # Logging
#                 if not success:
#                     f.write(f"Error: {response}\n")
#                     f.write(f"Evaluation response: {response}\n")
#                     continue
                    
#                 f.write(f"Evaluation response: {response}\n")
                
#                 try:
#                     ctx = input_message  # Use the extracted preferences instead of re-parsing
#                     if ctx.get("salary") and ctx.get("salary") > 0:
#                         f.write("BUDG/SAL:" + str(ctx["budget"]/ctx["salary"]) + "\n")
#                         f.write("RISK:" + str(calculate_risk(ctx["age"], ctx.get("employed", False), ctx["budget"]/ctx["salary"])) + "\n")
#                     else:
#                         f.write("RISK:" + str(calculate_risk(ctx["age"], ctx.get("employed", False), 0)) + "\n")
#                 except (ZeroDivisionError, KeyError) as e:
#                     f.write(f"RISK: Could not calculate - {e}\n")
                    
#                 f.write("PORTF:" + str(portfolio) + "\n")
                
#             except Exception as e:
#                 print(f"Error: {e}")
#                 import traceback
#                 traceback.print_exc()
#                 f.write(f"Exception occurred: {e}\n")
#                 continue  # Changed from exit(-1) to continue
