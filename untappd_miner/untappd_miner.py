from dotenv import dotenv_values
from pathlib import Path
from typing import Optional, Union
import time
from datetime import date, datetime
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup

@dataclass
class CheckinStats():
    total: int
    unique: int
    monthly: int
    current_user: int
    
@dataclass
class BreweryCheckinStats(CheckinStats):
    likes: int

@dataclass
class BreweryDetails():
    description: str
    checkin_stats: BreweryCheckinStats
    likers_sample: list[str]
    brewery_locations: list[str]    # Brewery-tied venue ids
    top_beers: list[int]    # Beer ids
    all_beers: list[int]   # Beer ids
    popular_locations: list[str]   # Popular Venue ids
@dataclass
class Brewery():
    id_url: str
    fullname: str
    city: str
    region: str
    country: str
    brewery_type: str
    number_of_beers: int
    total_ratings: int
    weight_avg_ratings: float
    details: BreweryDetails
        
@dataclass 
class Venue():
    id_venue: int
    name: str
    adress: str
    map_url: str
    is_verified: bool
    details: list[str]
    stats: CheckinStats
    loyal_patrons: list[str]    # user ids
    num_beers_on_menu: int    # Might be null

@dataclass
class BeerRating():
    user_id: str
    checkin_venue: str    # venue endpoint/id
    serving_type: str
    comment: str
    purchased_at: str    # venue endpoint/id
    number_tagged_friends: int
    has_picture: bool
    checkin_time: datetime

@dataclass
class BeerDetails():
    checkin_stats: CheckinStats
    description: str
    loyal_drinkers: list[str]    # user id for /user/id endpoint
    similar_beers: list[int]    # beer ids
    verified_locations: list[str]    # venue ids
    individual_ratings: BeerRating
#TODO FINISH IMPLEMENTATION
@dataclass
class Beer():
    id_url: str    # unique beer for endpoint /b/slug/bid
    bid: int    # beer id (part of id_url)
    brewery_id: str
    name: str
    style: str
    abv: float
    ibu: int
    weight_avg_ratings: float
    total_ratings: int
    date_added: date
    details: BeerDetails
    
        
#TODO USER AND SUPERUSER DATACLASS?
    
class UntappdMiner:    
    def __init__(self, dotenv_file: str | None = None) -> None:
        self.dotenv_file = dotenv_file
        self.client = httpx.Client()    # Init a client to store/send cookies
        self.breweries = {}    # keys will be unique url/id
        self.beers = {}
             
    @property
    def dotenv_file(self) -> Union[Path, None]:
        return self._dotenv_file
    
    @dotenv_file.setter
    def dotenv_file(self, dotenv_file: str | Path | None) -> None:
        # Default to .env if present
        if dotenv_file is None and Path(".env").exists():
            dotenv_file = ".env"            
        
        # Convert to Path object if .env present
        if dotenv_file is not None and not isinstance(dotenv_file, Path):
            dotenv_file = Path(dotenv_file)
        self._dotenv_file = dotenv_file
        
    # Basic get request
    def fetch_url(
        self, 
        url: str, 
        headers: dict | None = None, 
        params: dict | None = None,
        max_retries: int = 3,
    ) -> httpx.Response:
        for i in range(max_retries):
            try:
                print(f"Fetching data from {url} with {params=}")
                res = self.client.get(url=url, headers=headers, params=params)
                res.raise_for_status()
                return res
            except httpx.RequestError as e:
                print(f"An error occured for request: {e}")
                if i == max_retries - 1:
                    raise e
                time.sleep(1)
    
    def parse_response(self, res: httpx.Response) -> dict | str:
        content_type = res.headers["content-type"]
        if "text/html" in content_type:
            return res.text
        elif "application/json" in content_type:
            return res.json()
        else:
            return res
    
    @staticmethod
    def parse_dotenv(dotenv_file: Path | None, key: str) -> dict | None:
        # dotenv file is optional for webminer
        if dotenv_file is None:
            return None
        
        config = dotenv_values(dotenv_file)
        value = config[key] if key in config else None
        return value
        

class UntappdApiMiner(UntappdMiner):
    BASE_API = "https://api.untappd.com"
    
    def __init__(self, dotenv_file: str | None = None) -> None:
        super().__init__(dotenv_file)
        self._client_id = None
        self._client_secret = None
        if self._dotenv_file is not None:    # For API-related methods
            self._client_id = self.parse_dotenv(self._dotenv_file, "CLIENT_ID")
            self._client_secret = self.parse_dotenv(self._dotenv_file, "CLIENT_SECRET")
        self._post_req_counter = 0
    
    @property
    def post_req_counter(self) -> int:
        return self._post_req_counter
    
    @post_req_counter.setter
    def post_req_counter(self, value: int) -> None:
        self._post_req_counter = value
    
    def get_brewery_info_API(self, brewery_id: int):
        # Construct url for endpoint
        endpoint = f"/v4/brewery/info/{str(brewery_id)}"
        url = self.BASE_API_URL + endpoint
        print(f"Fetching {url}...")
        
        # Client credentials for get request
        params = {
            "client_id": self._client_id,
            "client_secret": self._client_secret
        }        
        
        res = self.fetch_url(url, params=params)
        return res
    
