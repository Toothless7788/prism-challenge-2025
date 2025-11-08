import re
import json
from dateparser.search import search_dates
import spacy
import yfinance as yf
import pandas as pd
import datetime

# Load spaCy model once at module level for efficiency
nlp = spacy.load("en_core_web_sm")

RISK_RATIO = 0.3
BUDGET_RATIO = 0.35

sectors = ["finance", "technology", "life science", "real estate", "energy", "manufacturing"]
tickers = ["JPM", "BAC", "WFC", "PGR", "GS", "AAPL", "MSFT", "NVDA", "GOOG", "AMZN", 
           "ISRG", "AMGN", "GILD", "VRTX", "REGN", "ALNY", "AMT", "PLD", "PSA", "DLR", 
           "UPS", "UNP", "CSX", "LUV", "PAA", "MMM", "CAT", "DE", "AMAT", "GE", "HON"]

map_categories = {
    "Structured Finance": "finance",
    "Finance": "finance",
    "Finance or Crypto Assets": "finance",
    "Technology": "technology",
    "Life Sciences": "life science",
    "Real Estate and Construction": "real estate",
    "Energy and Transportation": "energy",
    "Manufacturing": "manufacturing"
}

symbols = {
    "finance": ["JPM", "BAC", "WFC", "PGR", "GS"],
    "technology": ["AAPL", "MSFT", "NVDA", "GOOG", "AMZN"],
    "life science": ["ISRG", "AMGN", "GILD", "VRTX", "REGN", "ALNY"],
    "real estate": ["AMT", "PLD", "PSA", "DLR"],
    "energy": ["PAA", "UPS", "UNP", "CSX", "LUV"],
    "manufacturing": ["MMM", "CAT", "DE", "AMAT", "GE", "HON"],
}


def analysis1(start_date, end_date, avoid):
    """Analyze stocks and filter by growth rate."""
    invest = {}
    for sector in sectors:
        if sector in avoid:
            continue
        
        temp_tickers = symbols[sector]
        with open("mean.txt", "r") as f:
            data = eval(f.readline())
        
        for ticker in temp_tickers:
            start_year = int(start_date.split("-")[0])
            end_year = int(end_date.split("-")[0])
            if data[ticker][end_year] / data[ticker][start_year] > 1.6:
                invest[ticker] = float(data[ticker][start_year])
    
    return invest


