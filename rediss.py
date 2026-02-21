import redis
import time

r = redis.Redis(decode_responses=True)

def get_data():
    if r.get("data"):
        print("From cache")
        return r.get("data")

    print("From DB")
    time.sleep(3)  # simulate DB call
    r.setex("data", 10, "Hello Redis")  # expire in 10 sec
    return "Hello Redis"

print(get_data())
print(get_data())
