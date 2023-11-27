from dotenv import dotenv_values
from pathlib import Path
import httpx
from typing import Optional, Union
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
    BASE_API_URL = "https://api.untappd.com"
    
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
        return res.json()
    
class UntappdWebMiner(UntappdMiner):
    BASE_URL = "https://untappd.com/"
    
    def __init__(self, dotenv_file: str | None = None, custom_ua: str | None = None) -> None:
        super().__init__(dotenv_file)
        self.user_agent = custom_ua    # Set a default UA if none provided
        
    @property
    def user_agent(self) -> str:
        return self._user_agent
    
    @user_agent.setter
    def user_agent(self, custom_ua: str | None):
        # Required for proper parsing
        print(self.parse_dotenv(self._dotenv_file, "USER_AGENT"))
        if custom_ua is None and self.parse_dotenv(self._dotenv_file, "USER_AGENT") is None:
            custom_ua = "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"
        else:
            custom_ua = self.parse_dotenv(self._dotenv_file, "USER_AGENT")
        
        self._user_agent = custom_ua
        
    # Get beer-related data for a single brewery
    def get_beers_per_brewery(self, brewery_name: str) -> dict[str, str]:
        beer_endpoint=f"{self.BASE_URL}{brewery_name}/beer"
        res = self._fetch_url(beer_endpoint)
        print(res.status_code)