import spacy
import re
from collections import defaultdict

# CLAUDE BRUH CODE WE NEED TO OPTIMISE
class SpacyInvestmentAnalyzer:
    def __init__(self, model='en_core_web_sm'):
        """
        Initialize with spaCy model
            model: 'en_core_web_sm' (small, fast) or 'en_core_web_lg' (large, accurate)
        """
        try:
            self.nlp = spacy.load(model)
        except OSError:
            print(f"Model {model} not found. Downloading...")
            import subprocess
            subprocess.run(['python', '-m', 'spacy', 'download', model])
            self.nlp = spacy.load(model)
        
        # Define investment-related keywords
        self.risk_keywords = {
            'conservative': ['safe', 'never gamble', 'dont like to lose', 'dont like to loose',
                           'secure', 'stable', 'cautious', 'careful', 'protect', 'preservation'],
            'moderate': ['balanced', 'moderate', 'reasonable', 'mix', 'diversified'],
            'aggressive': ['risk', 'gamble', 'speculative', 'volatile', 'aggressive', 'growth']
        }
        
        self.sector_keywords = ['technology', 'tech', 'healthcare', 'health', 'energy', 
                               'finance', 'financial', 'real estate', 'property', 'retail']
        
        self.employment_keywords = {
            'unemployed': ['unemployed', 'jobless', 'between jobs', 'laid off'],
            'employed': ['employed', 'working', 'job'],
            'retired': ['retired', 'retirement'],
            'self-employed': ['self-employed', 'freelance', 'business owner', 'entrepreneur']
        }
        
        # Financial context keywords - CRITICAL for distinguishing money from age
        self.financial_context_keywords = [
            'savings', 'save', 'saved', 'dollars', 'pounds', 'money', 'wealth',
            'portfolio', 'assets', 'investment', 'invest', 'capital', 'funds',
            'net worth', 'worth', 'amount', 'budget', 'cash', 'fortune'
        ]
        
        # Age context keywords - helps identify when a number is an age
        self.age_context_keywords = [
            'am', 'is', 'age', 'years old', 'year old', 'old', 'aged',
            'birthday', 'born', 'turning'
        ]
    
    def extract_unnecessary_personal_info(self, doc):
        """
        Extract name, age, and employment using spaCy's NER with validation
        
        Args:
            doc: spaCy Doc object
            
        Returns:
            dict: Personal information
        """
        info = {}
        
        # Extract names using spaCy's Named Entity Recognition
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                info['name'] = ent.text
                break  # Take first person mentioned
        
        # Extract age with CONTEXT VALIDATION - this is the key fix!
        # We need to make sure we're looking at age, not money
        
        # Method 1: Use spaCy entities with context checking
        for ent in doc.ents:
            if ent.label_ in ['CARDINAL', 'DATE']:
                try:
                    # Extract numeric value
                    age_value = int(''.join(filter(str.isdigit, ent.text)))
                    
                    # VALIDATION 1: Must be reasonable age range
                    if not (18 <= age_value <= 120):
                        continue
                    
                    # VALIDATION 2: Check surrounding context
                    # Get text around the entity (30 chars before and after)
                    start_pos = max(0, ent.start_char - 30)
                    end_pos = min(len(doc.text), ent.end_char + 30)
                    context = doc.text[start_pos:end_pos].lower()
                    
                    # VALIDATION 3: Must have age context keywords nearby
                    has_age_context = any(keyword in context for keyword in self.age_context_keywords)
                    
                    # VALIDATION 4: Must NOT have financial context keywords nearby
                    has_financial_context = any(keyword in context for keyword in self.financial_context_keywords)
                    
                    # Only accept if it looks like age, not money
                    if has_age_context and not has_financial_context:
                        info['age'] = age_value
                        break
                        
                except (ValueError, AttributeError):
                    continue
        
        # Method 2: Regex with context validation (fallback)
        if 'age' not in info:
            # Look for patterns like "I am 55" or "I'm 55 years old"
            age_patterns = [
                r'\b(?:am|is|aged?)\s+(\d{1,3})\b',  # "I am 55"
                r'\b(\d{1,3})\s+years?\s+old\b',      # "55 years old"
            ]
            
            for pattern in age_patterns:
                matches = re.finditer(pattern, doc.text, re.IGNORECASE)
                for match in matches:
                    age_value = int(match.group(1))
                    if 18 <= age_value <= 120:
                        info['age'] = age_value
                        break
                if 'age' in info:
                    break
        
        # Extract employment status using keyword matching
        text_lower = doc.text.lower()
        for status, keywords in self.employment_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                info['employment_status'] = status
                break
        
        return info
    
    def extract_financial_info(self, doc):
        """
        Extract financial information with ROBUST VALIDATION
        
        Args:
            doc: spaCy Doc object
            
        Returns:
            dict: Financial information with validation
        """
        financial = {}
        candidates = []  # Store all potential money amounts with scores
        
        # Method 1: Use spaCy's MONEY entity (most reliable)
        for ent in doc.ents:
            if ent.label_ == 'MONEY':
                try:
                    amount = self._parse_money_amount(ent.text)
                    
                    # VALIDATION 1: Check context around the money entity
                    start_pos = max(0, ent.start_char - 50)
                    end_pos = min(len(doc.text), ent.end_char + 50)
                    context = doc.text[start_pos:end_pos].lower()
                    
                    # VALIDATION 2: Must have financial context
                    has_financial_context = any(keyword in context for keyword in self.financial_context_keywords)
                    
                    # VALIDATION 3: Should NOT be near age context
                    has_age_context = any(keyword in context for keyword in self.age_context_keywords)
                    
                    # Calculate confidence score
                    score = 0
                    if has_financial_context:
                        score += 2
                    if not has_age_context:
                        score += 1
                    if amount >= 10000:  # Larger amounts more likely to be savings
                        score += 10
                    
                    candidates.append({
                        'amount': amount,
                        'score': score,
                        'method': 'spacy_money_entity',
                        'context': context
                    })
                    
                except (ValueError, IndexError):
                    continue
        
        # Method 2: Regex pattern matching with context
        money_patterns = [
            # Pattern 1: Amount with unit words (50 million, 2.5 billion)
            r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(million|billion|thousand|m|b|k)',
            # Pattern 2: Currency symbols ($50,000)
            r'[$£€¥]\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            # Pattern 3: About/approximately patterns
            r'about\s+(\d+(?:,\d{3})*(?:\.\d+)?)\s*(million|billion|thousand|m|b|k)?',
        ]
        
        for pattern in money_patterns:
            matches = re.finditer(pattern, doc.text, re.IGNORECASE)
            for match in matches:
                try:
                    amount = self._parse_money_amount(match.group(0))
                    
                    # Get context around match
                    start_pos = max(0, match.start() - 50)
                    end_pos = min(len(doc.text), match.end() + 50)
                    context = doc.text[start_pos:end_pos].lower()
                    
                    # Validate context
                    has_financial_context = any(keyword in context for keyword in self.financial_context_keywords)
                    has_age_context = any(keyword in context for keyword in self.age_context_keywords)
                    
                    # Calculate score
                    score = 0
                    if has_financial_context:
                        score += 2
                    if not has_age_context:
                        score += 1
                    if amount >= 10000:
                        score += 1
                    if 'about' in context or 'approximately' in context:
                        score += 1  # "about 50 million" is very likely money
                    
                    candidates.append({
                        'amount': amount,
                        'score': score,
                        'method': 'regex_pattern',
                        'context': context
                    })
                    
                except (ValueError, IndexError):
                    continue
        
        # Select best candidate (highest score)
        if candidates:
            best_candidate = max(candidates, key=lambda x: x['score'])
            
            # Only accept if score is above threshold
            if best_candidate['score'] >= 2:
                financial['savings'] = best_candidate['amount']
                financial['confidence'] = best_candidate['score']
                financial['detection_method'] = best_candidate['method']
            else:
                # Log ambiguous case
                financial['warning'] = 'Ambiguous financial information detected'
                financial['candidates'] = candidates
        
        return financial
    
    def _parse_money_amount(self, text):
        """
        Helper function to parse money amounts from text
        
        Args:
            text: String containing money amount
            
        Returns:
            float: Parsed amount
        """
        text_lower = text.lower()
        
        # Extract base number
        number_match = re.search(r'(\d+(?:,\d{3})*(?:\.\d+)?)', text_lower)
        if not number_match:
            raise ValueError("No number found in text")
        
        amount = float(number_match.group(1).replace(',', ''))
        
        # Apply multipliers
        multipliers = {
            'thousand': 1_000, 'k': 1_000,
            'million': 1_000_000, 'm': 1_000_000,
            'billion': 1_000_000_000, 'b': 1_000_000_000
        }
        
        for unit, multiplier in multipliers.items():
            if unit in text_lower:
                amount *= multiplier
                break
        
        return amount
    
    def analyze_risk_tolerance(self, doc):
        """
        Analyze risk tolerance using keyword matching
        
        Args:
            doc: spaCy Doc object
            
        Returns:
            str: Risk tolerance level
        """
        text_lower = doc.text.lower()
        
        # Count keyword matches
        risk_scores = defaultdict(int)
        
        for risk_level, keywords in self.risk_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    risk_scores[risk_level] += 1
        
        # Determine risk profile with priority
        if risk_scores['conservative'] > 0:
            return 'Conservative'
        elif risk_scores['aggressive'] > 0:
            return 'Aggressive'
        else:
            return 'Moderate'
    
    def extract_sector_preferences(self, doc):
        """
        Extract investment sector preferences
        
        Args:
            doc: spaCy Doc object
            
        Returns:
            list: Preferred sectors
        """
        preferences = []
        text_lower = doc.text.lower()
        
        # Check for sector keywords
        for sector in self.sector_keywords:
            if sector in text_lower:
                # Normalize sector names
                if sector == 'tech':
                    normalized = 'Technology'
                elif sector == 'health':
                    normalized = 'Healthcare'
                elif sector == 'property':
                    normalized = 'Real Estate'
                elif sector == 'financial':
                    normalized = 'Finance'
                else:
                    normalized = sector.capitalize()
                
                if normalized not in preferences:
                    preferences.append(normalized)
        
        return preferences
    
    def extract_sentiment_insights(self, doc):
        """
        Extract sentiment and key phrases using spaCy
        
        Args:
            doc: spaCy Doc object
            
        Returns:
            dict: Sentiment insights
        """
        insights = {}
        
        # Extract key noun phrases
        noun_phrases = [chunk.text for chunk in doc.noun_chunks]
        insights['key_topics'] = noun_phrases[:5]
        
        # Extract entities for additional context
        entities = {}
        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []
            entities[ent.label_].append(ent.text)
        insights['entities'] = entities
        
        return insights
    
    def generate_recommendations(self, profile):
        """
        Generate investment recommendations based on profile
        """
        recommendations = []
        
        age = profile.get('age', 50)
        risk = profile.get('risk_tolerance', 'Moderate')
        savings = profile.get('savings', 0)
        sectors = profile.get('sector_preferences', [])
        
        # Age-based allocation
        stock_allocation = 100 - age
        bond_allocation = age
        
        recommendations.append(f"Age-based allocation: {stock_allocation}% stocks, {bond_allocation}% bonds")
        
        # Risk-based recommendations
        if risk == 'Conservative':
            recommendations.append("Focus on: Treasury bonds, dividend aristocrats, blue-chip stocks")
            recommendations.append("Avoid: Speculative stocks, cryptocurrencies, options trading")
            recommendations.append("Emergency fund: Keep 12-24 months of expenses in high-yield savings")
        elif risk == 'Aggressive':
            recommendations.append("Consider: Growth stocks, emerging markets, alternative investments")
            recommendations.append("Allocate 10-20% to speculative high-growth opportunities")
        else:
            recommendations.append("Balanced portfolio: Mix of growth and value stocks with bond cushion")
            recommendations.append("60/40 stock/bond split with quarterly rebalancing")
        
        # Sector-specific recommendations
        if 'Technology' in sectors:
            if risk == 'Conservative':
                recommendations.append("Technology: Focus on established tech giants with strong cash flow")
                recommendations.append("Consider: Microsoft, Apple, Google - companies with proven track records")
            else:
                recommendations.append("Technology: Mix of established companies (70%) and growth opportunities (30%)")
        
        # Savings-based recommendations
        if savings > 10_000_000:
            recommendations.append("High net worth strategies:")
            recommendations.append("  • Professional wealth management and tax optimization")
            recommendations.append("  • Estate planning and trust structures")
            recommendations.append("  • Alternative investments: Private equity, hedge funds, real estate")
            recommendations.append("  • International diversification for currency risk")
        elif savings > 1_000_000:
            recommendations.append("Consider working with a fee-only financial advisor")
            recommendations.append("Explore: Index funds, REITs, municipal bonds for tax efficiency")
        
        # Employment-specific recommendations
        employment = profile.get('employment_status')
        if employment == 'unemployed':
            recommendations.append("Unemployment considerations:")
            recommendations.append("  • Maintain 12-24 months emergency fund before investing")
            recommendations.append("  • Consider lower risk until employment stabilizes")
            recommendations.append("  • Explore health insurance options (COBRA, ACA marketplace)")
        
        return recommendations
    
    def analyze(self, text):
        """
        Complete analysis of investment profile using spaCy
        
        Args:
            text: Input text string
            
        Returns:
            dict: Complete profile analysis
        """
        # Process text with spaCy
        doc = self.nlp(text)
        
        profile = {}
        
        # Extract all information
        profile.update(self.extract_unnecessary_personal_info(doc))
        profile.update(self.extract_financial_info(doc))
        profile['risk_tolerance'] = self.analyze_risk_tolerance(doc)
        profile['sector_preferences'] = self.extract_sector_preferences(doc)
        profile['sentiment_insights'] = self.extract_sentiment_insights(doc)
        profile['recommendations'] = self.generate_recommendations(profile)
        
        return profile
    
    def print_profile(self, profile):
        """Pretty print the investment profile with validation info"""
        print("=" * 70)
        print("INVESTMENT PROFILE ANALYSIS (spaCy - VALIDATED)")
        print("=" * 70)
        
        print("\n📋 PERSONAL INFORMATION")
        print(f"  Name: {profile.get('name', 'N/A')}")
        print(f"  Age: {profile.get('age', 'N/A')}")
        print(f"  Employment: {profile.get('employment_status', 'N/A')}")
        
        print("\n💰 FINANCIAL INFORMATION")
        savings = profile.get('savings', 0)
        if savings > 0:
            print(f"  Savings: ${savings:,.2f}")
            if 'confidence' in profile:
                print(f"  Confidence Score: {profile['confidence']}/5")
            if 'detection_method' in profile:
                print(f"  Detection Method: {profile['detection_method']}")
        else:
            print(f"  Savings: Not specified")
            if 'warning' in profile:
                print(f"  ⚠️  Warning: {profile['warning']}")
        
        print("\n📊 RISK PROFILE")
        print(f"  Risk Tolerance: {profile.get('risk_tolerance', 'N/A')}")
        
        print("\n🎯 SECTOR PREFERENCES")
        sectors = profile.get('sector_preferences', [])
        if sectors:
            for sector in sectors:
                print(f"  • {sector}")
        else:
            print("  None specified")
        
        print("\n🔍 SENTIMENT INSIGHTS")
        insights = profile.get('sentiment_insights', {})
        if insights.get('key_topics'):
            print("  Key topics mentioned:")
            for topic in insights['key_topics'][:3]:
                print(f"    • {topic}")
        
        print("\n💡 INVESTMENT RECOMMENDATIONS")
        recommendations = profile.get('recommendations', [])
        for i, rec in enumerate(recommendations, 1):
            if rec.startswith('  •'):
                print(f"    {rec}")
            else:
                print(f"  {i}. {rec}")
        
        print("\n" + "=" * 70)


