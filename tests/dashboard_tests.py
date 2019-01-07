from flask_testing import LiveServerTestCase
from selenium import webdriver
from time import sleep
from user_app import create_app
from user_app.core.views import *
from user_app.models import Population


class SeleniumTests(LiveServerTestCase):

    def create_app(self):
        app = create_app('test')
        return app

    def setUp(self):
        db.drop_all()
        db.create_all()

        self.driver = webdriver.Firefox()

    def get_form_elements(self):
        population_form = self.driver.find_element_by_class_name('form')
        return population_form.find_elements_by_tag_name('input')[1:-1], population_form.find_element_by_id('submit')

    def test_add_twice_same_population(self):
        self.driver.get(self.get_server_url())

        def _add_population(elements, values):
            for form_element, value in zip(elements, values):
                form_element.send_keys(str(value))
                sleep(0.5)

        def _check_if_string_in_html(string):
            self.assertIn(string, self.driver.page_source)

        form_values = ['PopulacjaTestowa', 100, 0.8, 0.4, 1000]
        form_elements, form_submit = self.get_form_elements()

        _add_population(form_elements, form_values)

        form_submit.click()
        sleep(1)

        _check_if_string_in_html('Population added')

        population_from_db = Population.query.filter_by(name='PopulacjaTestowa').first()
        self.assertIsNotNone(population_from_db)

        form_elements_after_update, form_submit_after_update = self.get_form_elements()
        for element in form_elements_after_update:
            self.assertEqual(element.get_attribute("value"), '')

        _add_population(form_elements_after_update, form_values)
        form_submit_after_update.click()
        _check_if_string_in_html('Population name must be unique')

        sleep(1)

        self.driver.get(self.get_server_url())
        amount_of_populations = len(self.driver.find_elements_by_tag_name('h3'))
        self.assertEqual(amount_of_populations, 1)

        sleep(1)

    def tearDown(self):
        self.driver.close()