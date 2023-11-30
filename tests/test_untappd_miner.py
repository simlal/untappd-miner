from untappd_miner import UntappdMiner, UntappdWebMiner
import unittest

class TestUntappdMiner(unittest.TestCase):
    def setUp(self):
        self.miner_default = UntappdMiner(None)
        self.miner_dotenv = UntappdMiner()
        self.miner_chromeua = UntappdMiner()
        
        self.base_url = UntappdWebMiner().BASE_URL
        
    # TODO TEST .env
    
    def test_base_url(self):
        res = self.miner_default.fetch_url(self.base_url)
        self.assertEqual(res.status_code, 200)
    
    def test_parse_response_text(self):
        res = self.miner_default.fetch_url(self.base_url)
        parsed_res = self.miner_default._parse_response(res)
        self.assertIsInstance(parsed_res, str)
        
    # TODO test JSON PARSER
class TestUntappdWebMiner(unittest.TestCase):
    def setUp(self):
        self.webminer = UntappdWebMiner()
        
    def test_beer_tr_endpoint(self):
        beer_tr_endpoint = self.webminer.BASE_URL + self.webminer.BEER_TR_ENDPOINT
        res = self.webminer.fetch_url(beer_tr_endpoint)
        self.assertEqual(res.status_code, 200)
    
    def test_brewey_tr_endpoint(self):
        brewery_tr_endpoint = self.webminer.BASE_URL + self.webminer.BREWERY_TR_ENDPOINT
        res = self.webminer.fetch_url(brewery_tr_endpoint)
        self.assertEqual(res.status_code, 200)
    
    def test_get_countries_slug_beer(self):
        countries = self.webminer._get_countries_slug("beer")
        self.assertIsInstance(countries, list)
        self.assertTrue(len(countries) > 0)
    
    def test_get_countries_slug_brewery(self):
        countries = self.webminer._get_countries_slug("brewery")
        self.assertIsInstance(countries, list)
        self.assertTrue(len(countries) > 0)
