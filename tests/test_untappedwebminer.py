from untappd_miner import UntappdWebMiner
import unittest

class TestUntappdWebMiner(unittest.TestCase):
    
    def setUp(self):
        self.miner = UntappdWebMiner()
        
    def test_base_url(self):
        base_url = self.miner.BASE_URL
        res = self.miner.fetch_url(base_url)
        self.assertEqual(res.status_code, 200)
        
    def test_parse_response_text(self):
        res = self.miner.fetch_url(self.miner.BASE_URL)
        parsed_res = self.miner._parse_response(res)
        self.assertIsInstance(parsed_res, str)
        
    def test_beer_tr_endpoint(self):
        beer_tr_endpoint = self.miner.BASE_URL + self.miner.BEER_TR_ENDPOINT
        res = self.miner.fetch_url(beer_tr_endpoint)
        self.assertEqual(res.status_code, 200)
    
    def test_brewey_tr_endpoint(self):
        brewery_tr_endpoint = self.miner.BASE_URL + self.miner.BREWERY_TR_ENDPOINT
        res = self.miner.fetch_url(brewery_tr_endpoint)
        self.assertEqual(res.status_code, 200)
    
    def test_get_countries_slug_beer(self):
        countries = self.miner._get_countries_slug("beer")
        self.assertIsInstance(countries, list)
        self.assertTrue(len(countries) > 0)
    
    def test_get_countries_slug_brewery(self):
        countries = self.miner._get_countries_slug("brewery")
        self.assertIsInstance(countries, list)
        self.assertTrue(len(countries) > 0)
