from typing import Dict, List, Optional, Any
from openai import OpenAI
from openai.types.chat import ChatCompletion
import json
from dotenv import load_dotenv
import os
import logging
from utils.data_models import SearchPreferences, ProductInfo, AgentContext
from tools.scraper_integration import ScraperManager

load_dotenv()
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



class AmazonShoppingAgent:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.context = AgentContext()
        self.tools = tools
        self.scraper_manager = ScraperManager(headless=True)

    def _chat_completion(self, messages: List[Dict[str,str]]) -> ChatCompletion:
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                *self.context.conversation_history,
                *messages
            ],
            temperature=0.1,
            tools=self.tools,
            response_format={"type": "text"}
        )
        return response
    
    def __del__(self):
        """
        This will ensure that the scraper is closed when the agent is destroyed.
        """
        if hasattr(self, 'scraper_manager'):
            self.scraper_manager.close()

    def process_query(self, user_query: str):
        system_prompt = """
        You are a helpful assistant that parses user shopping queries and extracts search preferences. In particular
        you will be parsing queries from the user that are for products on Amazon.com.

        Available to you are the following tools:
        - search_amazon: to search for products on Amazon.com

        You need to determine if the user's query requires a new search or can be answered using the latest existing search results.

        Here are the rules:
        1. If they are asking about a new product or have a refinement that is vastly different from the latest 
        existing search preferences (or have never done a search before), extract the new search preferences
        and perform a new search using the search_amazon tool. Once you have the results, you should rank the products
        based on how well they match the user's preferences. 

        2. If they are asking about current search results or making a minor refinement,
        answer using the latest existing search results without performing a new search.

        3. If the user is making a nonsense or unrelated query, just say "I'm sorry, I don't understand that."
        
        Be judicious about when to search. Only perform a new search when truly necessary (such as when you cannot answer the 
        user's query based on the latest existing search results).
        """

        try:
            if self.context.current_results:
                results_summary = f"\nThe most recent search found {len(self.context.current_results)} products matching these criteria."
                results_summary += "\nCurrent search results include:\n"
                for product in self.context.current_results:
                    results_summary += f"- {product.product_name} (Price: ${product.price}, Rating: {product.rating}/5, Prime Eligible: {product.is_prime_eligible}, Description: {product.description})"
                system_prompt += results_summary
            response = self._chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ]
            )

            assistant_message = response.choices[0].message

            self.context.conversation_history.extend([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query},
                {"role": "assistant", "content": assistant_message.content, "tool_calls": assistant_message.tool_calls}
            ])

            if hasattr(assistant_message, "tool_calls") and assistant_message.tool_calls:
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    logger.info(f"Using tool: {tool_name}")

                    if tool_name == "search_amazon":
                        search_results = self._search_amazon_tool(**args)
                        self.context.current_results = search_results
                        self.context.has_active_search = True
                        self.context.current_preferences = SearchPreferences(**args)
                        self.context.conversation_history.append({
                            "role": "tool",
                            "name": "search_amazon",
                            "content": json.dumps([product.model_dump() for product in search_results]),
                            "tool_call_id": tool_call.id
                        })
                final_prompt = """
                Based on the above, provide a final response to the user's query.
                """
                final_response = self._chat_completion(
                    messages=[
                        {"role": "system", "content": final_prompt},
                    ]
                )
                final_content = final_response.choices[0].message.content
                
                self.context.conversation_history.append({
                    "role": "assistant",
                    "content": final_content
                })
                
                return final_content
            else:
                return assistant_message.content

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            raise e
        

    def _search_amazon_tool(self, **kwargs) -> List[ProductInfo]:
        """
        Uses the Selenium AmazonScraper to search for products on Amazon
        """
        try:
            search_preferences = SearchPreferences(**kwargs)
            logger.info(f"Agent searching for {search_preferences.query} on Amazon....")
            products = self.scraper_manager.search_amazon(search_preferences)
            return products
        except Exception as e:
            logger.error(f"Search tool error: {e}")
            return []
    
    def _rank_products_tool(self, products: List[ProductInfo], preferences: SearchPreferences):

        products_json = json.dumps([product.model_dump() for product in products])
        preferences_json = json.dumps(preferences.model_dump())

        system_prompt = """
        You are a product ranking expert, with a particular focus on Amazon products.
        Your job is to evaluate a list of products against user preferences and return a ranked list of products
        based on how well they match the user's preferences.

        For each product, provide:
        1. A numeric score (0-100)
        2. A rank position (1 is best)
        3. Specific reasons why this product matches the preferences
        4. Any potential concerns or drawbacks

        Return your analysis as a JSON object with the following structure:
        {
            "ranked_products": [
                {
                    "product": {original product object},
                    "rank": int,
                    "score": float,
                    "match_reasons": ["reason1", "reason2", ...],
                    "concerns": ["concern1", "concern2", ...]
                },
                ...
            ],
            "top_pick": {same structure as above},
            "preferences_used": {preferences object},
            "ranking_explanation": "string explaining ranking methodology"
        }
        """

        user_prompt = f"""
        Analyze these products:
        {products_json}
        
        Based on these user preferences:
        {preferences_json}
        """
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )

            content = response.choices[0].message.content
            ranking_data = json.loads(content)
            
            return ranking_data
        except Exception as e: 
            raise ValueError(f"Failed to rank products: {e}")

tools = [{
    "type": "function",
    "function": {
        "name": "search_amazon",
        "description": "Search for products on Amazon.com",
        "parameters":{
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query for the product"
                },
                "price_range": {
                    "type": "object",
                    "description": "The price range for the product",
                    "properties": {
                        "minPrice": {
                            "type": ["number", "null"],
                            "description": "The minimum price for the product"
                        },
                        "maxPrice": {
                            "type": ["number", "null"],
                            "description": "The maximum price for the product"
                        }
                    },
                },
                "rating_range": {
                    "type": "object",
                    "description": "The rating range for the product",
                    "properties": {
                        "minRating": {
                            "type": ["number", "null"],
                            "description": "The minimum rating for the product"
                        },
                        "maxRating": {
                            "type": ["number", "null"],
                            "description": "The maximum rating for the product"
                        }
                    }
                },
                "is_prime_eligible": {
                    "type": "boolean",
                    "description": "Whether the product is prime eligible"
                }
            }
        }
    }
}]