import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from fastapi import FastAPI
from fastapi.testclient import TestClient
import saved_locations as s

class SavedLocationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.old=s.DB_PATH;s.DB_PATH=Path(self.tmp.name)/'locations.db'
        self.auth=patch.object(s,'get_token_user',return_value=7);self.auth.start()
        self.update=patch.object(s,'update_location',side_effect=lambda data,authorization:{'lng':data.lng,'lat':data.lat,
            'alt':None,'address':'测试地点','nearest_station':{'id':'54830','name':'淄博'}});self.update.start()
        app=FastAPI();app.include_router(s.router);self.client=TestClient(app)
    def tearDown(self):
        self.auth.stop();self.update.stop();s.DB_PATH=self.old;self.tmp.cleanup()
    def test_real_boundary(self):
        self.assertTrue(s.in_shandong(118.055,36.813))
        self.assertFalse(s.in_shandong(116.4074,39.9042))
    def test_add_select_delete_and_ownership(self):
        response=self.client.post('/auth/locations',json={'lng':118.055,'lat':36.813,'name':'家'})
        self.assertEqual(response.status_code,200);place=response.json()['location']
        self.assertEqual(self.client.get('/auth/locations').json()['locations'][0]['name'],'家')
        self.assertEqual(self.client.put(f'/auth/locations/{place["id"]}/select').status_code,200)
        with patch.object(s,'get_token_user',return_value=8):
            self.assertEqual(self.client.put(f'/auth/locations/{place["id"]}/select').status_code,404)
            self.assertEqual(self.client.delete(f'/auth/locations/{place["id"]}').status_code,404)
        self.assertEqual(self.client.delete(f'/auth/locations/{place["id"]}').status_code,200)
    def test_outside_duplicate_and_limit(self):
        self.assertEqual(self.client.post('/auth/locations',json={'lng':116.4,'lat':39.9}).status_code,400)
        for i in range(5):
            self.assertEqual(self.client.post('/auth/locations',json={'lng':117+i*.01,'lat':36.6,'name':str(i)}).status_code,200)
        self.assertEqual(self.client.post('/auth/locations',json={'lng':117.1,'lat':36.6}).status_code,400)
    def test_search_only_returns_shandong(self):
        response=SimpleNamespace()
        response.raise_for_status=lambda:None
        response.json=lambda:[{'name':'淄博','display_name':'淄博市, 山东省','lon':'118.05','lat':'36.81'},
                              {'name':'北京','display_name':'北京市','lon':'116.4','lat':'39.9'}]
        with patch.object(s.requests,'get',return_value=response):
            result=self.client.get('/auth/locations/search',params={'q':'淄博'}).json()['results']
        self.assertEqual(len(result),1);self.assertEqual(result[0]['name'],'淄博')

if __name__=='__main__':unittest.main()
