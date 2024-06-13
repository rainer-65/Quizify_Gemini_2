import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import firebase_admin.exceptions

cred = credentials.Certificate("storage-gemini-quiz-firebase.json")
firebase_admin.initialize_app(cred)

db = firestore.client()


# User-defined exceptions
class DuplicateQuestionException(firebase_admin.exceptions.FirebaseError):
    """Raised when there is a duplicate question"""

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return str(self.message)

    # Function to store JSON data in Firebase Realtime Database


def store_data_in_firebase(firebase_coll, question) -> bool:
    try:
        doc_ref = db.collection(firebase_coll).document()
        if is_unique(firebase_coll, question):
            doc_ref.set(question)
            return True
        else:
            raise DuplicateQuestionException("Duplicate questions are NOT stored!")
    except DuplicateQuestionException:
        return False

    except firebase_admin.exceptions.FirebaseError:
        return False


def is_unique(firebase_coll, question) -> bool:
    # Reference to the collection
    collection_ref = db.collection(firebase_coll)
    # Query the collection to find the document with the given question
    query = collection_ref.where('question', '==', question).stream()

    # Check if any documents match the query
    for doc in query:
        print(f"Found matching document: {doc.id} => {doc.to_dict()}")
        return False  # If a document is found, return True
    return True  # If no documents are found, return False


# Function to delete all documents in a collection
def delete_collection(firebase_coll, batch_size):
    # Reference to the "quizCollection"
    try:
        collection_ref = db.collection(firebase_coll)
        docs = collection_ref.limit(batch_size).stream()
        deleted = 0

        for doc in docs:
            print(f'Deleting doc {doc.id} => {doc.to_dict()}')
            doc.reference.delete()
            deleted += 1

        if deleted >= batch_size:
            return delete_collection(batch_size)

        return True

    except firebase_admin.exceptions.FirebaseError:
        return False
