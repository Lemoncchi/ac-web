import os
import shutil
import unittest

os.environ['DATABASE_URI'] = 'sqlite:///:memory:'
os.environ["UPLOAD_FOLDER"] = os.path.join(
    os.path.dirname(__file__), "acweb", "uploads", "test_uploads"
)

from acweb import app, db
from acweb.commands import forge, initdb
from acweb.models import CloudFile, User

class TestUser():
    """用于测试的 User 类"""

    def __init__(self,username: str, password:str):
        self.username = username
        self.password = password

    def login(self, client):
        response = client.post('/login', data=dict(
            username=self.username,
            password=self.password,
        ), follow_redirects=True)
        # print('LOGIN', response.get_data(as_text=True))
        # assert f"{self.username}'s 中传云盘" in response.get_data(as_text=True)
        return response

    def register(self, client, psw_repeat:str | None = None):
        if psw_repeat is None:
            psw_repeat = self.password

        response = client.post('/register', data={
            'username': self.username,
            'psw': self.password,
            'psw-repeat': psw_repeat,
        }, follow_redirects=True)
        # print('REGISTER', response.get_data(as_text=True))
        return response
    
    def logout(self, client):
        response = client.get('/logout', follow_redirects=True)
        # print(response.get_data(as_text=True))
        return response


class AcWebTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(os.environ["UPLOAD_FOLDER"]):
            os.makedirs(os.environ["UPLOAD_FOLDER"])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(os.environ["UPLOAD_FOLDER"])

    def setUp(self):
        import warnings
        warnings.simplefilter('ignore', category=DeprecationWarning)  # 忽略 DeprecationWarning
        with app.test_request_context():
            app.config.update(
                TESTING=True,
                SQLALCHEMY_DATABASE_URI='sqlite:///:memory:'
            )
            db.create_all()

            self.test_user1 = TestUser('test1', 'yWy35dhxb3zf_Et')

            user = User(username=self.test_user1.username)
            user.set_password(self.test_user1.password)
            db.session.add(user)
            db.session.commit()

            cloud_file = CloudFile.save_encrypt_commit(user_id=user.id, file_name_='Test CloudFile Title', content_bytes_=os.urandom(16))
            self.testuser1_cloud_file_id = cloud_file.id
            self.client = app.test_client()
            self.runner = app.test_cli_runner()

    def tearDown(self):
        with app.test_request_context():
            CloudFile.delete_uncommit(self.testuser1_cloud_file_id)
            db.session.remove()
            db.drop_all()

    def share_file(self, cloud_file_id: int, expired_in:str = '10', customed_expired_in:str = '', allowed_download_times:str = '2', customed_allowed_download_times:str = ''):
        response = self.client.post(
            f"/share/{cloud_file_id}",
            data=dict(expired_in='10', customed_expired_in='',allowed_download_times='2', customed_allowed_download_times=''),
            follow_redirects=True,
        )
        # print(response.get_data(as_text=True))


    def test_app_exist(self):
        self.assertIsNotNone(app)

    def test_app_is_testing(self):
        self.assertTrue(app.config['TESTING'])

    def test_404_page(self):
        response = self.client.get('/nothing')
        data = response.get_data(as_text=True)
        self.assertIn('Page Not Found - 404', data)
        self.assertIn('Go Back', data)
        self.assertEqual(response.status_code, 404)

    def test_index_page(self):
        response = self.client.get('/')
        data = response.get_data(as_text=True)
        self.assertIn('中传放心传', data)
        self.assertNotIn('Test CloudFile Title', data)
        self.assertNotIn('myDropzone', data)
        self.assertEqual(response.status_code, 200)

        self.test_user1.login(self.client)
        response = self.client.get('/')
        data = response.get_data(as_text=True)
        self.assertIn('Test CloudFile Title', data)
        self.assertIn('myDropzone', data)
        self.assertEqual(response.status_code, 200)

    def test_login_protect(self):
        response = self.client.get('/')
        data = response.get_data(as_text=True)
        self.assertNotIn('Logout', data)
        self.assertNotIn('Settings', data)
        self.assertNotIn('fa-trash', data)
        self.assertNotIn('fa-edit', data)
        self.assertNotIn('fa-download', data)
        self.assertNotIn('fa-share', data)

    def test_login(self):
        response = self.test_user1.login(self.client)
        data = response.get_data(as_text=True)
        self.assertIn(f"{self.test_user1.username}'s 中传云盘", data)
        self.assertIn('Login success.', data)
        self.assertIn('Logout', data)
        self.assertIn('fa-trash', data)
        self.assertIn('fa-edit', data)
        self.assertIn('fa-download', data)
        self.assertIn('fa-share', data)
    #     self.assertIn('<form method="post">', data)

    #     response = self.client.post('/login', data=dict(
    #         username='test',
    #         password='456'
    #     ), follow_redirects=True)
    #     data = response.get_data(as_text=True)
    #     self.assertNotIn('Login success.', data)
    #     self.assertIn('Invalid username or password.', data)

    #     response = self.client.post('/login', data=dict(
    #         username='wrong',
    #         password='123'
    #     ), follow_redirects=True)
    #     data = response.get_data(as_text=True)
    #     self.assertNotIn('Login success.', data)
    #     self.assertIn('Invalid username or password.', data)

    #     response = self.client.post('/login', data=dict(
    #         username='',
    #         password='123'
    #     ), follow_redirects=True)
    #     data = response.get_data(as_text=True)
    #     self.assertNotIn('Login success.', data)
    #     self.assertIn('Invalid input.', data)

    #     response = self.client.post('/login', data=dict(
    #         username='test',
    #         password=''
    #     ), follow_redirects=True)
    #     data = response.get_data(as_text=True)
    #     self.assertNotIn('Login success.', data)
    #     self.assertIn('Invalid input.', data)

    def test_logout(self):
        self.test_user1.login(self.client)

        response = self.client.get('/logout', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Goodbye.', data)
        self.assertNotIn('Logout', data)
        self.assertNotIn('Settings', data)
        self.assertNotIn('fa-trash', data)
        self.assertNotIn('fa-edit', data)
        self.assertNotIn('fa-download', data)
        self.assertNotIn('fa-share', data)

    def test_settings(self):
        self.test_user1.login(self.client)

        response = self.client.get('/settings')
        data = response.get_data(as_text=True)
        self.assertIn('Settings', data)
        self.assertIn('Your Name', data)

        response = self.client.post('/settings', data=dict(
            username='',
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Settings updated.', data)
        self.assertIn('Invalid input.', data)

        response = self.client.post('/settings', data=dict(
            username='Grey Li',
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Settings updated.', data)
        self.assertIn('Grey Li', data)

    # def test_create_item(self):
    #     self.test_user1.login(self.client)

    #     response = self.client.post('/', data=dict(
    #         file_name='New CloudFile',
    #         year='2019'
    #     ), follow_redirects=True)
    #     data = response.get_data(as_text=True)
    #     self.assertIn('Item created.', data)
    #     self.assertIn('New CloudFile', data)

    #     response = self.client.post('/', data=dict(
    #         file_name='',
    #         year='2019'
    #     ), follow_redirects=True)
    #     data = response.get_data(as_text=True)
    #     self.assertNotIn('Item created.', data)
    #     self.assertIn('Invalid input.', data)

    #     response = self.client.post('/', data=dict(
    #         file_name='New CloudFile',
    #         year=''
    #     ), follow_redirects=True)
    #     data = response.get_data(as_text=True)
    #     self.assertNotIn('Item created.', data)
    #     self.assertIn('Invalid input.', data)

    # def test_update_item(self):
    #     self.test_user1.login(self.client)

    #     response = self.client.get('/cloud_file/edit/1')
    #     data = response.get_data(as_text=True)
    #     self.assertIn('Edit item', data)
    #     self.assertIn('Test CloudFile Title', data)
    #     self.assertIn('2019', data)

    #     response = self.client.post('/cloud_file/edit/1', data=dict(
    #         file_name='New CloudFile Edited',
    #         year='2019'
    #     ), follow_redirects=True)
    #     data = response.get_data(as_text=True)
    #     self.assertIn('Item updated.', data)
    #     self.assertIn('New CloudFile Edited', data)

    #     response = self.client.post('/cloud_file/edit/1', data=dict(
    #         file_name='',
    #         year='2019'
    #     ), follow_redirects=True)
    #     data = response.get_data(as_text=True)
    #     self.assertNotIn('Item updated.', data)
    #     self.assertIn('Invalid input.', data)

    #     response = self.client.post('/cloud_file/edit/1', data=dict(
    #         file_name='New CloudFile Edited Again',
    #         year=''
    #     ), follow_redirects=True)
    #     data = response.get_data(as_text=True)
    #     self.assertNotIn('Item updated.', data)
    #     self.assertNotIn('New CloudFile Edited Again', data)
    #     self.assertIn('Invalid input.', data)

    def test_login_delete_item(self):
        with app.test_request_context():
            self.test_user1.login(self.client)
            response = self.client.post('/cloud_file/delete/1', follow_redirects=True)
            data = response.get_data(as_text=True)
            self.assertIn('Item deleted.', data)
            self.assertNotIn('Test CloudFile Title', data)
            self.assertEqual(CloudFile.query.count(), 0)


    def test_logout_delete_item(self):
        with app.test_request_context():
            response = self.client.post('/cloud_file/delete/1', follow_redirects=True)
            data = response.get_data(as_text=True)
            self.assertNotIn('Item deleted.', data)
            self.assertNotIn('Test CloudFile Title', data)
            self.assertIn('Please log in to access this page.', data)
            self.assertEqual(CloudFile.query.count(), 1)


    def test_forge_command(self):
        with app.test_request_context():
            result = self.runner.invoke(forge)
            self.assertIn('Done.', result.output)
            self.assertNotEqual(db.session.query(CloudFile).count(), 0)

    def test_initdb_command(self):
        result = self.runner.invoke(initdb)
        self.assertIn('Initialized database.', result.output)

    def test_create_user_command(self):
        with app.test_request_context():
            db.drop_all()
            db.create_all()
            result = self.runner.invoke(args=['create-user', '--username', 'grey', '--password', '123'])
            self.assertIn('Creating user...', result.output)
            self.assertIn('Done.', result.output)
            self.assertEqual(User.query.count(), 1)
            self.assertEqual(User.query.first().username, 'grey')
            self.assertTrue(User.query.first().validate_password('123'))

    def test_create_user_command_update(self):
        with app.test_request_context():
            result = self.runner.invoke(args=['create-user', '--username', 'peter', '--password', '456'])
            self.assertIn('Updating user...', result.output)
            self.assertIn('Done.', result.output)
            self.assertEqual(User.query.count(), 1)
            self.assertEqual(User.query.first().username, 'peter')
            self.assertTrue(User.query.first().validate_password('456'))

    def test_None_share_page_access_token(self):
        with app.test_request_context():
            self.test_user1.login(self.client)
            self.share_file(self.testuser1_cloud_file_id)
            response = self.client.get('/share/download_page')
            data = response.get_data(as_text=True)
            self.assertIn('None share page access token.', data)
    
    def test_delete_others_file(self):
        """尝试在另外一个用户的账户登录下删除他人文件"""
        with app.test_request_context():
            tmp_test_user2 = TestUser('test2', 'e28keQq2:b.EtxP')
            tmp_test_user2.register(self.client)
            rsp = tmp_test_user2.login(self.client)
            self.assertIn(f"{tmp_test_user2.username}'s 中传云盘", rsp.get_data(as_text=True))

            response = self.client.get(f'/cloud_file/delete/{self.testuser1_cloud_file_id}', follow_redirects=True)
            data = response.get_data(as_text=True)
            # print(data)
            self.assertIn("Forbidden.\nYou don&#39;t have the permission to delete this item.", data)


    def test_other_account_download_others_file(self):
        """尝试使用他人账户通过非共享 URL（相当于个人下载 URL /cloud_file/downloads/content）下载他人文件"""
        with app.test_request_context():
            tmp_test_user2 = TestUser('test2', 'e28keQq2:b.EtxP')
            tmp_test_user2.register(self.client)
            rsp = tmp_test_user2.login(self.client)
            self.assertIn(f"{tmp_test_user2.username}'s 中传云盘", rsp.get_data(as_text=True))

            response = self.client.get(f'/cloud_file/downloads/content/{self.testuser1_cloud_file_id}', follow_redirects=True)
            data = response.get_data(as_text=True)
            # print(data)
            self.assertIn("Forbidden.", data)
            self.assertEqual(response.status_code, 403)

    def test_unlogin_download_others_file(self):
        """尝试使用他人的个人下载 URL (/cloud_file/downloads/content) 下载文件"""
        with app.test_request_context():
            response = self.client.get(
                f"/cloud_file/downloads/content/{self.testuser1_cloud_file_id}",
                follow_redirects=True,
            )
            data = response.get_data(as_text=True)
            # print(data)
            self.assertIn(
                "Please login then download the file.",
                data,
            )
            self.assertIn('<input type="text" placeholder="Enter Username" name="username" required>', data)


if __name__ == '__main__':
    unittest.main()
