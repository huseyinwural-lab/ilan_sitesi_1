
from locust import HttpUser, task, between
import random

class MultiCountryUser(HttpUser):
    wait_time = between(1, 3)
    
    # Traffic Distribution: 50% TR, 30% DE, 20% IT
    countries = ["tr"] * 5 + ["de"] * 3 + ["it"] * 2
    
    # @task(3)
    # def view_homepage(self):
    #     country = random.choice(self.countries)
    #     self.client.get(f"/{country}", name="/{country}")

    @task(5)
    def search_listings(self):
        country = random.choice(self.countries)
        self.client.get(f"/api/landing/{country}/cars", name="/api/landing/{country}/cars")

    @task(1)
    def view_listing_detail(self):
        # We need a valid listing ID. In real test, fetch from search first.
        # Here we just hit search to simulate load.
        pass
