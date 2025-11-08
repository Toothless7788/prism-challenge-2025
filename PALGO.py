# import re
# import json
# from dateparser.search import search_dates
# import spacy
# import yfinance as yf
# import pandas as pd
# import datetime

# # Load spaCy model once
# nlp = spacy.load("en_core_web_sm")

# RISK_RATIO = 0.3
# MAX_SECTOR_ALLOCATION = 0.4


# sectors = ["finance", "technology", "life science", "real estate", "energy", "manufacturing"]
# tickers = ["JPM", "BAC", "WFC", "PGR", "GS", "AAPL", "MSFT", "NVDA", "GOOG", "AMZN", 
#            "ISRG", "AMGN", "GILD", "VRTX", "REGN", "ALNY", "AMT", "PLD", "PSA", "DLR", 
#            "UPS", "UNP", "CSX", "LUV", "PAA", "MMM", "CAT", "DE", "AMAT", "GE", "HON"]

# map_categories = {
#     "structured finance": "finance",
#     "finance": "finance",
#     "crypto assets": "finance",
#     "finance or crypto assets": "finance",
#     "technology": "technology",
#     "life sciences": "life science",
#     "real estate": "real estate",
#     "real estate and construction": "real estate",
#     "energy": "energy",
#     "energy and transportation": "energy",
#     "manufacturing": "manufacturing",
# }

# symbols = {
#     "finance": ["JPM", "BAC", "WFC", "PGR", "GS"],
#     "technology": ["AAPL", "MSFT", "NVDA", "GOOG", "AMZN"],
#     "life science": ["ISRG", "AMGN", "GILD", "VRTX", "REGN", "ALNY"],
#     "real estate": ["AMT", "PLD", "PSA", "DLR"],
#     "energy": ["PAA", "UPS", "UNP", "CSX", "LUV"],
#     "manufacturing": ["MMM", "CAT", "DE", "AMAT", "GE", "HON"],
# }

# def analysis1(start_date, end_date, avoid):
#     """Analyze stocks and filter by growth rate."""
#     invest = {}
#     sector_stocks = {}  # Track which stocks belong to which sector
    
#     for sector in sectors:
#         if sector in avoid:
#             continue
        
#         temp_tickers = symbols[sector]
#         with open("mean.txt", "r") as f:
#             data = eval(f.readline())
        
#         for ticker in temp_tickers:
#             start_year = int(start_date.split("-")[0])
#             end_year = int(end_date.split("-")[0])
#             if data[ticker][end_year] / data[ticker][start_year] > 1.6:
#                 invest[ticker] = float(data[ticker][start_year])
#                 sector_stocks[ticker] = sector
    
#     return invest, sector_stocks

# # 
# def extract_preferences(message: str):
#     """Extract investment preferences using spaCy for NLP processing."""
#     doc = nlp(message)
    
#     context_dict = {
#         "start": None,
#         "end": None,
#         "age": -1,
#         "budget": None,
#         "dislikes": [],
#         "salary": None,
#         "employed": False
#     }
    
#     # Extract dates using dateparser
#     start_index = message.lower().find("start")
#     if start_index == -1:
#         start_index = 0
    
#     dates = re.findall(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", message[start_index:])
    
#     if len(dates) != 2:
#         try:
#             date_results = search_dates(message[start_index:])
#             if date_results:
#                 dates = [d[1] for d in date_results if 2000 < d[1].year < 2025]
#         except (IndexError, TypeError):
#             return False
        
#         if not dates or len(dates) != 2:
#             return False
#         context_dict["start"] = dates[0]
#         context_dict["end"] = dates[1]
#     else:
#         context_dict["start"] = datetime.datetime.strptime(dates[0], "%Y-%m-%d")
#         context_dict["end"] = datetime.datetime.strptime(dates[1], "%Y-%m-%d")
    
#     # Use spaCy for token processing with lemmatization
#     tokens = [token for token in doc if not token.is_stop]
#     token_texts = [token.text for token in tokens]
#     token_lemmas = [token.lemma_ for token in tokens]
    