def pack_portfolio(stock_prices: dict, budget: int, risk_level: str):
    """
    Pack portfolio with available budget using greedy algorithm.
    """
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
    """Extract investment preferences using spaCy for NLP processing."""
    doc = nlp(message)
    
    context_dict = {
        "start": None,
        "end": None,
        "age": -1,
        "budget": None,
        "dislikes": [],
        "salary": None, 
        "employed": False
    }
    
    # Extract dates using dateparser
    start_index = message.lower().find("start")
    if start_index == -1:
        start_index = 0
    
    dates = re.findall(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", message[start_index:])
    
    if len(dates) != 2:
        try:
            date_results = search_dates(message[start_index:])
            if date_results:
                dates = [d[1] for d in date_results if 2000 < d[1].year < 2025]
        except (IndexError, TypeError):
            return False
        
        if not dates or len(dates) != 2:
            return False
        context_dict["start"] = dates[0]
        context_dict["end"] = dates[1]
    else:
        context_dict["start"] = datetime.datetime.strptime(dates[0], "%Y-%m-%d")
        context_dict["end"] = datetime.datetime.strptime(dates[1], "%Y-%m-%d")
    
    # Use spaCy for token processing with lemmatization
    tokens = [token for token in doc if not token.is_stop]
    token_texts = [token.text for token in tokens]
    token_lemmas = [token.lemma_ for token in tokens]
    
    # Extract age using spaCy's entity recognition and pattern matching
    for ent in doc.ents:
        if ent.label_ == "DATE" and "year" in ent.text.lower() and "old" in ent.text.lower():
            age_match = re.search(r"(\d+)", ent.text)
            if age_match:
                context_dict["age"] = int(age_match.group(1))
    
    # Fallback age extraction
    if context_dict["age"] == -1:
        for i, token in enumerate(tokens):
            if re.match(r"[0-9]+-year-old", token.text):
                context_dict["age"] = int(token.text.split("-")[0])
            elif token.lemma_ == "year" and i > 0:
                prev_token = tokens[i-1]
                if prev_token.like_num:
                    context_dict["age"] = int(prev_token.text)
    
    # Extract budget using dependency parsing
    for i, token in enumerate(tokens):
        if token.lemma_ in ["budget", "investment"]:
            # Look for numbers near budget keyword
            window = tokens[max(0, i-2):min(len(tokens), i+6)]
            numbers = [t.text for t in window if t.like_num]
            
            if numbers:
                budget_val = int(numbers[0].replace(",", ""))
                context_sentence = message[max(0, token.idx-50):min(len(message), token.idx+100)]
                
                if "per year" in context_sentence.lower():
                    difference = context_dict["end"] - context_dict["start"]
                    y_diff = (difference.days + difference.seconds/86400) / 365.2425
                    context_dict["budget"] = int(budget_val * y_diff)
                else:
                    context_dict["budget"] = budget_val
                break
    
    # Extract total investment (alternative to budget)
    if context_dict["budget"] is None:
        for i, token in enumerate(tokens):
            if token.text.lower() == "total" and i+1 < len(tokens):
                if tokens[i+1].lemma_ == "investment":
                    window = tokens[i:min(len(tokens), i+5)]
                    numbers = [t.text for t in window if t.like_num]
                    if numbers:
                        context_dict["budget"] = int(numbers[0].replace(",", ""))
    
    # Extract dislikes/avoids using dependency parsing
    for i, token in enumerate(tokens):
        if token.lemma_ in ["avoid", "dislike"]:
            # Find the end of the avoid clause (period or comma)
            avoid_end = i + 1
            for j in range(i + 1, len(tokens)):
                if tokens[j].text in [".", ","]:
                    avoid_end = j
                    break
            
            avoid_phrase = [t.text.lower() for t in tokens[i+1:avoid_end] if t.text != ","]
            avoid_text = " ".join(avoid_phrase)
            
            avoid_list = []
            for sector in sectors:
                if re.search(sector, avoid_text):
                    avoid_list.append(sector)
            
            context_dict["dislikes"] = avoid_list
            break
    
    # Format dates
    if isinstance(context_dict["start"], datetime.datetime):
        context_dict["start"] = context_dict["start"].strftime("%Y-%m-%d")
    if isinstance(context_dict["end"], datetime.datetime):
        context_dict["end"] = context_dict["end"].strftime("%Y-%m-%d")
    
    print(f"context_dict: {context_dict}")
    
    # Check if all required fields are present
    if None in [context_dict["start"], context_dict["end"], context_dict["budget"]]:
        return False
    
    return context_dict


def read_pref(context):
    """Read preferences from JSON string."""
    # print(f"context in read_pref: {context}; type: {type(context)}")
    return json.loads(context)


def calculate_risk(age, employed, ratio):
    """Calculate risk level based on age, employment, and budget ratio."""
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
    """Filter stocks by risk level."""
    if risk_level == "medium":
        return prices
    
    if not prices:
        return prices
    
    risks = {}
    start_year = int(start_date.split("-")[0])
    end_year = int(end_date.split("-")[0])
    
    with open("risk.txt", "r") as f:
        data = eval(f.readline())
    
    for ticker in prices:
        risks[ticker] = [data[ticker][i] for i in data[ticker] if start_year <= i <= end_year]
    
    for ticker in risks:
        if risks[ticker]:
            risks[ticker] = sum(risks[ticker]) / len(risks[ticker])
        else:
            risks[ticker] = 0
    
    risks = sorted(list(risks.items()), key=lambda x: x[1])
    n = len(risks)
    
    if risk_level == "low":
        last_index = int((1 - RISK_RATIO) * n)
        filtered_risks = dict(risks[:last_index])
    elif risk_level == "high":
        first_index = int(RISK_RATIO * n)
        filtered_risks = dict(risks[first_index:])
    else:
        return prices
    
    return {p: prices[p] for p in prices if p in filtered_risks}


def compute(message: str | dict):
    """Main computation function for portfolio recommendation."""
    if isinstance(message, str):
        pref = read_pref(message)
    else:
        pref = message

    print(f"pref: {pref}")
    
    if pref:
        to_avoid = [map_categories.get(x, None) for x in pref["dislikes"]]
        to_avoid = [x for x in to_avoid if x is not None]

        print(f"\nto_avoid: {to_avoid}")
        
        prices = analysis1(start_date=pref["start"], end_date=pref["end"], avoid=to_avoid)

        print(f"\nprices: {prices}")
        
        if pref["employed"]:
            # Never run
            risk_ratio = pref["budget"] / pref["salary"]
        else:
            risk_ratio = 0.05
        
        risk_level = calculate_risk(pref["age"], pref["employed"], risk_ratio)

        print(f"risk_level: {risk_level}")

        filtered_prices = filter_by_risk(prices, pref["start"], pref["end"], risk_level)

        print(f"filtered_prices: {filtered_prices}")

        portfolio_dict = pack_portfolio(filtered_prices, pref["budget"], risk_level)
        
        if portfolio_dict:
            return list(portfolio_dict.items())
        else:
            return None
    else:
        return None