class UntappdWebMiner(UntappdMiner):
    BASE_URL = "https://untappd.com"
    BEER_TR_ENDPOINT = "/beer/top_rated"
    BREWERY_TR_ENDPOINT = "/brewery/top_rated"
    
    ENDPOINT_TR_NAMES = ["beer", "brewery"]
    
    def __init__(self, dotenv_file: str | None = None, user_agent: str | None = None) -> None:
        super().__init__(dotenv_file)
        self._user_agent = self.__ua_setter_on_init(user_agent)    # Set a default UA if none provided
        
    @property
    def user_agent(self) -> str:
        return self._user_agent
    
    @user_agent.setter
    def user_agent(self, custom_ua: str | None):
        self._user_agent = custom_ua
        
    def get_top_rated_breweries(self, country: str = "all", brewery_type: str = "all") -> Brewery:
        possible_countries = self._get_countries_slug(endpoint="brewery")
        possible_btypes = self._get_brewery_type_slug()
        
        # Validate country and brewery_type
        countries = possible_countries if country == "all" else None
        if country not in possible_countries and countries is None:
            raise ValueError(f"'country' must be one of {possible_countries}")
        countries = [country] if countries is None else countries

        brewery_types = possible_btypes if brewery_type == "all" else None
        if brewery_type not in possible_btypes and brewery_types is None:
            raise ValueError(f"'country' must be one of {possible_btypes}")
        brewery_types = [brewery_type] if brewery_types is None else brewery_types
        
        # Get all data for each possible endpoint
        url = self.BASE_URL + self.BREWERY_TR_ENDPOINT
        headers = {"User-Agent": self._user_agent} 
        for c_slug in countries:
            country_name = self.__country_name_from_slug(c_slug)
            for btype in brewery_types:
                # Per country and brewery_type request
                params = {"country": c_slug, "brewery_type": btype}
                response = self.fetch_url(url=url, headers=headers, params=params)
                html = self.parse_response(response)
                # print(html)
                
                # Skip if content is empty
                if self.__empty_content(html, endpoint_name="brewery"):
                    print(f"Empty content for country: {c_slug} and brewery_type: {btype}")
                    continue
            
                soup = BeautifulSoup(html, "html.parser")
                beer_items = soup.find_all("div", {"class": "beer-item"})
                for bi in beer_items:
                    # Get the TopRated data first
                    brewery_data_dict = {}
                    
                    # id_url is the unique identifier and endpoint for brewery
                    pname = bi.find("p", {"class": "name"})
                    brewery_data_dict["id_url"] = pname.find("a").attrs["href"].strip()
                    brewery_data_dict["fullname"] = pname.text.strip()
                    
                    # Geography can be city, region country or city, country or country
                    pstyle = bi.find_all("p", {"class": "style"})
                    geography = pstyle[0].text.strip()
                    brewery_data_dict["city"] = geography.split(",")[0].strip() if "," in geography else None
                    region_country_temp = geography.split(",")[1].strip() if "," in geography else geography
                    region_temp = region_country_temp.split(" ") if " " in region_country_temp else None
                    if region_temp is not None:
                        region_temp = self.__remove_rightmost_country(country_name, region_temp)
                        brewery_data_dict["region"] = " ".join(region_temp)
                    else:
                        brewery_data_dict["region"] = None
                    brewery_data_dict["country"] = country_name
                    brewery_data_dict["brewery_type"] = pstyle[1].text.strip()
                    
                    # Aggregated stats from top-rated
                    div_details = bi.find("div", {"class": "details brewery"})
                    num_beers_temp = div_details.find("p", {"class": "abv"}).text.strip()
                    brewery_data_dict["number_of_beers"] = int(num_beers_temp.split(" ")[0].replace(",", ""))
                    num_ratings_temp = div_details.find("p", {"class": "ibu"}).text.strip()
                    brewery_data_dict["total_ratings"] = int(num_ratings_temp.split(" ")[0].replace(",", ""))
                    div_rating = bi.find("div", {"class": "rating"})
                    brewery_data_dict["weight_avg_ratings"] = float(div_rating.find("div", {"class": "caps"}).attrs["data-rating"])
                    print(brewery_data_dict)
                    
                    # TODO GET BREWERY DETAILS
                    # Add to breweries container based on dataclass
                    # brewery_data = Brewery()
                    # if brewery_data.id_url not in self.breweries:
                    #     self.breweries[brewery_data.id_url] = brewery_data
                    # print(self.breweries)
                    
        # Get the BreweryDetails data
        for brewery_id in self.breweries:
            pass
    
                    
                    
    #TODO GET DATA FROM THE BREWERY PAGE     
    def get_brewery_details(self, brewery_id: str, detailed_checkins: bool=False) -> Brewery:
        try :
            brewery_id = str(brewery_id)
        except:
            raise TypeError("'brewery_id' must be a string.")
        
        # Get the base page for a given brewery
        url = self.BASE_URL + f"/{brewery_id}"
        headers = {"User-Agent": self._user_agent}
        response = self.fetch_url(url=url, headers=headers)
        html = self.parse_response(response)
             
        # TODO get 
        
        
    
    #TODO GET DATA FROM THE VENUE PAGE
    def get_venue_details(self, venue_id: int) -> Venue:
        pass
    
    #TODO GET DATA 
    def get_beers_from_brewery(self, brewery_id: int) -> list[Beer]:
        pass
    
    #TODO GET DATA FROM THE BEER PAGE
    def get_beer_details(self, beer_id: int) -> Beer:
        pass
    
    # TODO GET LAST 500 ratings for a beer  
    def get_all_beer_ratings(self, beer_id: int) -> list[dict]:
        pass
    
    def _get_countries_slug(self, endpoint: str) -> list[str]:
        # Validate and construct endpoint 0=beer 1=brewery
        if endpoint not in self.ENDPOINT_TR_NAMES:
            raise ValueError(f"'endpoint' must be one of {self.ENDPOINT_TR_NAMES}")
        
        if endpoint == self.ENDPOINT_TR_NAMES[0]:
            url = self.BASE_URL + self.BEER_TR_ENDPOINT
        
        if endpoint == self.ENDPOINT_TR_NAMES[1]:
            url = self.BASE_URL + self.BREWERY_TR_ENDPOINT
        
        # Get source from given endpoint
        headers = {"User-Agent": self._user_agent}
        response = self.fetch_url(url=url, headers=headers)
        html = self.parse_response(response)
        
        # Fetch countries from endpoint
        soup = BeautifulSoup(html, "html.parser")
        selecter_country_id = soup.find(id="sort_picker")

        countries = []
        for option in selecter_country_id.find_all("option"):
            if "data-value-slug" in option.attrs:
                countries.append(option["data-value-slug"])
        return countries
    
    def _get_brewery_type_slug(self, exclude_cider_mead: bool = False) -> list[str]:
        url = self.BASE_URL + self.BREWERY_TR_ENDPOINT
        
        # Get source from given endpoint
        headers = {"User-Agent": self._user_agent}
        response = self.fetch_url(url=url, headers=headers)
        html: str = self.parse_response(response)
        
        # Fetch brewerytypes from endpoint
        soup = BeautifulSoup(html, "html.parser")
        selecter_btypes = soup.find(id="filter_picker")

        brewery_types = []
        for option in selecter_btypes.find_all("option"):
            if "data-value-slug" in option.attrs:
                brewery_types.append(option["data-value-slug"])
        
        if exclude_cider_mead:
            brewery_types = [btype for btype in brewery_types if btype not in ["cidery", "meadery"]]
        return brewery_types
    
    ### Internal helpers ###
    
    def __ua_setter_on_init(self, ua_init: str | None) -> str:
        # Set default otherwise pick from .env
        if ua_init is None and self.parse_dotenv(self._dotenv_file, "USER_AGENT") is None:
            ua = "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"
        elif ua_init is None:
            ua = self.parse_dotenv(self._dotenv_file, "USER_AGENT")
        else:    # Hardcoded ua
            ua = ua_init
        return ua
    
    def __empty_content(self, html: str, endpoint_name: str) -> bool:
        if html == "" or html is None:
            raise ValueError(f"Empty content for endpoint: {endpoint_name}")
        
        if endpoint_name not in self.ENDPOINT_TR_NAMES:
            raise ValueError(f"'endpoint' must be one of {self.ENDPOINT_TR_NAMES}")
        
        # Check content according to toprated endpoint 0=beer 1=brewery
        soup = BeautifulSoup(html, "html.parser")
        
        # TODO Figure out what the empty ocntent of beers would be
        if endpoint_name == self.ENDPOINT_TR_NAMES[0]:
            pass
        if endpoint_name == self.ENDPOINT_TR_NAMES[1]:
            ptags = soup.find_all("p", attrs={"class": "no-activity"})
            return len(ptags) > 0    # presence no-activity p-tag means empty content
    
    def __country_name_from_slug(self, slug: str) -> str:
        country_name = " ".join(slug.split("-")).title()
        return country_name
    
    def __remove_rightmost_country(self, country_name: str, state_country_list: list[str]) -> list[str]:
        scl_reversed = state_country_list[::-1]
        if country_name in scl_reversed:
            scl_reversed.remove(country_name)
        scl_normal = scl_reversed[::-1]
        return scl_normal
        
            
        