#     # Extract age using spaCy's entity recognition and pattern matching
#     for ent in doc.ents:
#         if ent.label_ == "DATE" and "year" in ent.text.lower() and "old" in ent.text.lower():
#             age_match = re.search(r"(\d+)", ent.text)
#             if age_match:
#                 context_dict["age"] = int(age_match.group(1))
    
#     # Fallback age extraction
#     if context_dict["age"] == -1:
#         for i, token in enumerate(tokens):
#             if re.match(r"[0-9]+-year-old", token.text):
#                 context_dict["age"] = int(token.text.split("-")[0])
#             elif token.lemma_ == "year" and i > 0:
#                 prev_token = tokens[i-1]
#                 if prev_token.like_num:
#                     context_dict["age"] = int(prev_token.text)
    
#     # Extract salary first (before budget, as budget might reference salary)
#     for i, token in enumerate(tokens):
#         if token.lemma_ in ["salary", "income", "earn"]:
#             context_dict["employed"] = True
#             window = tokens[max(0, i-2):min(len(tokens), i+6)]
#             numbers = [t.text for t in window if t.like_num]
#             if numbers:
#                 context_dict["salary"] = int(numbers[0].replace(",", ""))
#                 break
    
#     # Also check for "true salary" pattern
#     if context_dict["salary"] is None:
#         salary_match = re.search(r"(?:true )?salary.*?\$?([0-9,]+)", message, re.IGNORECASE)
#         if salary_match:
#             context_dict["salary"] = int(salary_match.group(1).replace(",", ""))
#             context_dict["employed"] = True
    
#     # Extract budget using dependency parsing
#     for i, token in enumerate(tokens):
#         if token.lemma_ in ["budget", "investment"]:
#             # Look for numbers near budget keyword
#             window = tokens[max(0, i-2):min(len(tokens), i+6)]
#             numbers = [t.text for t in window if t.like_num]
            
#             if numbers:
#                 budget_val = int(numbers[0].replace(",", ""))
#                 context_sentence = message[max(0, token.idx-50):min(len(message), token.idx+100)]
                
#                 if "per year" in context_sentence.lower():
#                     difference = context_dict["end"] - context_dict["start"]
#                     y_diff = (difference.days + difference.seconds/86400) / 365.2425
#                     context_dict["budget"] = int(budget_val * y_diff)
#                 else:
#                     context_dict["budget"] = budget_val
#                 break
    
#     # Extract total investment (alternative to budget)
#     if context_dict["budget"] is None:
#         for i, token in enumerate(tokens):
#             if token.text.lower() == "total" and i+1 < len(tokens):
#                 if tokens[i+1].lemma_ in ["investment", "budget"]:
#                     window = tokens[i:min(len(tokens), i+5)]
#                     numbers = [t.text for t in window if t.like_num]
#                     if numbers:
#                         context_dict["budget"] = int(numbers[0].replace(",", ""))
    
#     # Extract dislikes/avoids using dependency parsing
#     for i, token in enumerate(tokens):
#         if token.lemma_ in ["avoid", "dislike"]:
#             # Find the end of the avoid clause (period or comma)
#             avoid_end = i + 1
#             for j in range(i + 1, len(tokens)):
#                 if tokens[j].text in [".", ","]:
#                     avoid_end = j
#                     break
            
#             avoid_phrase = [t.text.lower() for t in tokens[i+1:avoid_end] if t.text != ","]
#             avoid_text = " ".join(avoid_phrase)
            
#             avoid_list = []
#             for sector in sectors:
#                 if re.search(sector, avoid_text):
#                     avoid_list.append(sector)
            
#             context_dict["dislikes"] = avoid_list
#             break
    
#     # Format dates
#     if isinstance(context_dict["start"], datetime.datetime):
#         context_dict["start"] = context_dict["start"].strftime("%Y-%m-%d")
#     if isinstance(context_dict["end"], datetime.datetime):
#         context_dict["end"] = context_dict["end"].strftime("%Y-%m-%d")
    
#     print(f"context_dict: {context_dict}")
    
#     # Check if all required fields are present
#     if None in [context_dict["start"], context_dict["end"], context_dict["budget"]]:
#         return False
    
#     return context_dict


# def read_pref(context):
#     """Read preferences from JSON string."""
#     return json.loads(context)


