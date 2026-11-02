import urllib.request
import json
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

base_url = 'http://127.0.0.1:8000'

def test_full_flow():
    # 1. Submit Franchise Application
    payload = {
        'personal': {
            'fullName': 'Sathish Kumar',
            'phone': '9840123499',
            'email': 'sathish.k@gmail.com',
            'address': '77 GST Road',
            'city': 'Tambaram',
            'state': 'Tamil Nadu',
            'pincode': '600045'
        },
        'proposedLocation': {
            'city': 'Chennai',
            'state': 'Tamil Nadu',
            'area': 'Tambaram Sanatorium',
            'street': 'GST Road',
            'pincode': '600045',
            'propertyStatus': 'I have rented/leased the property',
            'shopArea': '550',
            'landmark': 'Near Tambaram Railway Station',
            'description': 'Prime commercial spot with heavy foot traffic'
        },
        'businessExperience': {
            'hasExperience': True,
            'businessType': 'Fast Food',
            'yearsOfExperience': '4',
            'description': 'Managed quick service restaurant'
        },
        'propertyDetails': {
            'ownership': 'Rented',
            'area': '550',
            'frontage': '20 ft',
            'floor': 'Ground Floor',
            'parking': 'Yes',
            'rent': '₹40,000/month',
            'landmarks': 'Tambaram Railway Station',
            'description': 'Ground floor roadside shop'
        },
        'additionalInfo': 'Ready to start within 30 days.'
    }

    boundary = '----WebKitFormBoundaryE2ETest123'
    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="formData"\r\n\r\n'
        f'{json.dumps(payload)}\r\n'
        f'--{boundary}--\r\n'
    ).encode('utf-8')

    req = urllib.request.Request(
        f'{base_url}/api/franchise/apply',
        data=body,
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
    )

    with urllib.request.urlopen(req) as r:
        apply_res = json.loads(r.read().decode())
        print('Franchise Application Created:', apply_res)
        app_id = apply_res.get('appId')

    # 2. Check Admin Applications Endpoint
    with urllib.request.urlopen(f'{base_url}/api/admin/applications') as r:
        admin_apps = json.loads(r.read().decode())
        total = admin_apps.get('stats', {}).get('totalApplications')
        found = any(a.get('id') == app_id for a in admin_apps.get('applications', []))
        print(f'Admin Applications Total: {total}, Found new app {app_id}: {found}')

    # 3. Check MongoDB directly
    async def verify_mongo():
        client = AsyncIOMotorClient('mongodb://127.0.0.1:27017/')
        db = client['frycho_db']
        doc = await db.applications.find_one({'id': app_id}, {'_id': 0})
        print('MongoDB Compass Record in frycho_db.applications:')
        print('  - ID:', doc.get('id'))
        print('  - Applicant:', doc.get('personal', {}).get('fullName'))
        print('  - City:', doc.get('proposedLocation', {}).get('city'))
        print('  - Status:', doc.get('status'))

    asyncio.run(verify_mongo())

if __name__ == '__main__':
    test_full_flow()
