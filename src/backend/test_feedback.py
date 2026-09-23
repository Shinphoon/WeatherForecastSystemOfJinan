import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import Mock, patch
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
import feedback

class FeedbackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old = feedback.DB_PATH
        feedback.DB_PATH = Path(self.temp.name) / 'test.sqlite3'
        self.user_id = 2
        self.auth = patch.object(feedback, 'get_token_user', side_effect=lambda _: self.user_id)
        def admin(_):
            if self.user_id != 1: raise HTTPException(status_code=403, detail='仅管理员')
        self.admin = patch.object(feedback, 'require_admin', side_effect=admin)
        conn = Mock(); conn.cursor.return_value.fetchone.return_value = SimpleNamespace(username='tester')
        self.db = patch.object(feedback,'get_connection',return_value=conn)
        for p in (self.auth,self.admin,self.db): p.start()
        app = FastAPI(); app.include_router(feedback.router); self.client = TestClient(app)
    def tearDown(self):
        for p in (self.auth,self.admin,self.db): p.stop()
        feedback.DB_PATH = self.old; self.temp.cleanup()
    def test_persistence_ownership_and_admin_status(self):
        body = {'category':'功能建议','content':'希望增加天气查询功能','request_id':str(uuid4())}
        first = self.client.post('/feedback',json=body)
        self.assertEqual(first.status_code,200)
        self.assertEqual(self.client.post('/feedback',json=body).json()['id'],first.json()['id'])
        self.assertEqual(self.client.get('/feedback').json()['total'],1)
        self.assertEqual(self.client.get('/admin/feedback').status_code,403)
        self.assertEqual(self.client.put('/admin/feedback/1',json={'status':'handled'}).status_code,403)
        self.user_id = 3
        self.assertEqual(self.client.get('/feedback').json()['total'],0)
        self.user_id = 1
        self.assertEqual(self.client.get('/admin/feedback').json()['total'],1)
        self.assertEqual(self.client.put('/admin/feedback/1',json={'status':'handled','reply':'已收到建议，将改进查询功能'}).status_code,200)
        self.user_id = 2
        self.assertEqual(self.client.get('/feedback').json()['items'][0]['status'],'handled')
        self.assertEqual(self.client.get('/feedback').json()['items'][0]['reply'],'已收到建议，将改进查询功能')
        self.assertTrue(self.client.get('/feedback').json()['items'][0]['replied_at'])
    def test_invalid_content_rejected(self):
        body={'category':'功能建议','content':'     ','request_id':str(uuid4())}
        self.assertEqual(self.client.post('/feedback',json=body).status_code,400)
        body['content']='x'*2001
        self.assertEqual(self.client.post('/feedback',json=body).status_code,422)
        self.assertEqual(self.client.get('/feedback').json()['total'],0)

if __name__ == '__main__': unittest.main()