# def calculate_risk(age, employed, ratio):
#     """Calculate risk level based on age, employment, and budget ratio."""
#     # More conservative risk calculation
#     if ratio > 0.25:  # Changed from 0.3
#         return "low"
#     if ratio < 0.05:
#         return "high"
#     if not employed:
#         return "low"
#     elif age == -1:
#         return "medium"
#     elif age < 35:  # Changed from 30
#         return "high"
#     elif 35 <= age <= 55:  # Narrower medium range
#         return "medium"
#     return "low"


# def filter_by_risk(prices, sector_map, start_date, end_date, risk_level):
#     """Filter stocks by risk level."""
#     if risk_level == "medium":
#         return prices
    
#     if not prices:
#         return prices
    
#     risks = {}
#     start_year = int(start_date.split("-")[0])
#     end_year = int(end_date.split("-")[0])
    
#     with open("risk.txt", "r") as f:
#         data = eval(f.readline())
    
#     for ticker in prices:
#         risks[ticker] = [data[ticker][i] for i in data[ticker] if start_year <= i <= end_year]
    
#     for ticker in risks:
#         if risks[ticker]:
#             risks[ticker] = sum(risks[ticker]) / len(risks[ticker])
#         else:
#             risks[ticker] = 0
    
#     risks = sorted(list(risks.items()), key=lambda x: x[1])
#     n = len(risks)
#     risk_thresholds = {
#         "low": 0.4,    # Take bottom 40% (lowest risk)
#         "high": 0.6    # Take top 40% (highest risk)
#     }
#     if risk_level == "low":
#         last_index = int((1 - risk_thresholds["low"]) * n)
#         filtered_risks = dict(risks[:last_index])
#     elif risk_level == "high":
#         first_index = int(risk_thresholds["high"] * n)
#         filtered_risks = dict(risks[first_index:])
#     else:
#         return prices
    
#     return {p: prices[p] for p in prices if p in filtered_risks}


# def compute(message: str | dict):
#     """Main computation function for portfolio recommendation."""
#     if isinstance(message, str):
#         pref = read_pref(message)
#     else:
#         pref = message

#     print(f"pref: {pref}")
    
#     if not pref:
#         print("Error: No preferences provided")
#         return None
    
#     try:
#         to_avoid = [map_categories.get(x, None) for x in pref.get("dislikes", [])]
#         to_avoid = [x for x in to_avoid if x is not None]
        
#         prices, sector_map = analysis1(start_date=pref["start"], end_date=pref["end"], avoid=to_avoid)
        
#         if not prices:
#             print("Error: No stocks passed growth filter")
#             return None
        
#         # Handle missing 'employed' and 'salary' fields
#         employed = pref.get("employed", False)
#         salary = pref.get("salary", 0)
        
#         if employed and salary and salary > 0:
#             risk_ratio = pref["budget"] / salary
#         else:
#             risk_ratio = 0
        
#         risk_level = calculate_risk(pref.get("age", -1), employed, risk_ratio)
#         print(f"Calculated risk level: {risk_level}")
        
#         filtered_prices = filter_by_risk(prices, sector_map, pref["start"], pref["end"], risk_level)
        
#         if not filtered_prices:
#             print("Error: No stocks passed risk filter")
#             return None
        
#         portfolio_dict = pack_portfolio(filtered_prices, sector_map, pref["budget"], risk_level)
        
#         if portfolio_dict:
#             return list(portfolio_dict.items())
#         else:
#             print("Error: Portfolio packing failed")
#             return None
            
#     except Exception as e:
#         print(f"Error in compute: {e}")
#         import traceback
#         traceback.print_exc()
#         return None


# def pack_portfolio(stock_prices: dict, sector_map: dict, budget: int, risk_level: str):
#     """
#     Pack portfolio with diversification constraints.
#     Returns portfolio dict or None if insufficient stocks.
#     """
#     if not stock_prices or len(stock_prices) < 3:
#         print(f"Insufficient stocks available: {len(stock_prices) if stock_prices else 0}")
#         return None
    
