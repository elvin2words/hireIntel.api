import os
import shutil
import uuid
from werkzeug.utils import secure_filename

from src.Modules.Candidate.Documents.DocumentModels import Document
from src.Modules.Candidate.Documents.DocumentRepository import DocumentRepository


class DocumentService:
    def __init__(self):
        self.__document_repository = DocumentRepository()
        self.UPLOAD_FOLDER = 'static/documents'
        self.ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS

    def store_document(self, file_path, original_filename, candidate_id, document_type):
        try:
            # Create upload directory if it doesn't exist
            os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)

            # Generate unique filename
            file_extension = original_filename.rsplit('.', 1)[1].lower()
            stored_filename = f"{str(uuid.uuid4())}.{file_extension}"
            new_file_path = os.path.join(self.UPLOAD_FOLDER, stored_filename)

            # Copy file to new location
            shutil.copy2(file_path, new_file_path)

            # Create document record
            document = Document(
                candidate_id=candidate_id,
                original_name=original_filename,
                stored_name=stored_filename,
                file_path=new_file_path,
                document_type=document_type
            )

            return self.__document_repository.save_document(document)
        except Exception as e:
            raise Exception(f"Error storing document: {str(e)}")