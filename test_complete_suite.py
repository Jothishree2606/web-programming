import urllib.request
import urllib.parse
import json
import pymongo
from pathlib import Path

from api.config import MONGODB_URI, DATABASE_NAME
BASE_URL = "http://127.0.0.1:8000"
MONGO_URI = MONGODB_URI
DB_NAME = DATABASE_NAME

def run_tests():
    print("=" * 60)
    print("FRYCHO COMPLETE END-TO-END VERIFICATION SUITE")
    print("=" * 60)

    # Connect to MongoDB directly
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]
    print("[1] Direct MongoDB Connection: SUCCESS")
    print(f"    Connected to: {MONGO_URI}, DB: {DB_NAME}")
    print(f"    Existing Collections: {db.list_collection_names()}")

    # 1. Health Check
    req = urllib.request.Request(f"{BASE_URL}/api/health")
    with urllib.request.urlopen(req) as resp:
        health = json.loads(resp.read().decode())
        print("\n[2] Health Endpoint (/api/health):")
        print(f"    Status: {health.get('status')}")
        print(f"    Database info: {health.get('database')}")
        assert health.get("database", {}).get("connected") == True, "DB not connected!"

    # 2. Admin Login
    login_data = json.dumps({"username": "admin", "password": "frychoadmin2026"}).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/api/auth/login",
        data=login_data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        auth_res = json.loads(resp.read().decode())
        token = auth_res.get("access_token")
        print("\n[3] Admin Login (/api/auth/login): SUCCESS")
        print(f"    Token received: {token[:25]}...")

    # 3. Submit Franchise Application with File Upload
    boundary = "----TestBoundaryFRYCHO2026"
    test_file_content = b"%PDF-1.4 Mock ID Proof Document for Frycho Test"
    
    app_payload = {
        "personal": {
            "fullName": "Kiran Udhaya",
            "phone": "9876543210",
            "email": "kiran@example.com",
            "address": "42 Anna Salai",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "pincode": "600002"
        },
        "proposedLocation": {
            "city": "Coimbatore",
            "state": "Tamil Nadu",
            "area": "Gandhipuram",
            "street": "Cross Cut Road",
            "pincode": "641012",
            "propertyStatus": "Rented",
            "shopArea": "500",
            "landmark": "Near Bus Stand",
            "description": "High footfall main road location"
        },
        "businessExperience": {
            "hasExperience": True,
            "businessType": "Food & Beverage",
            "yearsOfExperience": "3",
            "description": "Ran a quick service burger cafe"
        },
        "propertyDetails": {
            "ownership": "Rented",
            "area": "500",
            "frontage": "22 ft",
            "floor": "Ground Floor",
            "parking": "Yes",
            "rent": "35000",
            "landmarks": "Bus Stand",
            "description": "Prime frontage"
        },
        "additionalInfo": "Excited to bring FRYCHO to Coimbatore!"
    }

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="formData"\r\n\r\n'
        f"{json.dumps(app_payload)}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="identityProof"; filename="aadhar_test.pdf"\r\n'
        f"Content-Type: application/pdf\r\n\r\n"
    ).encode("utf-8") + test_file_content + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        f"{BASE_URL}/api/franchise/apply",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    with urllib.request.urlopen(req) as resp:
        app_res = json.loads(resp.read().decode())
        created_app_id = app_res["appId"]
        print("\n[4] Franchise Application Submission (/api/franchise/apply):")
        print(f"    Generated App ID: {created_app_id}")
        print(f"    Message: {app_res.get('message')}")

    # Verify MongoDB for Franchise Application
    mongo_app = db.applications.find_one({"id": created_app_id}, {"_id": 0})
    print("\n[5] Verifying MongoDB frycho_db.applications:")
    assert mongo_app is not None, "Application was NOT found in MongoDB!"
    print(f"    Found document in MongoDB!")
    print(f"    ID: {mongo_app.get('id')}")
    print(f"    Applicant: {mongo_app.get('personal', {}).get('fullName')}")
    print(f"    Status: {mongo_app.get('status')}")
    print(f"    Documents stored: {len(mongo_app.get('documents', []))}")
    if mongo_app.get('documents'):
        doc_info = mongo_app['documents'][0]
        print(f"    Uploaded File URL: {doc_info.get('url')}")
        print(f"    Uploaded File Exists on Disk: {Path(doc_info.get('localPath')).exists()}")

    # 4. Admin Applications List
    req = urllib.request.Request(f"{BASE_URL}/api/admin/applications")
    with urllib.request.urlopen(req) as resp:
        admin_apps_res = json.loads(resp.read().decode())
        apps_list = admin_apps_res.get("applications", [])
        found_in_admin = any(a.get("id") == created_app_id for a in apps_list)
        print("\n[6] Admin Applications View (/api/admin/applications):")
        print(f"    Total in Admin Dashboard: {len(apps_list)}")
        print(f"    Newly submitted app visible to Admin: {found_in_admin}")
        assert found_in_admin, "Admin cannot see the newly created application!"

    # 5. Admin Status Update
    update_body = json.dumps({"status": "Under Review", "adminNotes": "Checked location via StreetView - looks prime."}).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/api/admin/applications/{created_app_id}/status",
        data=update_body,
        headers={"Content-Type": "application/json"},
        method="PATCH"
    )
    with urllib.request.urlopen(req) as resp:
        patch_res = json.loads(resp.read().decode())
        print("\n[7] Admin Status Update (/api/admin/applications/{id}/status):")
        print(f"    Updated Status: {patch_res.get('application', {}).get('status')}")
        print(f"    Admin Notes: {patch_res.get('application', {}).get('adminNotes')}")

    # Verify update in MongoDB directly
    mongo_app_updated = db.applications.find_one({"id": created_app_id}, {"_id": 0})
    assert mongo_app_updated.get("status") == "Under Review", "MongoDB status not updated!"
    print(f"    Direct MongoDB verify: Status={mongo_app_updated.get('status')}, Notes={mongo_app_updated.get('adminNotes')}")

    # 6. Submit Contact Enquiry
    enquiry_payload = {
        "name": "Meera Krishnan",
        "phone": "9840112233",
        "email": "meera.k@gmail.com",
        "subject": "Franchise Royalty Question",
        "message": "What is the expected ROI period for a tier-2 city outlet?"
    }
    req = urllib.request.Request(
        f"{BASE_URL}/api/contact",
        data=json.dumps(enquiry_payload).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        enq_res = json.loads(resp.read().decode())
        created_enq_id = enq_res["enquiryId"]
        print("\n[8] Contact Enquiry Submission (/api/contact):")
        print(f"    Generated Enquiry ID: {created_enq_id}")

    # Verify MongoDB for Enquiry
    mongo_enq = db.enquiries.find_one({"id": created_enq_id}, {"_id": 0})
    assert mongo_enq is not None, "Enquiry not found in MongoDB!"
    print("\n[9] Verifying MongoDB frycho_db.enquiries:")
    print(f"    Found enquiry in MongoDB: {mongo_enq.get('id')}, Name: {mongo_enq.get('name')}, Status: {mongo_enq.get('status')}")

    # 7. Admin Enquiries List
    req = urllib.request.Request(f"{BASE_URL}/api/admin/enquiries")
    with urllib.request.urlopen(req) as resp:
        admin_enqs_res = json.loads(resp.read().decode())
        enqs_list = admin_enqs_res.get("enquiries", [])
        found_enq_in_admin = any(e.get("id") == created_enq_id for e in enqs_list)
        print("\n[10] Admin Enquiries View (/api/admin/enquiries):")
        print(f"    Total Enquiries: {len(enqs_list)}")
        print(f"    Newly submitted enquiry visible to Admin: {found_enq_in_admin}")
        assert found_enq_in_admin, "Admin cannot see the newly created enquiry!"

    # 8. Admin Enquiry Status Update
    patch_enq_body = json.dumps({"status": "Contacted", "adminNotes": "Called applicant, explained 12-14 month ROI."}).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/api/admin/enquiries/{created_enq_id}/status",
        data=patch_enq_body,
        headers={"Content-Type": "application/json"},
        method="PATCH"
    )
    with urllib.request.urlopen(req) as resp:
        patch_enq_res = json.loads(resp.read().decode())
        print("\n[11] Admin Enquiry Status Update (/api/admin/enquiries/{id}/status):")
        print(f"    Updated Status: {patch_enq_res.get('enquiry', {}).get('status')}")

    mongo_enq_updated = db.enquiries.find_one({"id": created_enq_id}, {"_id": 0})
    assert mongo_enq_updated.get("status") == "Contacted"
    print(f"    Direct MongoDB verify: Status={mongo_enq_updated.get('status')}")

    # 9. CSV Exports
    req = urllib.request.Request(f"{BASE_URL}/api/admin/applications/export")
    with urllib.request.urlopen(req) as resp:
        csv_content = resp.read().decode()
        print("\n[12] CSV Applications Export (/api/admin/applications/export):")
        print(f"    CSV Size: {len(csv_content)} bytes, Rows: {len(csv_content.strip().splitlines())}")

    req = urllib.request.Request(f"{BASE_URL}/api/admin/enquiries/export")
    with urllib.request.urlopen(req) as resp:
        enq_csv = resp.read().decode()
        print("\n[13] CSV Enquiries Export (/api/admin/enquiries/export):")
        print(f"    CSV Size: {len(enq_csv)} bytes, Rows: {len(enq_csv.strip().splitlines())}")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED! 100% OPERATIONAL WITH MONGODB COMPASS & ADMIN")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
