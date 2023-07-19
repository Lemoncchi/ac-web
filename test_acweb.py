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

            user = User(username='test')
            user.set_password('123')
            db.session.add(user)
            db.session.commit()

            cloud_file = CloudFile.save_encrypt_commit(user_id=user.id, file_name_='Test CloudFile Title', content_bytes_=os.urandom(16))
            self.test_cloud_file_id = cloud_file.id
            self.client = app.test_client()
            self.runner = app.test_cli_runner()

    def tearDown(self):
        with app.test_request_context():
            CloudFile.delete_uncommit(self.test_cloud_file_id)
            db.session.remove()
            db.drop_all()

    def login(self):
        response = self.client.post('/login', data=dict(
            username='test',
            password='123'
        ), follow_redirects=True)
        # print('LOGIN', response.get_data(as_text=True))
    
    def share_file(self, cloud_file_id: int, expired_in:str = '10', customed_expired_in:str = '', allowed_download_times:str = '2', customed_allowed_download_times:str = ''):
        response = self.client.post(
            f"/share/{cloud_file_id}",
            data=dict(expired_in='10', customed_expired_in='',allowed_download_times='2', customed_allowed_download_times=''),
            follow_redirects=True,
        )
        # print(response.get_data(as_text=True))

    def logout(self):
        response = self.client.get('/logout', follow_redirects=True)
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

        self.login()
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
        response = self.client.post('/login', data=dict(
            username='test',
            password='123'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn("test's 中传云盘", data)
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
        self.login()

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
        self.login()

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
    #     self.login()

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
    #     self.login()

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
            self.login()
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

    def test_None_share_code_access_token(self):
        with app.test_request_context():
            self.login()
            self.share_file(self.test_cloud_file_id)
            response = self.client.get(f'/share/download/{self.test_cloud_file_id}')
            data = response.get_data(as_text=True)
            self.assertIn('None share code access token.', data)
        

if __name__ == '__main__':
    unittest.main()
