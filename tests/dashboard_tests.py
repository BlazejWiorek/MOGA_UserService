from flask_testing import LiveServerTestCase
from selenium import webdriver
from user_app import create_app, db


import requests


class MyTest(LiveServerTestCase):

    def create_app(self):
        app = create_app('test')
        return app

    def setUp(self):
        db.drop_all()
        db.create_all()

        self.driver = webdriver.Firefox()
        self.driver.get(self.get_server_url())

    def test_server_is_up_and_running(self):
        response = requests.get(self.get_server_url())
        self.assertEqual(response.status_code, 200)