#     risk_budget_ratios = {
#         "low": 0.30,      # Use 30% for low risk (was 35%)
#         "medium": 0.50,   # Use 50% for medium risk (was 60%)
#         "high": 0.70      # Use 70% for high risk (was 85%)
#     }
#     budget_ratio = risk_budget_ratios.get(risk_level, 0.30)
    
#     portfolio = {}
#     sector_allocations = {}
#     total_budget = budget * budget_ratio
#     remaining_budget = total_budget
    
#     # Sort stocks by price (cheapest first for better packing)
#     sorted_stocks = sorted(stock_prices.items(), key=lambda x: x[1])
    
#     # Get unique sectors available
#     available_sectors = list(set(sector_map.values()))
#     min_sectors = min(3, len(available_sectors))  # Try to use at least 3 sectors
    
#     # Calculate sector budgets
#     sector_budgets = {}
#     for sector in available_sectors:
#         sector_budgets[sector] = 0
    
#     # First pass: ensure minimum diversity by buying at least one stock per sector
#     sectors_used = set()
#     for ticker, price in sorted_stocks:
#         sector = sector_map[ticker]
#         if sector not in sectors_used and price <= remaining_budget:
#             portfolio[ticker] = 1
#             remaining_budget -= price
#             sectors_used.add(sector)
#             sector_allocations[sector] = price
            
#             if len(sectors_used) >= min_sectors:
#                 break
    
#     if len(sectors_used) < min_sectors and len(sectors_used) > 0:
#         # Not enough sectors, but we have some stocks
#         print(f"Warning: Only {len(sectors_used)} sectors available (target: {min_sectors})")
#     elif len(sectors_used) == 0:
#         print("Error: Could not allocate any stocks")
#         return None
    
#     # Second pass: fill remaining budget with diversification constraints
#     max_sector_budget = total_budget * MAX_SECTOR_ALLOCATION
#     attempts = 0
#     max_attempts = len(sorted_stocks) * 10
    
#     i = 0
#     while remaining_budget > sorted_stocks[0][1] and attempts < max_attempts:
#         ticker, price = sorted_stocks[i % len(sorted_stocks)]
#         sector = sector_map[ticker]
        
#         # Check if adding this stock would exceed sector allocation
#         current_sector_allocation = sector_allocations.get(sector, 0)
        
#         if price <= remaining_budget and (current_sector_allocation + price) <= max_sector_budget:
#             portfolio[ticker] = portfolio.get(ticker, 0) + 1
#             remaining_budget -= price
#             sector_allocations[sector] = current_sector_allocation + price
        
#         i += 1
#         attempts += 1
    
#     # Verify portfolio is valid
#     if not portfolio:
#         print("Error: Portfolio is empty after packing")
#         return None
    
#     # Calculate actual allocation percentages
#     total_invested = sum(stock_prices[t] * q for t, q in portfolio.items())
#     print(f"Portfolio diversity: {len(sectors_used)} sectors, {len(portfolio)} stocks")
#     print(f"Budget used: ${total_invested:,.2f} / ${total_budget:,.2f} ({total_invested/total_budget*100:.1f}%)")
    
#     return portfolio

import re
import json
from dateparser.search import search_dates
import spacy
import yfinance as yf
import pandas as pd
import datetime

# Load spaCy model once
nlp = spacy.load("en_core_web_sm")

RISK_RATIO = 0.3
MAX_SECTOR_ALLOCATION = 0.5  # Added missing constant

sectors = ["finance", "technology", "life science", "real estate", "energy", "manufacturing"]
tickers = ["JPM", "BAC", "WFC", "PGR", "GS", "AAPL", "MSFT", "NVDA", "GOOG", "AMZN", 
           "ISRG", "AMGN", "GILD", "VRTX", "REGN", "ALNY", "AMT", "PLD", "PSA", "DLR", 
           "UPS", "UNP", "CSX", "LUV", "PAA", "MMM", "CAT", "DE", "AMAT", "GE", "HON"]