# Example usage and testing
if __name__ == "__main__":
    # Initialize analyzer
    analyzer = SpacyInvestmentAnalyzer()
    
    # Test case 1: Original example
    print("TEST CASE 1: Original Example")
    print("-" * 70)
    text1 = """My name is Jim and I am 55, I am recently unemployed however have 
    a large amount of savings, about 50 million, I am very safe and never gamble 
    and dont like to loose money, I really love technology and want to invest there"""
    
    profile1 = analyzer.analyze(text1)
    analyzer.print_profile(profile1)
    
    # Test case 2: Different format
    print("\n\n" + "=" * 70)
    print("TEST CASE 2: Different Money Format")
    print("-" * 70)
    text2 = """Hi, I'm Sarah, 42 years old. I'm employed and have $2.5 million 
    saved up. I'm looking for aggressive growth opportunities in healthcare."""
    
    profile2 = analyzer.analyze(text2)
    analyzer.print_profile(profile2)
    
    # Test case 3: Edge case - age and money close together
    print("\n\n" + "=" * 70)
    print("TEST CASE 3: Edge Case - Age and Money Near Each Other")
    print("-" * 70)
    text3 = """I'm 65 and have about 65 thousand dollars in my retirement account."""
    
    profile3 = analyzer.analyze(text3)
    analyzer.print_profile(profile3)
    
    # Show debugging info for test case 1
    print("\n\n" + "=" * 70)
    print("DEBUGGING: Why Jim's profile worked correctly")
    print("=" * 70)
    doc = analyzer.nlp(text1)
    print("\nAll entities detected:")
    for ent in doc.ents:
        print(f"  {ent.text:20} → {ent.label_:15}")