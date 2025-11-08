import re
import time
import json
from dateparser.search import search_dates
from dateparser import parse
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import yfinance as yf
import pandas as pd
import datetime

BUDGET_RATIO = 0.35
RISK_RATIO = 0.3 # remove RISK_RATIO propotion for filtering the risk

sectors = ["finance", "technology", "life science", "real estate", "energy", "manufacturing"]
tickers = ["JPM", "BAC", "WFC", "PGR", "GS", "AAPL", "MSFT", "NVDA", "GOOG", "AMZN", "ISRG", "AMGN", "GILD", "VRTX", "REGN", "ALNY", "AMT", "PLD", "PSA", "DLR", "UPS", "UNP", "CSX", "LUV", "PAA", "MMM", "CAT", "DE", "AMAT", "GE", "HON"]

map_categories = {"Structured Finance": "finance",
                  "Finance": "finance",
                  "Finance or Crypto Assets": "finance",
                  "Technology": "technology",
                  "Life Sciences": "life sciences",
                  "Real Estate and Construction": "real estate",
                  "Energy and Transportation": "energy",
                  "Manufacturing": "manufacturing"}

symbols = {
    "finance": ["JPM", "BAC", "WFC", "PGR", "GS"],
    "technology": ["AAPL", "MSFT", "NVDA", "GOOG", "AMZN"],
    "life science":["ISRG", "AMGN", "GILD", "VRTX", "REGN", "ALNY"],
    "real estate": ["AMT", "PLD", "PSA", "DLR"],
    "energy": ["PAA", "UPS", "UNP", "CSX", "LUV"],
    "manufacturing": ["MMM", "CAT", "DE", "AMAT", "GE", "HON"],
}

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

def analysis1(start_date, end_date, avoid):
    invest = {}
    for sector in sectors:
        if sector in avoid:
            continue
        else:
            temp_tickers = symbols[sector]
            with open("mean.txt", "r") as f:
                data = eval(f.readline())
            for ticker in temp_tickers:
                start_year = int(start_date.split("-")[0])
                end_year = int(end_date.split("-")[0])
                if data[ticker][end_year]/data[ticker][start_year] > 1.6:
                    invest[ticker] = float(data[ticker][start_year])
            # start_date1 = datetime.datetime.strptime(start_date, "%Y-%m-%d")+datetime.timedelta(days=3)
            # end_date1 = datetime.datetime.strptime(end_date, "%Y-%m-%d")+datetime.timedelta(days=3)
            # try:
            #     open_data = yf.download(" ".join(temp_tickers), start=start_date, end=start_date1.strftime("%Y-%m-%d"), progress=False)
            #     close_data = yf.download(" ".join(temp_tickers), start=end_date, end=end_date1.strftime("%Y-%m-%d"), progress=False)
            #     # print(open_data)
            #     # print(close_data)
            #     if open_data.empty or close_data.empty:
            #         continue
            #     for ticker in open_data['Open']:
            #         open_price = open_data['Close'][ticker].iloc[0]
            #         close_price = close_data['Open'][ticker].iloc[0]
            #         if close_price - open_price > 0:
            #             invest[ticker] = float(open_price)
            # except Exception as e:
            #     pass
    
    # print("INVEST", invest)
    return invest


def pack_portfolio(stock_prices: dict, budget: int):
    portfoio = {}
    remaining_budget = budget*BUDGET_RATIO
    stock_prices = list(stock_prices.items())
    sorted_stocks = sorted(stock_prices, key=lambda x: x[1], reverse=True)
    # print(sorted_stocks)
    n = len(sorted_stocks)
    i = 0
    try:
        while remaining_budget > sorted_stocks[-1][1]: 
            if sorted_stocks[i][1] <= remaining_budget:
                portfoio[sorted_stocks[i][0]] = portfoio.get(sorted_stocks[i][0], 0) + 1
                remaining_budget -= sorted_stocks[i][1]
            i = (i + 1)%n
        # print(remaining_budget)
        return portfoio
    except IndexError:
        return False

