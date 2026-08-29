import requests
import json

BASE_URL = "http://localhost:5000/api"

print("=" * 60)
print("TESTING PROFILE UPDATE WITH NEW TOKEN")
print("=" * 60)

# 1. Login to get a fresh token
print("\n1. Logging in...")
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
print(f"User ID: {user.get('id')} (Type: {type(user.get('id'))})")
print(f"Token: {token[:60]}...\n")

# 2. Get current user
print("2. Getting current user...")
me_response = requests.get(
    f"{BASE_URL}/auth/me",
    headers={"Authorization": f"Bearer {token}"}
)

if me_response.status_code == 200:
    current_user = me_response.json().get('user')
    print(f"✅ Current user: {current_user.get('first_name')} {current_user.get('last_name')}")
    print(f"   Phone: {current_user.get('phone')}")
    print(f"   Company: {current_user.get('company_name')}")
else:
    print(f"❌ Failed to get user: {me_response.status_code}")
    print(f"Response: {me_response.text}")
    exit()

# 3. Update profile
print("\n3. Updating profile...")
update_data = {
    "first_name": "Admin",
    "last_name": "Harykims",
    "phone": "0712345678",
    "company_name": "Harykims Intertech",
    "address": "Nairobi, Kenya"
}

print(f"   Sending: {update_data}")
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
    updated_user = result.get('user')
    print(f"   Updated user:")
    print(f"   - Name: {updated_user.get('first_name')} {updated_user.get('last_name')}")
    print(f"   - Phone: {updated_user.get('phone')}")
    print(f"   - Company: {updated_user.get('company_name')}")
    print(f"   - Address: {updated_user.get('address')}")
else:
    print(f"❌ Profile update failed: {update_response.status_code}")
    print(f"Response: {update_response.text}")

# 4. Verify
print("\n4. Verifying profile update...")
verify_response = requests.get(
    f"{BASE_URL}/auth/me",
    headers={"Authorization": f"Bearer {token}"}
)

if verify_response.status_code == 200:
    user_data = verify_response.json().get('user')
    print(f"✅ Verified user:")
    print(f"   Name: {user_data.get('first_name')} {user_data.get('last_name')}")
    print(f"   Phone: {user_data.get('phone')}")
    print(f"   Company: {user_data.get('company_name')}")
    print(f"   Address: {user_data.get('address')}")
else:
    print(f"❌ Verification failed: {verify_response.status_code}")
    print(f"Response: {verify_response.text}")

print("\n" + "=" * 60)
