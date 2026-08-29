import requests
import json

BASE_URL = "http://localhost:5000/api"

# 1. Login
print("1. Logging in...")
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": "admin@harykims.com", "password": "admin123"}
)

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.status_code}")
    print(login_response.text)
    exit()

data = login_response.json()
token = data.get('access_token')
user = data.get('user')

print(f"✅ Login successful!")
print(f"User: {user.get('first_name')} {user.get('last_name')}")
print(f"Token: {token[:50]}...\n")

# 2. Update profile
print("2. Updating profile...")
update_data = {
    "first_name": "Admin",
    "last_name": "Harykims",
    "phone": "0712345678",
    "company_name": "Harykims Intertech",
    "address": "Nairobi, Kenya"
}

update_response = requests.put(
    f"{BASE_URL}/auth/profile",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    },
    json=update_data
)

if update_response.status_code == 200:
    print(f"✅ Profile updated successfully!")
    result = update_response.json()
    print(f"Updated user: {result.get('user')}")
else:
    print(f"❌ Profile update failed: {update_response.status_code}")
    print(f"Response: {update_response.text}")

# 3. Verify the update
print("\n3. Verifying profile update...")
verify_response = requests.get(
    f"{BASE_URL}/auth/me",
    headers={"Authorization": f"Bearer {token}"}
)

if verify_response.status_code == 200:
    print(f"✅ Verified user:")
    user_data = verify_response.json().get('user')
    print(f"  Name: {user_data.get('first_name')} {user_data.get('last_name')}")
    print(f"  Phone: {user_data.get('phone')}")
    print(f"  Company: {user_data.get('company_name')}")
    print(f"  Address: {user_data.get('address')}")
else:
    print(f"❌ Verification failed: {verify_response.status_code}")
