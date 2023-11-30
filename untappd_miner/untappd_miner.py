from dotenv import dotenv_values
from pathlib import Path
from typing import Optional, Union

import httpx
from bs4 import BeautifulSoup

class UntappdMiner:    
    def __init__(self, dotenv_file: str | None = None) -> None:
        self.dotenv_file = dotenv_file
             
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
    def _fetch_url(
        self, 
        url: str, 
        headers: dict | None = None, 
        params: dict | None = None
    ) -> httpx.Response:
        try:
            res = httpx.get(url=url, headers=headers, params=params)
            res.raise_for_status()
            
            content_type = res.headers["content-type"]
            if "text/html" in content_type:
                return res.text
            elif "application/json":
                return res.json()
            else:
                return res
        except httpx.RequestError as e:
            print(f"An error occured for request: {e}")
            raise e
    
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
        
        res = self._fetch_url(url, params=params)
        return res
    
class UntappdWebMiner(UntappdMiner):
    BASE_URL = "https://untappd.com"
    BEER_TR_ENDPOINT = "/beer/top_rated"
    BREWERY_TR_ENDPOINT = "/brewery/top_rated"
    
    def __init__(self, dotenv_file: str | None = None, user_agent: str | None = None) -> None:
        super().__init__(dotenv_file)
        self._user_agent = self.__ua_setter_on_init(user_agent)    # Set a default UA if none provided
        
    @property
    def user_agent(self) -> str:
        return self._user_agent
    
    @user_agent.setter
    def user_agent(self, custom_ua: str | None):
        self._user_agent = custom_ua
        
    def get_top_rated_breweries(self, ) -> dict[str, str]:
        pass
        
    def _get_countries_slug(self, endpoint: str) -> list[str]:
        # Validate and construct endpoint
        endpoints = ["beer", "brewery"]
        if endpoint not in endpoints:
            raise ValueError(f"'endpoint' must be one of {endpoints}")
        
        if endpoint == endpoint[0]:
            url = self.BASE_URL + self.BEER_TR_ENDPOINT
        
        if endpoint == endpoints[1]:
            url = self.BASE_URL + self.BREWERY_TR_ENDPOINT
        
        # Get source from given endpoint
        headers = {"User-Agent": self._user_agent}
        html = self._fetch_url(url=url, headers=headers)
        
        # Fetch countries from endpoint
        soup = BeautifulSoup(html, "html.parser")
        selecter_country_id = soup.find(id="sort_picker")

        countries = []
        for option in selecter_country_id.find_all("option"):
            if "data-value-slug" in option.attrs:
                countries.append(option["data-value-slug"])
        return countries
        
    def __ua_setter_on_init(self, ua_init: str | None) -> str:
        # Set default otherwise pick from .env
        if ua_init is None and self.parse_dotenv(self._dotenv_file, "USER_AGENT") is None:
            ua = "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"
        elif ua_init is None:
            ua = self.parse_dotenv(self._dotenv_file, "USER_AGENT")
        else:    # Hardcoded ua
            ua = ua_init
        return ua
        
        
        