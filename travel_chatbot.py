"""
Travel Planner AI Chatbot
Advanced travel planning assistant with security, OpenAI function calling, and travel-only restrictions
"""

import json
import pandas as pd
import re
import logging
import openai
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    encoding='utf-8',
    handlers=[
        logging.FileHandler('travel_chatbot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
security_logger = logging.getLogger('security')
travel_logger = logging.getLogger('travel')

# OpenAI Configuration
openai.api_key = open('OpenAI_API_Key.txt', 'r').read().strip()


class TravelSecurityValidator:
    """Advanced security and travel topic validation system"""

    def __init__(self):
        # Travel-related keywords for validation
        self.travel_keywords = {
            'destinations': [
                'city', 'country', 'destination', 'place', 'location', 'visit', 'travel to',
                'paris', 'london', 'tokyo', 'new york', 'dubai', 'barcelona', 'rome',
                'bangkok', 'sydney', 'mumbai', 'europe', 'asia', 'america', 'africa'
            ],
            'accommodation': [
                'hotel', 'hostel', 'resort', 'accommodation', 'stay', 'lodge', 'inn',
                'apartment', 'booking', 'room', 'suite', 'bed and breakfast'
            ],
            'activities': [
                'attraction', 'sightseeing', 'tour', 'museum', 'landmark', 'monument',
                'beach', 'park', 'temple', 'church', 'castle', 'gallery', 'zoo',
                'shopping', 'restaurant', 'nightlife', 'entertainment'
            ],
            'transportation': [
                'flight', 'plane', 'airport', 'train', 'bus', 'taxi', 'car rental',
                'transportation', 'metro', 'subway', 'ferry', 'cruise'
            ],
            'planning': [
                'itinerary', 'schedule', 'plan', 'trip', 'vacation', 'holiday', 'journey',
                'budget', 'cost', 'price', 'expense', 'currency', 'exchange',
                'visa', 'passport', 'weather', 'climate', 'season'
            ]
        }

        # Security threat detection
        self.threat_words = {
            'high_threat': [
                'bomb', 'terrorist', 'kill', 'murder', 'attack', 'violence', 'weapon',
                'gun', 'knife', 'explosive', 'threat', 'harm', 'destroy'
            ],
            'inappropriate': [
                'sex', 'porn', 'nude', 'adult', 'drug', 'cocaine', 'marijuana'
            ],
            'travel_illegal': [
                'visa fraud', 'fake passport', 'smuggling', 'human trafficking',
                'drug trafficking', 'money laundering', 'illegal border'
            ]
        }

        # Non-travel topics to block
        self.non_travel_topics = {
            'technology': [
                'programming', 'coding', 'software', 'computer', 'python', 'javascript',
                'html', 'css', 'database', 'api', 'algorithm'
            ],
            'entertainment': [
                'movie', 'tv show', 'music', 'song', 'game', 'sport', 'celebrity', 'news'
            ],
            'education': [
                'homework', 'essay', 'study', 'exam', 'math problem', 'research paper'
            ],
            'general': [
                'hello', 'hi', 'how are you', 'tell me a joke', 'what do you think'
            ]
        }

        # Compile patterns for efficient matching
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for efficient matching"""
        # Travel keywords pattern
        all_travel_words = []
        for category, words in self.travel_keywords.items():
            all_travel_words.extend(words)

        self.travel_pattern = re.compile(
            r'\b(?:' + '|'.join(re.escape(word) for word in all_travel_words) + r')\b',
            re.IGNORECASE
        )

        # Threat patterns
        self.threat_patterns = {}
        for category, words in self.threat_words.items():
            pattern = r'\b(?:' + '|'.join(re.escape(word) for word in words) + r')\b'
            self.threat_patterns[category] = re.compile(pattern, re.IGNORECASE)

        # Non-travel patterns
        self.non_travel_patterns = {}
        for category, words in self.non_travel_topics.items():
            pattern = r'\b(?:' + '|'.join(re.escape(word) for word in words) + r')\b'
            self.non_travel_patterns[category] = re.compile(pattern, re.IGNORECASE)

    def validate_content(self, text: str, user_id: str = "anonymous") -> dict:
        """
        Comprehensive content validation for security and travel topics

        Returns:
            dict: Validation result with safety status and recommendations
        """
        if not text or not isinstance(text, str):
            return {"is_safe": False, "is_travel": False, "action": "block", "reason": "invalid_input"}

        text_clean = text.strip().lower()

        # 1. Security threat check
        security_result = self._check_security_threats(text_clean, user_id)
        if not security_result["is_safe"]:
            return {
                "is_safe": False,
                "is_travel": False,
                "action": "block",
                "reason": "security_violation",
                "category": security_result["category"],
                "severity": security_result.get("severity", "high")
            }

        # 2. Travel topic validation
        travel_score = self._calculate_travel_relevance(text_clean)

        if travel_score < 0.3:  # Travel relevance threshold
            non_travel_category = self._detect_non_travel_category(text_clean)

            travel_logger.info(
                f"Non-travel query blocked - User: {user_id}, Category: {non_travel_category}, Score: {travel_score:.2f}")

            return {
                "is_safe": True,
                "is_travel": False,
                "action": "redirect",
                "reason": "non_travel_topic",
                "category": non_travel_category,
                "travel_score": travel_score,
                "suggestion": self._get_travel_suggestion()
            }

        # Content is safe and travel-related
        travel_logger.info(f"Travel query approved - User: {user_id}, Score: {travel_score:.2f}")
        return {
            "is_safe": True,
            "is_travel": True,
            "action": "allow",
            "reason": "valid_travel_query",
            "travel_score": travel_score
        }

    def _check_security_threats(self, text: str, user_id: str) -> dict:
        """Check for security threats and inappropriate content"""
        for category, pattern in self.threat_patterns.items():
            matches = pattern.findall(text)
            if matches:
                security_logger.warning(
                    f"Security threat detected - User: {user_id}, Category: {category}, Matches: {matches}")
                return {
                    "is_safe": False,
                    "category": category,
                    "matches": matches,
                    "severity": "critical" if category == "high_threat" else "moderate"
                }
        return {"is_safe": True}

    def _calculate_travel_relevance(self, text: str) -> float:
        """Calculate travel relevance score (0.0 to 1.0)"""
        words = text.split()
        if not words:
            return 0.0

        travel_matches = len(self.travel_pattern.findall(text))
        total_words = len(words)

        # Base score from keyword matches
        keyword_score = min(travel_matches / max(total_words * 0.3, 1), 1.0)

        # Boost for travel-specific patterns
        travel_patterns = [
            r'\b(?:trip to|travel to|visit|vacation in|holiday in)\b',
            r'\b(?:hotel in|stay in|accommodation in)\b',
            r'\b(?:attractions in|things to do in)\b',
            r'\b(?:budget for|cost of).+(?:trip|travel|vacation)\b',
            r'\b(?:weather in|climate in|best time to visit)\b'
        ]

        pattern_boost = 0.0
        for pattern in travel_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                pattern_boost += 0.2

        return min(keyword_score + pattern_boost, 1.0)

    def _detect_non_travel_category(self, text: str) -> str:
        """Detect category of non-travel topic"""
        for category, pattern in self.non_travel_patterns.items():
            if pattern.search(text):
                return category
        return "other_non_travel"

    def _get_travel_suggestion(self) -> str:
        """Get helpful travel-focused suggestion"""
        suggestions = [
            "Try asking about hotels, attractions, or itineraries for your destination!",
            "I can help you plan trips - ask about destinations, budgets, or travel recommendations!",
            "Let's focus on travel planning - ask me about accommodations, activities, or trip costs!",
            "Ask me about travel topics like finding hotels, creating itineraries, or budgeting for trips!"
        ]
        import random
        return random.choice(suggestions)


# Initialize security validator
security_validator = TravelSecurityValidator()

# Load travel datasets
try:
    hotels_df = pd.read_csv('travel_hotels.csv')
    attractions_df = pd.read_csv('travel_attractions.csv')
    with open('travel_itinerary_templates.json', 'r') as f:
        itinerary_templates = json.load(f)
    logger.info("Travel datasets loaded successfully!")
except Exception as e:
    logger.error(f"Error loading datasets: {e}")
    hotels_df = pd.DataFrame()
    attractions_df = pd.DataFrame()
    itinerary_templates = {}


class TravelPlannerFunctions:
    """Advanced travel planning functions with comprehensive features"""

    @staticmethod
    def search_hotels(city: str, budget_max: int = None, category: str = None, check_availability: bool = True):
        """
        Search for hotels with advanced filtering

        Args:
            city: Destination city
            budget_max: Maximum budget per night (USD)
            category: Hotel category (luxury/mid-range/budget)
            check_availability: Whether to check availability

        Returns:
            dict: Hotel search results with detailed information
        """
        try:
            if not city or not isinstance(city, str):
                return {"error": "City parameter is required and must be a valid string"}

            city = city.strip().title()

            if hotels_df.empty:
                return {"error": "Hotel database is currently unavailable"}

            # Filter by city (case-insensitive)
            city_hotels = hotels_df[hotels_df['city'].str.lower() == city.lower()]

            if city_hotels.empty:
                available_cities = sorted(hotels_df['city'].unique().tolist())
                return {
                    "error": f"No hotels found in {city}",
                    "available_cities": available_cities,
                    "suggestion": f"Try one of these cities: {', '.join(available_cities[:5])}"
                }

            # Apply filters
            if budget_max:
                if not isinstance(budget_max, int) or budget_max < 0 or budget_max > 5000:
                    return {"error": "Budget must be a positive integer between 0 and 5000 USD"}
                city_hotels = city_hotels[city_hotels['price_per_night'] <= budget_max]

            if category:
                valid_categories = ['luxury', 'mid-range', 'budget']
                if category.lower() not in valid_categories:
                    return {"error": f"Category must be one of: {', '.join(valid_categories)}"}
                city_hotels = city_hotels[city_hotels['category'].str.lower() == category.lower()]

            if check_availability:
                city_hotels = city_hotels[city_hotels['availability'] == True]

            if city_hotels.empty:
                return {
                    "error": f"No hotels found matching your criteria in {city}",
                    "suggestion": "Try adjusting your budget or category preferences"
                }

            # Sort by rating and select top results
            results = city_hotels.sort_values(['rating', 'price_per_night'], ascending=[False, True]).head(8)

            hotels_list = []
            for _, hotel in results.iterrows():
                hotels_list.append({
                    'id': hotel['hotel_id'],
                    'name': hotel['name'],
                    'category': hotel['category'],
                    'price_per_night': int(hotel['price_per_night']),
                    'rating': float(hotel['rating']),
                    'amenities': hotel['amenities'].split(','),
                    'address': hotel['address'],
                    'available': bool(hotel['availability']),
                    'country': hotel['country']
                })

            # Calculate statistics
            avg_price = int(results['price_per_night'].mean())
            price_range = {
                'min': int(results['price_per_night'].min()),
                'max': int(results['price_per_night'].max())
            }

            return {
                "success": True,
                "city": city,
                "country": results.iloc[0]['country'],
                "hotels_found": len(hotels_list),
                "hotels": hotels_list,
                "statistics": {
                    "average_price": avg_price,
                    "price_range": price_range,
                    "average_rating": round(results['rating'].mean(), 1)
                },
                "filters_applied": {
                    "budget_max": budget_max,
                    "category": category,
                    "availability_check": check_availability
                }
            }

        except Exception as e:
            logger.error(f"Error in search_hotels: {e}")
            return {"error": "Failed to search hotels. Please try again with valid parameters."}

    @staticmethod
    def get_attractions(city: str, category: str = None, max_entry_fee: int = None):
        """
        Get tourist attractions with filtering options

        Args:
            city: Destination city
            category: Attraction category filter
            max_entry_fee: Maximum entry fee (USD)

        Returns:
            dict: Attractions search results
        """
        try:
            if not city or not isinstance(city, str):
                return {"error": "City parameter is required and must be a valid string"}

            city = city.strip().title()

            if attractions_df.empty:
                return {"error": "Attractions database is currently unavailable"}

            # Filter by city
            city_attractions = attractions_df[attractions_df['city'].str.lower() == city.lower()]

            if city_attractions.empty:
                available_cities = sorted(attractions_df['city'].unique().tolist())
                return {
                    "error": f"No attractions found in {city}",
                    "available_cities": available_cities,
                    "suggestion": f"Try one of these cities: {', '.join(available_cities[:5])}"
                }

            # Apply filters
            if category:
                available_categories = sorted(attractions_df['category'].unique().tolist())
                if category not in available_categories:
                    return {
                        "error": f"Invalid category '{category}'",
                        "available_categories": available_categories
                    }
                city_attractions = city_attractions[city_attractions['category'] == category]

            if max_entry_fee is not None:
                if not isinstance(max_entry_fee, int) or max_entry_fee < 0:
                    return {"error": "Maximum entry fee must be a non-negative integer"}
                city_attractions = city_attractions[city_attractions['entry_fee'] <= max_entry_fee]

            if city_attractions.empty:
                return {
                    "error": f"No attractions found matching your criteria in {city}",
                    "suggestion": "Try adjusting your category or budget filters"
                }

            # Sort by rating and select top results
            results = city_attractions.sort_values(['rating', 'entry_fee'], ascending=[False, True]).head(12)

            attractions_list = []
            for _, attraction in results.iterrows():
                attractions_list.append({
                    'id': attraction['attraction_id'],
                    'name': attraction['name'],
                    'category': attraction['category'],
                    'entry_fee': int(attraction['entry_fee']),
                    'duration_hours': float(attraction['duration_hours']),
                    'rating': float(attraction['rating']),
                    'description': attraction['description'],
                    'opening_hours': attraction['opening_hours'],
                    'country': attraction['country']
                })

            # Group by category for better organization
            categories_summary = results.groupby('category').agg({
                'attraction_id': 'count',
                'entry_fee': 'mean',
                'rating': 'mean'
            }).round(1).to_dict('index')

            return {
                "success": True,
                "city": city,
                "country": results.iloc[0]['country'],
                "attractions_found": len(attractions_list),
                "attractions": attractions_list,
                "categories_summary": categories_summary,
                "statistics": {
                    "average_entry_fee": int(results['entry_fee'].mean()),
                    "free_attractions": len(results[results['entry_fee'] == 0]),
                    "average_duration": round(results['duration_hours'].mean(), 1),
                    "average_rating": round(results['rating'].mean(), 1)
                },
                "filters_applied": {
                    "category": category,
                    "max_entry_fee": max_entry_fee
                }
            }

        except Exception as e:
            logger.error(f"Error in get_attractions: {e}")
            return {"error": "Failed to get attractions. Please try again with valid parameters."}

    @staticmethod
    def create_itinerary(city: str, duration_days: int, interests: str = None):
        """
        Create detailed travel itinerary

        Args:
            city: Destination city
            duration_days: Trip duration (1-14 days)
            interests: User interests/preferences

        Returns:
            dict: Detailed itinerary with daily plans
        """
        try:
            if not city or not isinstance(city, str):
                return {"error": "City parameter is required and must be a valid string"}

            if not isinstance(duration_days, int) or duration_days < 1 or duration_days > 14:
                return {"error": "Duration must be between 1 and 14 days"}

            city = city.strip().title()

            # Check for pre-built templates
            if city in itinerary_templates and f"{duration_days}_days" in itinerary_templates[city]:
                template_itinerary = itinerary_templates[city][f"{duration_days}_days"]

                total_cost = sum(day['estimated_cost'] for day in template_itinerary)

                return {
                    "success": True,
                    "city": city,
                    "duration_days": duration_days,
                    "itinerary_type": "curated_template",
                    "itinerary": template_itinerary,
                    "total_estimated_cost": total_cost,
                    "daily_average_cost": round(total_cost / duration_days, 2),
                    "notes": "This is a curated itinerary template based on popular attractions and activities."
                }

            # Generate custom itinerary from attractions
            attractions_result = TravelPlannerFunctions.get_attractions(city)
            if not attractions_result.get("success"):
                return attractions_result

            attractions = attractions_result["attractions"]

            if len(attractions) < duration_days * 2:
                return {
                    "error": f"Insufficient attraction data for {duration_days} days in {city}",
                    "suggestion": "Try a shorter duration or a different destination"
                }

            # Create balanced itinerary
            itinerary = []
            attractions_per_day = max(2, len(attractions) // duration_days)

            # Group attractions by category for variety
            categorized_attractions = {}
            for attraction in attractions:
                category = attraction['category']
                if category not in categorized_attractions:
                    categorized_attractions[category] = []
                categorized_attractions[category].append(attraction)

            # Distribute attractions across days
            used_attractions = set()

            for day in range(1, duration_days + 1):
                day_attractions = []
                day_cost = 50  # Base cost for meals and transport

                # Try to get diverse attractions for each day
                for category in categorized_attractions:
                    available = [a for a in categorized_attractions[category]
                                 if a['id'] not in used_attractions]
                    if available and len(day_attractions) < attractions_per_day:
                        selected = available[0]
                        day_attractions.append(selected)
                        used_attractions.add(selected['id'])
                        day_cost += selected['entry_fee']

                # Fill remaining slots if needed
                while len(day_attractions) < attractions_per_day:
                    remaining = [a for a in attractions if a['id'] not in used_attractions]
                    if not remaining:
                        break
                    selected = remaining[0]
                    day_attractions.append(selected)
                    used_attractions.add(selected['id'])
                    day_cost += selected['entry_fee']

                # Create day plan
                day_plan = {
                    'day': day,
                    'title': f"Day {day} - {city} Exploration",
                    'activities': [attr['name'] for attr in day_attractions],
                    'attraction_details': day_attractions,
                    'meals': ['Local breakfast', 'Regional lunch', 'Traditional dinner'],
                    'estimated_cost': day_cost,
                    'total_duration': sum(attr['duration_hours'] for attr in day_attractions),
                    'transportation': 'Public transport + Walking'
                }

                itinerary.append(day_plan)

            total_cost = sum(day['estimated_cost'] for day in itinerary)

            return {
                "success": True,
                "city": city,
                "duration_days": duration_days,
                "itinerary_type": "custom_generated",
                "itinerary": itinerary,
                "total_estimated_cost": total_cost,
                "daily_average_cost": round(total_cost / duration_days, 2),
                "attractions_included": len(used_attractions),
                "customization": {
                    "interests": interests,
                    "variety_achieved": len(categorized_attractions)
                },
                "notes": "This is a custom itinerary generated from available attractions data."
            }

        except Exception as e:
            logger.error(f"Error in create_itinerary: {e}")
            return {"error": "Failed to create itinerary. Please try again with valid parameters."}

    @staticmethod
    def get_travel_budget_estimate(city: str, duration_days: int, accommodation_category: str = "mid-range"):
        """
        Calculate comprehensive travel budget

        Args:
            city: Destination city
            duration_days: Trip duration
            accommodation_category: Hotel category preference

        Returns:
            dict: Detailed budget breakdown
        """
        try:
            if not city or not isinstance(city, str):
                return {"error": "City parameter is required"}

            if not isinstance(duration_days, int) or duration_days < 1 or duration_days > 30:
                return {"error": "Duration must be between 1 and 30 days"}

            city = city.strip().title()

            valid_categories = ['luxury', 'mid-range', 'budget']
            if accommodation_category not in valid_categories:
                return {"error": f"Accommodation category must be one of: {', '.join(valid_categories)}"}

            # Get hotel prices
            hotels_result = TravelPlannerFunctions.search_hotels(city, category=accommodation_category)
            if hotels_result.get("success") and hotels_result.get("hotels"):
                avg_hotel_price = hotels_result["statistics"]["average_price"]
            else:
                # Fallback pricing based on category and city
                base_prices = {'luxury': 400, 'mid-range': 150, 'budget': 60}
                city_multipliers = {
                    'Paris': 1.3, 'London': 1.4, 'Tokyo': 1.2, 'New York': 1.5, 'Dubai': 1.1,
                    'Barcelona': 0.9, 'Rome': 1.0, 'Bangkok': 0.6, 'Sydney': 1.1, 'Mumbai': 0.5
                }
                multiplier = city_multipliers.get(city, 1.0)
                avg_hotel_price = int(base_prices[accommodation_category] * multiplier)

            # Get attractions costs
            attractions_result = TravelPlannerFunctions.get_attractions(city)
            if attractions_result.get("success") and attractions_result.get("attractions"):
                attractions_data = attractions_result["attractions"][:duration_days * 3]
                avg_attraction_cost = sum(a['entry_fee'] for a in attractions_data) / len(attractions_data)
            else:
                avg_attraction_cost = 20  # Fallback

            # Calculate comprehensive budget
            accommodation_total = avg_hotel_price * duration_days
            attractions_total = avg_attraction_cost * duration_days * 2.5  # 2-3 attractions per day

            # City-specific meal costs
            meal_costs = {
                'Paris': 70, 'London': 65, 'Tokyo': 55, 'New York': 80, 'Dubai': 60,
                'Barcelona': 45, 'Rome': 50, 'Bangkok': 25, 'Sydney': 60, 'Mumbai': 20
            }
            meals_daily = meal_costs.get(city, 50)
            meals_total = meals_daily * duration_days

            # Transportation costs
            transport_daily = 30 if city in ['New York', 'London', 'Paris'] else 20
            transport_total = transport_daily * duration_days

            # Miscellaneous (shopping, tips, emergencies)
            misc_percentage = 0.15
            subtotal = accommodation_total + attractions_total + meals_total + transport_total
            miscellaneous_total = subtotal * misc_percentage

            total_budget = subtotal + miscellaneous_total

            # Budget breakdown by category
            budget_breakdown = {
                "accommodation": {
                    "total": round(accommodation_total, 2),
                    "daily": round(accommodation_total / duration_days, 2),
                    "category": accommodation_category,
                    "percentage": round((accommodation_total / total_budget) * 100, 1)
                },
                "attractions": {
                    "total": round(attractions_total, 2),
                    "daily": round(attractions_total / duration_days, 2),
                    "avg_per_attraction": round(avg_attraction_cost, 2),
                    "percentage": round((attractions_total / total_budget) * 100, 1)
                },
                "meals": {
                    "total": round(meals_total, 2),
                    "daily": round(meals_daily, 2),
                    "percentage": round((meals_total / total_budget) * 100, 1)
                },
                "transportation": {
                    "total": round(transport_total, 2),
                    "daily": round(transport_daily, 2),
                    "percentage": round((transport_total / total_budget) * 100, 1)
                },
                "miscellaneous": {
                    "total": round(miscellaneous_total, 2),
                    "daily": round(miscellaneous_total / duration_days, 2),
                    "percentage": round((miscellaneous_total / total_budget) * 100, 1)
                },
                "total": round(total_budget, 2)
            }

            # Budget comparison by category
            category_comparisons = {
                'budget': round(total_budget * 0.7, 2),
                'mid-range': round(total_budget, 2),
                'luxury': round(total_budget * 1.5, 2)
            }

            return {
                "success": True,
                "city": city,
                "duration_days": duration_days,
                "accommodation_category": accommodation_category,
                "budget_breakdown": budget_breakdown,
                "daily_average": round(total_budget / duration_days, 2),
                "category_comparisons": category_comparisons,
                "budget_tips": [
                    f"Accommodation represents {budget_breakdown['accommodation']['percentage']}% of your budget",
                    f"Consider visiting during off-peak season for 20-30% savings",
                    f"Free attractions can reduce costs by ${round(attractions_total * 0.3, 2)}",
                    f"Street food and local eateries can save ${round(meals_total * 0.4, 2)}"
                ],
                "currency": "USD"
            }

        except Exception as e:
            logger.error(f"Error in get_travel_budget_estimate: {e}")
            return {"error": "Failed to estimate budget. Please try again with valid parameters."}

    @staticmethod
    def check_weather_recommendation(city: str, travel_month: str):
        """
        Get weather-based travel recommendations

        Args:
            city: Destination city
            travel_month: Month of travel

        Returns:
            dict: Weather recommendations and best travel times
        """
        try:
            if not city or not isinstance(city, str):
                return {"error": "City parameter is required"}

            if not travel_month or not isinstance(travel_month, str):
                return {"error": "Travel month is required"}

            city = city.strip().title()
            travel_month = travel_month.strip().title()

            # Validate month
            valid_months = ['January', 'February', 'March', 'April', 'May', 'June',
                            'July', 'August', 'September', 'October', 'November', 'December']

            if travel_month not in valid_months:
                return {"error": f"Invalid month. Must be one of: {', '.join(valid_months)}"}

            # Comprehensive weather database
            weather_data = {
                "Paris": {
                    "best_months": ["April", "May", "June", "September", "October"],
                    "good_months": ["March", "July", "August"],
                    "avoid_months": ["December", "January", "February"],
                    "weather_info": "Mild temperatures, moderate rainfall, perfect for sightseeing",
                    "peak_season": "May-September",
                    "temperature_range": "3°C to 25°C (37°F to 77°F)",
                    "rainfall": "Moderate year-round, heaviest in winter"
                },
                "London": {
                    "best_months": ["May", "June", "July", "August", "September"],
                    "good_months": ["April", "October"],
                    "avoid_months": ["November", "December", "January", "February"],
                    "weather_info": "Mild summers, rainy winters, longer daylight hours in summer",
                    "peak_season": "June-August",
                    "temperature_range": "2°C to 23°C (36°F to 73°F)",
                    "rainfall": "Year-round, but less in summer"
                },
                "Tokyo": {
                    "best_months": ["March", "April", "May", "October", "November"],
                    "good_months": ["February", "December"],
                    "avoid_months": ["June", "July", "August", "September"],
                    "weather_info": "Cherry blossom season (March-May) and pleasant autumn weather",
                    "peak_season": "March-May, October-November",
                    "temperature_range": "0°C to 30°C (32°F to 86°F)",
                    "rainfall": "Rainy season June-July, typhoons August-September"
                },
                "New York": {
                    "best_months": ["April", "May", "June", "September", "October"],
                    "good_months": ["March", "November"],
                    "avoid_months": ["January", "February", "July", "August"],
                    "weather_info": "Four distinct seasons, hot humid summers, cold winters",
                    "peak_season": "April-June, September-November",
                    "temperature_range": "-3°C to 29°C (27°F to 85°F)",
                    "rainfall": "Fairly distributed year-round"
                },
                "Dubai": {
                    "best_months": ["November", "December", "January", "February", "March"],
                    "good_months": ["April", "October"],
                    "avoid_months": ["June", "July", "August", "September"],
                    "weather_info": "Desert climate, very hot summers, mild winters",
                    "peak_season": "November-March",
                    "temperature_range": "14°C to 41°C (57°F to 106°F)",
                    "rainfall": "Very low, occasional winter showers"
                },
                "Barcelona": {
                    "best_months": ["April", "May", "June", "September", "October"],
                    "good_months": ["March", "July", "November"],
                    "avoid_months": ["December", "January", "February"],
                    "weather_info": "Mediterranean climate, warm dry summers, mild winters",
                    "peak_season": "May-September",
                    "temperature_range": "8°C to 28°C (46°F to 82°F)",
                    "rainfall": "Low, mainly in autumn and spring"
                },
                "Rome": {
                    "best_months": ["April", "May", "June", "September", "October"],
                    "good_months": ["March", "November"],
                    "avoid_months": ["July", "August", "December", "January"],
                    "weather_info": "Mediterranean climate, hot summers, mild winters",
                    "peak_season": "April-June, September-October",
                    "temperature_range": "3°C to 30°C (37°F to 86°F)",
                    "rainfall": "Wettest in autumn and winter"
                },
                "Bangkok": {
                    "best_months": ["November", "December", "January", "February"],
                    "good_months": ["March", "October"],
                    "avoid_months": ["April", "May", "June", "July", "August", "September"],
                    "weather_info": "Tropical climate, hot and humid with distinct rainy season",
                    "peak_season": "November-February",
                    "temperature_range": "22°C to 35°C (72°F to 95°F)",
                    "rainfall": "Heavy monsoon May-October"
                },
                "Sydney": {
                    "best_months": ["September", "October", "November", "March", "April", "May"],
                    "good_months": ["February", "June"],
                    "avoid_months": ["July", "August"],
                    "weather_info": "Temperate climate, warm summers, mild winters (Southern Hemisphere)",
                    "peak_season": "September-November, March-May",
                    "temperature_range": "8°C to 26°C (46°F to 79°F)",
                    "rainfall": "Fairly even year-round, slightly more in autumn/winter"
                },
                "Mumbai": {
                    "best_months": ["November", "December", "January", "February", "March"],
                    "good_months": ["October", "April"],
                    "avoid_months": ["June", "July", "August", "September"],
                    "weather_info": "Tropical climate, intense monsoon season, hot and humid",
                    "peak_season": "November-February",
                    "temperature_range": "16°C to 38°C (61°F to 100°F)",
                    "rainfall": "Heavy monsoon June-September"
                }
            }

            # Default data for cities not in database
            default_weather = {
                "best_months": ["April", "May", "September", "October"],
                "good_months": ["March", "June", "November"],
                "avoid_months": ["December", "January", "February"],
                "weather_info": "Generally pleasant weather for travel",
                "peak_season": "April-October",
                "temperature_range": "Variable",
                "rainfall": "Seasonal variation"
            }

            city_weather = weather_data.get(city, default_weather)

            # Determine recommendation level
            if travel_month in city_weather["best_months"]:
                recommendation_level = "excellent"
                recommendation = f"Excellent time to visit {city}! {travel_month} is one of the best months."
            elif travel_month in city_weather.get("good_months", []):
                recommendation_level = "good"
                recommendation = f"Good time to visit {city}. {travel_month} offers decent weather conditions."
            elif travel_month in city_weather.get("avoid_months", []):
                recommendation_level = "not_recommended"
                recommendation = f"Not the ideal time for {city}. Consider visiting during: {', '.join(city_weather['best_months'][:3])}"
            else:
                recommendation_level = "fair"
                recommendation = f"Fair time to visit {city}, though {', '.join(city_weather['best_months'][:3])} would be better."

            return {
                "success": True,
                "city": city,
                "travel_month": travel_month,
                "recommendation_level": recommendation_level,
                "recommendation": recommendation,
                "weather_details": {
                    "best_months": city_weather["best_months"],
                    "good_months": city_weather.get("good_months", []),
                    "avoid_months": city_weather.get("avoid_months", []),
                    "weather_info": city_weather["weather_info"],
                    "peak_season": city_weather.get("peak_season", ""),
                    "temperature_range": city_weather.get("temperature_range", ""),
                    "rainfall_info": city_weather.get("rainfall", "")
                },
                "travel_tips": [
                    f"Peak season: {city_weather.get('peak_season', 'N/A')} - expect higher prices and crowds",
                    f"Best weather: {', '.join(city_weather['best_months'])}",
                    f"Temperature range: {city_weather.get('temperature_range', 'Variable')}",
                    "Book accommodations early during peak months"
                ]
            }

        except Exception as e:
            logger.error(f"Error in check_weather_recommendation: {e}")
            return {"error": "Failed to get weather recommendation. Please try again."}


# OpenAI Function Definitions
travel_functions = [
    {
        "name": "search_hotels",
        "description": "Search for hotels and accommodations in travel destinations with advanced filtering options",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The destination city for hotel search (e.g., Paris, Tokyo, New York)"
                },
                "budget_max": {
                    "type": "integer",
                    "description": "Maximum budget per night in USD (0-5000)"
                },
                "category": {
                    "type": "string",
                    "description": "Hotel category preference",
                    "enum": ["luxury", "mid-range", "budget"]
                },
                "check_availability": {
                    "type": "boolean",
                    "description": "Whether to check current hotel availability"
                }
            },
            "required": ["city"]
        }
    },
    {
        "name": "get_attractions",
        "description": "Find tourist attractions and points of interest for travel destinations",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The travel destination city for attractions search"
                },
                "category": {
                    "type": "string",
                    "description": "Category of attractions to explore",
                    "enum": ["Historical", "Museum", "Religious", "Landmark", "Shopping", "Cultural", "Entertainment",
                             "Nature", "Architecture", "Market"]
                },
                "max_entry_fee": {
                    "type": "integer",
                    "description": "Maximum entry fee budget for attractions in USD"
                }
            },
            "required": ["city"]
        }
    },
    {
        "name": "create_itinerary",
        "description": "Create detailed travel itineraries for specific destinations and durations",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The travel destination city for itinerary planning"
                },
                "duration_days": {
                    "type": "integer",
                    "description": "Number of days for the travel itinerary (1-14)"
                },
                "interests": {
                    "type": "string",
                    "description": "Travel interests and preferences (e.g., history, culture, food, adventure)"
                }
            },
            "required": ["city", "duration_days"]
        }
    },
    {
        "name": "get_travel_budget_estimate",
        "description": "Calculate comprehensive travel budget estimates for trips",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "Travel destination city for budget calculation"
                },
                "duration_days": {
                    "type": "integer",
                    "description": "Trip duration in days for budget planning (1-30)"
                },
                "accommodation_category": {
                    "type": "string",
                    "description": "Accommodation preference for budget calculation",
                    "enum": ["luxury", "mid-range", "budget"]
                }
            },
            "required": ["city", "duration_days"]
        }
    },
    {
        "name": "check_weather_recommendation",
        "description": "Get weather-based travel timing recommendations for destinations",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "Travel destination city for weather advice"
                },
                "travel_month": {
                    "type": "string",
                    "description": "Month of planned travel for weather recommendations",
                    "enum": ["January", "February", "March", "April", "May", "June", "July", "August", "September",
                             "October", "November", "December"]
                }
            },
            "required": ["city", "travel_month"]
        }
    }
]

# Function mapping for execution
function_mapping = {
    "search_hotels": TravelPlannerFunctions.search_hotels,
    "get_attractions": TravelPlannerFunctions.get_attractions,
    "create_itinerary": TravelPlannerFunctions.create_itinerary,
    "get_travel_budget_estimate": TravelPlannerFunctions.get_travel_budget_estimate,
    "check_weather_recommendation": TravelPlannerFunctions.check_weather_recommendation
}

# Session storage for conversation management
conversation_sessions = {}


def call_openai_with_functions(messages, session_id):
    """Call OpenAI API with advanced function calling capabilities"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            functions=travel_functions,
            function_call="auto",
            temperature=0.7,
            max_tokens=1000
        )
        return response

    except openai.error.RateLimitError:
        logger.warning("OpenAI rate limit exceeded")
        return None
    except openai.error.APIError as e:
        logger.error(f"OpenAI API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in OpenAI call: {e}")
        return None


@app.route('/')
def home():
    """Serve the main travel chatbot interface"""
    return render_template('travel_chatbot.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint with comprehensive security and travel validation"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id', 'default')

        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        # Initialize session if not exists
        if session_id not in conversation_sessions:
            conversation_sessions[session_id] = {
                'messages': [],
                'created_at': datetime.now(),
                'message_count': 0,
                'off_topic_warnings': 0,
                'security_violations': 0
            }

        session = conversation_sessions[session_id]
        session['message_count'] += 1

        # Rate limiting
        if session['message_count'] > 50:
            return jsonify({
                'error': 'Session limit reached. Please start a new chat for continued travel assistance.',
                'action': 'reset_required'
            }), 429

        # COMPREHENSIVE CONTENT VALIDATION
        validation_result = security_validator.validate_content(user_message, session_id)

        if not validation_result["is_safe"]:
            session['security_violations'] += 1
            security_logger.error(
                f"Security violation - Session: {session_id}, Type: {validation_result.get('category')}")

            # Auto-reset after security violations
            if session['security_violations'] >= 2:
                # Clear session
                conversation_sessions[session_id] = {
                    'messages': [],
                    'created_at': datetime.now(),
                    'message_count': 0,
                    'off_topic_warnings': 0,
                    'security_violations': 0
                }
                return jsonify({
                    'success': True,
                    'message': 'Chat has been reset due to security violations. Let\'s start fresh with safe travel planning!',
                    'session_reset': True,
                    'reason': 'security'
                })

            return jsonify({
                'success': True,
                'message': 'I can only assist with safe travel planning. Please ask about hotels, attractions, itineraries, or travel advice.',
                'blocked': True,
                'reason': 'security',
                'violations': session['security_violations']
            })

        if not validation_result["is_travel"]:
            session['off_topic_warnings'] += 1

            # Progressive warning system
            if session['off_topic_warnings'] == 1:
                response_msg = f"I\'m a travel planning assistant and can only help with travel-related queries. {validation_result.get('suggestion', 'Try asking about travel planning!')}"
            elif session['off_topic_warnings'] == 2:
                response_msg = f"I\'m specifically designed for travel planning only. Please ask about destinations, hotels, attractions, itineraries, or travel budgets."
            elif session['off_topic_warnings'] >= 3:
                response_msg = "I can ONLY assist with travel planning. I cannot help with other topics. Please ask about: hotels, attractions, itineraries, travel budgets, or destination recommendations."
            else:
                response_msg = f"I\'m here exclusively for travel assistance. {validation_result.get('suggestion', '')}"

            return jsonify({
                'success': True,
                'message': response_msg,
                'off_topic': True,
                'category': validation_result.get('category'),
                'warnings': session['off_topic_warnings'],
                'travel_examples': [
                    "Find luxury hotels in Paris under $400",
                    "Create a 5-day Tokyo itinerary",
                    "What\'s the budget for a Barcelona trip?",
                    "Best attractions in London",
                    "Weather in Dubai in December"
                ]
            })

        # Build travel-focused conversation context
        messages = [
            {
                "role": "system",
                "content": """You are an expert travel planning assistant. You specialize EXCLUSIVELY in helping travelers plan amazing trips.

Your capabilities include:
1. Hotel and accommodation searches with detailed filtering
2. Tourist attraction discovery and recommendations
3. Comprehensive travel itinerary creation
4. Accurate travel budget estimation
5. Weather-based travel timing advice

IMPORTANT GUIDELINES:
- You ONLY help with travel-related queries
- Use the available travel functions whenever appropriate
- Provide detailed, helpful, and enthusiastic travel advice
- Always prioritize user safety and practical travel recommendations
- Include specific details like prices, ratings, and practical tips
- Be conversational and engaging while remaining professional

Available destinations include Paris, London, Tokyo, New York, Dubai, Barcelona, Rome, Bangkok, Sydney, and Mumbai with comprehensive data for each location."""
            }
        ]

        # Add recent conversation history (last 10 messages)
        messages.extend(session['messages'][-10:])

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        # Call OpenAI with functions
        response = call_openai_with_functions(messages, session_id)

        if not response:
            return jsonify({
                'error': 'Travel planning service temporarily unavailable. Please try again.',
                'retry': True
            }), 500

        # Process the response
        response_message = response.choices[0].message

        # Check if AI wants to call a function
        if response_message.get("function_call"):
            function_name = response_message["function_call"]["name"]

            try:
                function_args = json.loads(response_message["function_call"]["arguments"])
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid function call from AI'}), 500

            logger.info(f"Travel function called: {function_name} with args: {function_args}")

            # Execute the travel function
            if function_name in function_mapping:
                function_result = function_mapping[function_name](**function_args)

                # Add function call and result to conversation
                function_call_message = {
                    "role": "assistant",
                    "content": None,
                    "function_call": {
                        "name": function_name,
                        "arguments": json.dumps(function_args)
                    }
                }

                function_result_message = {
                    "role": "function",
                    "name": function_name,
                    "content": json.dumps(function_result)
                }

                messages.append(function_call_message)
                messages.append(function_result_message)

                # Get final response from AI
                final_response = call_openai_with_functions(messages, session_id)

                if final_response:
                    final_message = final_response.choices[0].message.content

                    # Update session with travel conversation
                    session['messages'].extend([
                        {"role": "user", "content": user_message},
                        function_call_message,
                        function_result_message,
                        {"role": "assistant", "content": final_message}
                    ])

                    return jsonify({
                        'success': True,
                        'message': final_message,
                        'function_called': function_name,
                        'function_result': function_result,
                        'function_args': function_args,
                        'session_id': session_id,
                        'travel_query': True
                    })
                else:
                    # Fallback response
                    fallback_msg = f"I found travel information for you! {function_result.get('message', 'Here are the details for your travel query.')}"

                    session['messages'].extend([
                        {"role": "user", "content": user_message},
                        {"role": "assistant", "content": fallback_msg}
                    ])

                    return jsonify({
                        'success': True,
                        'message': fallback_msg,
                        'function_called': function_name,
                        'function_result': function_result,
                        'function_args': function_args,
                        'session_id': session_id,
                        'travel_query': True
                    })
            else:
                return jsonify({'error': f'Unknown travel function: {function_name}'}), 400
        else:
            # Regular response without function calling
            regular_response = response_message.content

            # Update session
            session['messages'].extend([
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": regular_response}
            ])

            return jsonify({
                'success': True,
                'message': regular_response,
                'session_id': session_id,
                'travel_query': True
            })

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({
            'error': 'Travel assistance temporarily unavailable. Please try again.',
            'technical_error': str(e)
        }), 500


@app.route('/api/reset-chat', methods=['POST'])
def reset_chat():
    """Reset chat session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')

        # Clear session data
        if session_id in conversation_sessions:
            del conversation_sessions[session_id]

        logger.info(f"Travel chat session {session_id} reset")

        return jsonify({
            'success': True,
            'message': 'Chat reset! Ready to help you plan your next adventure. Where would you like to travel?',
            'session_reset': True
        })

    except Exception as e:
        logger.error(f"Error resetting chat: {e}")
        return jsonify({'error': 'Failed to reset chat. Please refresh the page.'}), 500


@app.route('/api/travel-destinations', methods=['GET'])
def get_travel_destinations():
    """Get available travel destinations"""
    try:
        destinations = []
        if not hotels_df.empty:
            cities = hotels_df['city'].unique()
            countries = hotels_df.groupby('city')['country'].first().to_dict()

            for city in sorted(cities):
                hotel_count = len(hotels_df[hotels_df['city'] == city])
                attraction_count = len(
                    attractions_df[attractions_df['city'] == city]) if not attractions_df.empty else 0

                destinations.append({
                    'city': city,
                    'country': countries[city],
                    'hotels_available': hotel_count,
                    'attractions_available': attraction_count
                })

        return jsonify({
            'success': True,
            'destinations': destinations,
            'total_cities': len(destinations)
        })

    except Exception as e:
        logger.error(f"Error getting destinations: {e}")
        return jsonify({'error': 'Failed to load destinations'}), 500


@app.route('/api/functions', methods=['GET'])
def get_available_functions():
    """Get available travel functions"""
    return jsonify({
        'functions': [
            {
                'name': func['name'],
                'description': func['description'],
                'parameters': func['parameters']
            }
            for func in travel_functions
        ],
        'scope': 'travel_planning_only'
    })


@app.route('/api/session-status', methods=['GET'])
def session_status():
    """Get current session status"""
    try:
        session_id = request.args.get('session_id', 'default')

        if session_id in conversation_sessions:
            session = conversation_sessions[session_id]
            return jsonify({
                'success': True,
                'session_active': True,
                'message_count': session['message_count'],
                'off_topic_warnings': session['off_topic_warnings'],
                'security_violations': session['security_violations'],
                'created_at': session['created_at'].isoformat()
            })
        else:
            return jsonify({
                'success': True,
                'session_active': False
            })

    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        return jsonify({'error': 'Failed to get session status'}), 500


if __name__ == '__main__':
    # Clean up old sessions on startup
    conversation_sessions.clear()
    logger.info(" Travel Planner AI Chatbot starting - Advanced implementation with security and function calling")
    app.run(debug=True, port=5000, host='0.0.0.0')