map_categories = {
    "structured finance": "finance",
    "finance": "finance",
    "crypto assets": "finance",
    "finance or crypto assets": "finance",
    "technology": "technology",
    "life sciences": "life science",
    "real estate": "real estate",
    "real estate and construction": "real estate",
    "energy": "energy",
    "energy and transportation": "energy",
    "manufacturing": "manufacturing",
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
    sector_stocks = {}
    
    for sector in sectors:
        if sector in avoid:
            continue
        
        temp_tickers = symbols[sector]
        with open("mean.txt", "r") as f:
            data = eval(f.readline())
        
        for ticker in temp_tickers:
            start_year = int(start_date.split("-")[0])
            end_year = int(end_date.split("-")[0])
            # FIXED: Lowered growth threshold from 1.6 to 1.2 (20% growth instead of 60%)
            if data[ticker][end_year] / data[ticker][start_year] > 1.20:
                invest[ticker] = float(data[ticker][start_year])
                sector_stocks[ticker] = sector
    
    return invest, sector_stocks

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
    
    # FIXED: Better budget extraction - look for all dollar amounts
    budget_patterns = [
        r"\$\s*([0-9,]+)",  # $92712 or $92,712
        r"([0-9,]+)\s*(?:dollars|total|budget)",  # 92712 dollars
    ]
    
    for pattern in budget_patterns:
        matches = re.findall(pattern, message, re.IGNORECASE)
        if matches:
            # Take the largest number found (likely the budget)
            amounts = [int(m.replace(",", "")) for m in matches]
            context_dict["budget"] = max(amounts)
            break
    
    # Check if budget is per year
    if context_dict["budget"] and "per year" in message.lower():
        difference = context_dict["end"] - context_dict["start"]
        y_diff = (difference.days + difference.seconds/86400) / 365.2425
        context_dict["budget"] = int(context_dict["budget"] * y_diff)
    
    # Extract salary
    salary_match = re.search(r"(?:true )?salary.*?\$?\s*([0-9,]+)", message, re.IGNORECASE)
    if salary_match:
        context_dict["salary"] = int(salary_match.group(1).replace(",", ""))
        context_dict["employed"] = True
    
    # Extract dislikes/avoids
    for i, token in enumerate(tokens):
        if token.lemma_ in ["avoid", "dislike"]:
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
    return json.loads(context)


def calculate_risk(age, employed, ratio):
    """Calculate risk level based on age, employment, and budget ratio."""
    if ratio > 0.25:
        return "low"
    if ratio < 0.05:
        return "high"
    if not employed:
        return "low"
    elif age == -1:
        return "medium"
    elif age < 35:
        return "high"
    elif 35 <= age <= 55:
        return "medium"
    return "low"


def filter_by_risk(prices, sector_map, start_date, end_date, risk_level):
    """Filter stocks by risk level."""
    if risk_level == "medium":
        return prices
    
    if not prices:
        return prices
    
    # FIXED: If we have very few stocks, don't filter by risk
    if len(prices) <= 5:
        print(f"Warning: Only {len(prices)} stocks available, skipping risk filter")
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
    
    # FIXED: Map risk levels to numeric thresholds
    risk_thresholds = {
        "low": 0.5,    # Take bottom 50% (lowest risk)
        "high": 0.5    # Take top 50% (highest risk)
    }
    
    if risk_level == "low":
        last_index = max(3, int(risk_thresholds["low"] * n))  # At least 3 stocks
        filtered_risks = dict(risks[:last_index])
    elif risk_level == "high":
        first_index = max(0, int((1 - risk_thresholds["high"]) * n))
        filtered_risks = dict(risks[first_index:])
    else:
        return prices
    
    result = {p: prices[p] for p in prices if p in filtered_risks}
    
    # FIXED: If filtering removed too many stocks, return original
    if len(result) < 3:
        print(f"Warning: Risk filter left only {len(result)} stocks, returning all {len(prices)}")
        return prices
    
    return result


def compute(message: str | dict):
    """Main computation function for portfolio recommendation."""
    if isinstance(message, str):
        pref = read_pref(message)
    else:
        pref = message

    print(f"pref: {pref}")
    
    if not pref:
        print("Error: No preferences provided")
        return None
    
    try:
        to_avoid = [map_categories.get(x, None) for x in pref.get("dislikes", [])]
        to_avoid = [x for x in to_avoid if x is not None]
        
        prices, sector_map = analysis1(start_date=pref["start"], end_date=pref["end"], avoid=to_avoid)
        
        if not prices:
            print("Error: No stocks passed growth filter")
            return None
        
        print(f"Stocks after growth filter: {len(prices)}")
        
        employed = pref.get("employed", False)
        salary = pref.get("salary", 0)
        
        if employed and salary and salary > 0:
            risk_ratio = pref["budget"] / salary
        else:
            risk_ratio = 0
        
        risk_level = calculate_risk(pref.get("age", -1), employed, risk_ratio)
        print(f"Calculated risk level: {risk_level}")
        
        filtered_prices = filter_by_risk(prices, sector_map, pref["start"], pref["end"], risk_level)
        
        print(f"Stocks after risk filter: {len(filtered_prices)}")
        
        if not filtered_prices:
            print("Error: No stocks passed risk filter")
            return None
        
        portfolio_dict = pack_portfolio(filtered_prices, sector_map, pref["budget"], risk_level)
        
        if portfolio_dict:
            return list(portfolio_dict.items())
        else:
            print("Error: Portfolio packing failed")
            return None
            
    except Exception as e:
        print(f"Error in compute: {e}")
        import traceback
        traceback.print_exc()
        return None


def pack_portfolio(stock_prices: dict, sector_map: dict, budget: int, risk_level: str):
    """Pack portfolio with diversification constraints."""
    if not stock_prices:
        print(f"No stocks available")
        return None
    
    # FIXED: Require at least 2 stocks instead of 3
    if len(stock_prices) < 2:
        print(f"Insufficient stocks available: {len(stock_prices)}")
        return None
    
    risk_budget_ratios = {
        "low": 0.30,
        "medium": 0.35,
        "high": 0.40
    }
    budget_ratio = risk_budget_ratios.get(risk_level, 0.30)
    
    portfolio = {}
    sector_allocations = {}
    total_budget = budget * budget_ratio
    remaining_budget = total_budget
    
    # Sort stocks by price (cheapest first)
    sorted_stocks = sorted(stock_prices.items(), key=lambda x: x[1])
    
    # Get unique sectors available
    available_sectors = list(set(sector_map.values()))
    min_sectors = min(2, len(available_sectors))  # FIXED: At least 2 sectors instead of 3
    
    print(f"Available sectors: {available_sectors}, targeting {min_sectors} minimum")
    
    # First pass: ensure minimum diversity
    sectors_used = set()
    for ticker, price in sorted_stocks:
        sector = sector_map[ticker]
        if sector not in sectors_used and price <= remaining_budget:
            portfolio[ticker] = 1
            remaining_budget -= price
            sectors_used.add(sector)
            sector_allocations[sector] = price
            
            if len(sectors_used) >= min_sectors:
                break
    
    if len(sectors_used) == 0:
        print("Error: Could not allocate any stocks")
        return None
    
    print(f"Initial allocation: {len(sectors_used)} sectors, {len(portfolio)} stocks, ${total_budget - remaining_budget:.2f} spent")
    
    # Second pass: fill remaining budget
    max_sector_budget = total_budget * MAX_SECTOR_ALLOCATION
    attempts = 0
    max_attempts = len(sorted_stocks) * 10
    
    i = 0
    while remaining_budget > sorted_stocks[0][1] and attempts < max_attempts:
        ticker, price = sorted_stocks[i % len(sorted_stocks)]
        sector = sector_map[ticker]
        
        current_sector_allocation = sector_allocations.get(sector, 0)
        
        if price <= remaining_budget and (current_sector_allocation + price) <= max_sector_budget:
            portfolio[ticker] = portfolio.get(ticker, 0) + 1
            remaining_budget -= price
            sector_allocations[sector] = current_sector_allocation + price
        
        i += 1
        attempts += 1
    
    if not portfolio:
        print("Error: Portfolio is empty after packing")
        return None
    
    total_invested = sum(stock_prices[t] * q for t, q in portfolio.items())
    print(f"Final portfolio: {len(sectors_used)} sectors, {len(portfolio)} stocks")
    print(f"Budget used: ${total_invested:,.2f} / ${total_budget:,.2f} ({total_invested/total_budget*100:.1f}%)")
    
    return portfolio