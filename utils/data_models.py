from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class PriceRange(BaseModel):
    minPrice: Optional[float] = None
    maxPrice: Optional[float] = None


class RatingRange(BaseModel):
    minRating: Optional[float] = None
    maxRating: Optional[float] = None

class ProductInfo(BaseModel):
    product_name: str;
    price: float;
    rating: float;
    is_prime_eligible: bool;
    description: Optional[str] = None
    reviews: Optional[List[str]] = None


class SearchPreferences(BaseModel):
    query: str = Field(..., description="The search query for the product")
    price_range: PriceRange = Field(default_factory=PriceRange, description="The price range for the product")
    rating_range: RatingRange = Field(default_factory=RatingRange, description="The rating range for the product")
    is_prime_eligible: bool = Field(default=False, description="Whether to show only prime eligible products")
    ## TODO: Add more fields.

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)

    def to_search_filters(self) -> Dict[str, Any]:
        filters = {}
        filters["price_range"] = self.price_range
        filters["rating_range"] = self.rating_range
        filters["is_prime_eligible"] = self.is_prime_eligible
        return filters
    

class AgentContext:
    def __init__(self):
        self.current_preferences: Optional[SearchPreferences] = None        
        self.conversation_history: List[Dict[str, str]] = []
        self.current_results: List[ProductInfo] = []
        self.has_active_search: bool = False
    
    def update_search(self, preferences: SearchPreferences, results: List[ProductInfo]):
        self.current_preferences = preferences
        self.current_results = results
        self.has_active_search = True
    
    def clear(self):
        self.current_preferences = None
        self.current_results = []
        self.has_active_search = False
        self.conversation_history = []