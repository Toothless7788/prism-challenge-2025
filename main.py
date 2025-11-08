import os
import json
import logging
import requests
from dotenv import load_dotenv
from prevalgo import compute, calculate_risk
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
    # NOTE: Mocking
    mock_context = '{"message":"Christopher Avila is a 67-year-old investor who started investing in 2011-07-01 and ended it on 2014-06-11. His hobbies include learning languages, and he avoids finance or crypto assets. He has a total budget of $23215."}'
    return (True, mock_context)

    # return send_get_request("/request")


def get_my_current_information():
    """
    Query your team information.
    Returns:
        (success?, error or message)
    """
    # NOTE: Mocking
    mock_information = ""
    return (True, mock_information)

    # return send_get_request("/info")


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

if __name__ == "__main__":
    print(f"Running main.py")

    # success, information = get_my_current_information()
    # if not success:
    #     logging.error(f"Error: {information}")
    # logging.info(f"Team information: ", information)

    # NOTE: Here
    while True:
        success, context = get_context()
        if not success:
            logging.error(f"Error: {context}")
            exit(-1)

        # logging.info(f"Context provided: ", context)
        print(f"==================")
        print(f"Context received: {context}")

        # logging.debug(compute(eval(context)["message"]))

        # Maybe do something with the context to generate this?
        with open("log3.txt", "at") as f:
            # f.write(eval(context)["message"] + "\n")
            # f.write("PARSED: " + str(extract_preferences(eval(context)["message"])) + "\n")
            try:
                input_message = eval(context)["message"]

                # NOTE: ok
                print(f"input_message: {input_message}")

                # TODO: Process input_message
                input_message = ""

                portfolio = compute(input_message)
            except Exception as e:
                print(f"Error: {e}")

                exit(-1)
                
            print(f"portfolio: {portfolio}")

            success, response = send_portfolio(portfolio)

            # TODO: Temp
            exit(-1)

            # Logging

            if not success:
                f.write(f"Error: {response}\n")
                f.write(f"Evaluation response: {response}\n")
                continue
            f.write(f"Evaluation response: {response}\n")
            ctx = json.loads(eval(context)["message"])
            try:
                f.write("BUDG/SAL:" + str(ctx["budget"]/ctx["salary"]) + "\n")
                f.write("RISK:" + str(calculate_risk(ctx["age"], ctx["employed"], ctx["budget"]/ctx["salary"])) + "\n")

            except ZeroDivisionError:
                f.write("RISK:" + str(calculate_risk(ctx["age"], ctx["employed"], 0)) + "\n")
                pass      
            f.write("PORTF:" + str(portfolio) + "\n")
