import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate("storage-gemini-quiz-firebase.json")
firebase_admin.initialize_app(cred)

db = firestore.client()


def store_to_firebase():
    print("Test")


# Function to store JSON data to Firebase Realtime Database
def store_json_to_firebase(data, ref_path):
    ref = db.reference(ref_path)
    ref.set(data)
    print(f"Data stored at {ref_path}")


# Function to retrieve JSON data from Firebase Realtime Database
def retrieve_json_from_firebase(ref_path):
    ref = db.reference(ref_path)
    data = ref.get()
    print(f"Data retrieved from {ref_path}")
    return data