def extract_preferences(message: str):
    context_dict = {"start": None, "end": None, "age": -1, "budget": None, "dislikes": [], 
                    "salary": None
                    # "extraction_time": None
                }
    tokens = word_tokenize(message)
    print("TOKENS:", tokens)
    stop_words = set(stopwords.words("english"))
    filtered_words = [word for word in tokens if
                      word.casefold() not in stop_words]
    # print("FILTERED:", filtered_words)
    start_index = " ".join(filtered_words).find("start")
    dates = re.findall(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", " ".join(filtered_words)[start_index:])
    if len(dates) != 2:
        try:
            dates = [d[1] for d in search_dates(" ".join(filtered_words)[start_index:]) if 2000 < d[1].year < 2025]
        except (IndexError, TypeError):
            # print(filtered_words)
            return False
        if len(dates) != 2:
            # print(filtered_words)
            return False
        context_dict["start"] = dates[0]
        context_dict["end"] = dates[1]
    else:
        context_dict["start"] = datetime.datetime.strptime(dates[0], "%Y-%m-%d")
        context_dict["end"] = datetime.datetime.strptime(dates[1], "%Y-%m-%d")
    for i, word in enumerate(filtered_words):
        if re.match(r"[0-9]+-year-old", word):
            context_dict["age"] = int(word.split("-")[0])
        elif word == "years":
            context_dict["age"] = int(filtered_words[i-1])
        elif word == "budget":
            budget_phrase = " ".join(filtered_words[i:i+6])
            budget_val = int([b for b in word_tokenize(budget_phrase) if b.isnumeric()][0])
            print(budget_val)
            if "per year" in budget_phrase:
                difference = context_dict["end"] - context_dict["start"]
                y_diff = (difference.days + difference.seconds/86400)/365.2425
                context_dict["budget"] = int(budget_val*y_diff)
            else:
                context_dict["budget"] = budget_val
        elif word == "total" and filtered_words[i+1] == "investment":
            if "budget" in filtered_words:
                return False
            budget_phrase = filtered_words[i:i+5]
            context_dict["budget"] = int(int(budget_phrase[3]))
        elif word == "avoids" or word == "avoid":
            avoid_phrase = filtered_words[i:]
            split = avoid_phrase.index(".")
            dislikes = [word.lower() for word in avoid_phrase[1:split] if word != ","]
            # print(dislikes)
            avoid_list = []
            for kw in sectors:
                if re.search(kw, " ".join(dislikes)):
                    avoid_list.append(kw)
            context_dict["dislikes"] = avoid_list
        
    # timer_end = time.time()
    # context_dict["extraction_time"] = timer_end-timer_start
    # print(context_dict["start"])
    context_dict["start"] = context_dict["start"].strftime("%Y-%m-%d")
    context_dict["end"] = context_dict["end"].strftime("%Y-%m-%d")
    if not any([d == None for d in list(context_dict.values())]):
        # print(context_dict)
        return context_dict
    else:
        # print("WE CAN'T PARSE: '" + message + "' yet.")
        # print(context_dict)
        return False
    
def read_pref(context):
    return json.loads(context)
 
# print(extract_preferences("Andre Webb is 19 years old, he started investing in 2012-04-11, and his investment end date was 2013-10-08. He enjoys hiking, and he avoids structured finance, life sciences, and finance. He has a true salary of $204,950 per year, and a budget of $10570."))


def calculate_risk(age, employed, ratio):
    if ratio > 0.3:
        return "low"
    if ratio < 0.05:
        return "high"
    if not employed:
        return "low"
    elif age == -1:
        return "medium"
    elif age < 30:
        return "high"
    elif 30 <= age <= 60:
        return "medium" 
    return "low"


def filter_by_risk(prices, start_date, end_date, risk_level):
    # print("PRICES:", prices)
    if risk_level == "medium":
        return prices
    risks = {}
    start_year = int(start_date.split("-")[0])
    end_year = int(end_date.split("-")[0])
    with open("risk.txt", "r") as f:
        data = eval(f.readline())
    for ticker in prices:
        risks[ticker] = [data[ticker][i] for i in data[ticker] if start_year <= i <= end_year]
    for ticker in risks:
        risks[ticker] = sum(risks[ticker])/len(risks[ticker])
    risks = sorted(list(risks.items()), key=lambda x: x[1])
    # print("RISKS:", risks)
    n = len(risks)
    if risk_level == "low":
        last_index = int((1-RISK_RATIO)*n)
        filtered_risks = dict(risks[:last_index])
        return {p: prices[p] for p in prices if p in filtered_risks}
    elif risk_level == "medium":
        index_a = int((RISK_RATIO/2)*n)
        index_b = int(((1-RISK_RATIO)/2)*n)
        filtered_risks = dict(risks[index_a:index_b])
        return {p: prices[p] for p in prices if p in filtered_risks}
    else:
        first_index = int(RISK_RATIO*n)
        filtered_risks = dict(risks[first_index:])
        return {p: prices[p] for p in prices if p in filtered_risks} 
    
def compute(message: str):
    pref = read_pref(message)
    # pref = eval(message)
    if (pref):
        to_avoid = [map_categories.get(x, None) for x in pref["dislikes"]]
        prices = analysis1(start_date=pref["start"], end_date=pref["end"], avoid=to_avoid)
        if pref["employed"]:
            portfolio_dict = pack_portfolio(filter_by_risk(prices, pref["start"], pref["end"], calculate_risk(pref["age"], pref["employed"], pref["budget"]/pref["salary"])), pref["budget"])
        else:
            portfolio_dict = pack_portfolio(filter_by_risk(prices, pref["start"], pref["end"], calculate_risk(pref["age"], pref["employed"], 0)), pref["budget"])
        if portfolio_dict != False:
            return list(portfolio_dict.items())
        else:
            return None
    else:
        return None
    
# print(compute("{'timestamp': '2025-04-06T05:13:05.974400686Z', 'start': '2012-01-01', 'end': '2013-10-16', 'age': 77, 'employed': True, 'salary': 78528, 'budget': 17756, 'dislikes': ['Crypto Assets', 'Real Estate and Construction', 'Trade and Services', 'Finance']}"))


# 
# with open("examples.txt", "r") as f:
#     with open("output.txt", "a") as g:
#         ctxs = f.readlines()
#         for ctx in ctxs:
#             msg = eval(ctx)["message"]
#             pref = extract_preferences(msg)
#             print(pref)
#             # prices = analysis1(start_date=pref["start"], end_date=pref["end"], avoid=pref["dislikes"])
#             # g.write(str(pack_portfolio(prices, pref["budget"])) + "\n")
