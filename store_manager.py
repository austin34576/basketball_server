import firebase_admin
from firebase_admin import credentials, storage, firestore


class Database:
    def __init__(self):
	
        self.bucket_name = "austin-project-56827.appspot.com"
        self.fb_cred = 'serviceaccount.json'
        cred = credentials.Certificate(self.fb_cred)
        firebase_admin.initialize_app(cred,
                                      {'storageBucket': self.bucket_name})
        self.db = firestore.client()  # this connects to our Firestore database
    
    def sanity_check():
         print('test')
    
    def update_firestore(self, collection:str, userid:str, data:dict):
        collection = self.db_collection(collection)
        doc = collection.document(userid)
        doc.set(data, merge=True)

    def exists_on_cloud(self, filename):
        # as stated before you can think of blob as a miscellaneous collection of data or bytes
        bucket = storage.bucket()
        blob = bucket.blob(filename)
        if blob.exists():
            return blob.public_url
        else:
            return False

    def upload_file(self, firebase_path, local_path):
        url = self.exists_on_cloud(firebase_path)
        if not url:
            bucket = storage.bucket()
            blob = bucket.blob(firebase_path)
            blob.upload_from_filename(local_path)
            blob.make_public()
            url = blob.public_url
        return url