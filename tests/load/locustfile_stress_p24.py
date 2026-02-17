from locust import HttpUser, task, between
import random

class StressTestUser(HttpUser):
    wait_time = between(0.5, 2.0) # Fast clicking
    
    # Auth token placeholder - In a real stress test, we'd need a CSV of tokens.
    # For this env, we'll assume the system can handle unauthenticated or we simulate one user.
    token = None 

    def on_start(self):
        # Login once to get token
        response = self.client.post("/api/v2/mobile/auth/login", json={
            "email": "admin@platform.com", 
            "password": "Admin123!",
            "device_name": "LoadTest", 
            "device_id": f"load_{random.randint(1000,9999)}"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]

    @task(5)
    def view_feed(self):
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        self.client.get("/api/v2/mobile/listings/feed?country=TR", headers=headers, name="/feed")

    @task(3)
    def view_recommendations(self):
        # This hits the ML/Hybrid engine
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        self.client.get("/api/v2/mobile/recommendations/", headers=headers, name="/recommendations")

    @task(1)
    def view_listing_detail(self):
        # Mock ID - In real test, extract from feed
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        # We need a valid UUID. Using a dummy one might 404, but tests the DB path.
        # Ideally, fetch from feed first.
        # self.client.get("/api/v2/mobile/listings/uuid", ...) 
        pass
