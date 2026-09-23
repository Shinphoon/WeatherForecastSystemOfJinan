"""API regression tests with an in-memory fake; never ban real accounts."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
import auth
import admin_users


class FakeDB:
    def __init__(self):
        self.users = {
            1: dict(id=1, role='admin', status=1),
            2: dict(id=2, role='user', status=1),
            3: dict(id=3, role='admin', status=1),
        }
    def connect(self):
        db = self
        class Connection:
            def cursor(self): return Cursor()
            def close(self): pass
            def commit(self): pass
            def rollback(self): pass
        class Cursor:
            def execute(self, sql, *params):
                self.sql = sql
                self.row = db.users.get(params[-1]) if params else None
                if sql.startswith('UPDATE sys_user'):
                    self.row['status'] = params[0]
                if sql.startswith('SELECT id, username'):
                    self.description = [(key,) for key in ['id', 'username', 'nickname', 'phone', 'email', 'role', 'status', 'push_enable', 'last_address', 'last_lat', 'last_lng', 'create_time', 'update_time']]
            def fetchone(self):
                if 'COUNT(*)' in self.sql: return (len(db.users),)
                if 'WHERE username' in self.sql:
                    return SimpleNamespace(**db.users[2], username='user2', password='unused')
                return SimpleNamespace(**self.row) if self.row else None
            def fetchall(self):
                return [tuple(user.get(col[0]) for col in self.description) for user in db.users.values()]
            def close(self): pass
        return Connection()


class AdminUserTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeDB()
        self.patches = [patch.object(module, 'get_connection', self.db.connect) for module in (auth, admin_users)]
        for item in self.patches: item.start()
        app = FastAPI()
        app.include_router(auth.router)
        app.include_router(admin_users.router)
        self.client = TestClient(app)
    def tearDown(self):
        for item in self.patches: item.stop()
    def headers(self, user_id):
        return {'Authorization': 'Bearer ' + auth.create_access_token(user_id, 'test')}
    def change(self, target, status, actor=1):
        return self.client.put(f'/admin/users/{target}/status', json={'status': status}, headers=self.headers(actor))

    def test_only_admin_can_read_user_data(self):
        self.assertEqual(self.client.get('/admin/users').status_code, 401)
        self.assertEqual(self.client.get('/admin/users', headers=self.headers(2)).status_code, 403)
        result = self.client.get('/admin/users', headers=self.headers(1))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()['total'], 3)
        self.assertNotIn('password', result.json()['users'][0])

    def test_ban_blocks_existing_token_and_login_then_unban(self):
        token = self.headers(2)['Authorization']
        self.assertEqual(auth.get_token_user(token), 2)
        self.assertEqual(self.change(2, 0).status_code, 200)
        with self.assertRaises(auth.HTTPException) as error: auth.get_token_user(token)
        self.assertEqual(error.exception.status_code, 403)
        result = self.client.post('/auth/login', json={'username': 'user2', 'password': 'unused'})
        self.assertEqual(result.status_code, 403)
        self.assertEqual(self.change(2, 1).status_code, 200)
        self.assertEqual(auth.get_token_user(token), 2)

    def test_protected_accounts_invalid_target_and_status(self):
        self.assertEqual(self.change(1, 0).status_code, 400)
        self.assertEqual(self.change(3, 0).status_code, 400)
        self.assertEqual(self.change(999, 0).status_code, 404)
        self.assertEqual(self.change(2, 2).status_code, 422)
        self.assertEqual(self.db.users[2]['status'], 1)

    def test_non_admin_and_disabled_admin_cannot_mutate(self):
        self.assertEqual(self.change(2, 0, actor=2).status_code, 403)
        self.db.users[1]['status'] = 0
        self.assertEqual(self.change(2, 0).status_code, 403)
        self.assertEqual(self.db.users[2]['status'], 1)

    def test_invalid_pagination_and_deleted_token_user(self):
        self.assertEqual(self.client.get('/admin/users?page=0', headers=self.headers(1)).status_code, 422)
        with self.assertRaises(auth.HTTPException) as error: auth.get_token_user(self.headers(999)['Authorization'])
        self.assertEqual(error.exception.status_code, 401)


if __name__ == '__main__': unittest.main()
