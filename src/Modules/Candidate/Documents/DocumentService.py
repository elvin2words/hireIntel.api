import os
import shutil
import uuid
from datetime import datetime

from werkzeug.utils import secure_filename

from src.Helpers.ErrorHandling import CustomError
from src.Modules.Candidate.Documents.DocumentModels import Document
from src.Modules.Candidate.Documents.DocumentRepository import DocumentRepository


class DocumentService:
    def __init__(self, path):
        self.__document_repository = DocumentRepository()
        self.UPLOAD_FOLDER = path
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

    def get_candidate_resume(self, candidate_id):
        """Get the most recent resume document for a candidate"""
        try:
            resume = self.__document_repository.get_latest_candidate_resume(candidate_id)
            if not resume:
                raise CustomError("No resume found for candidate", 404)
            return resume
        except Exception as e:
            raise CustomError(f"Error fetching resume: {str(e)}", 400)

    def update_document_status(self, document_id, new_status):
        """Update document processing status"""
        try:
            document = self.__document_repository.get_document_by_id(document_id)
            if not document:
                raise CustomError("Document not found", 404)

            document.status = new_status
            document.updated_at = datetime.utcnow()

            return self.__document_repository.update_document(document)
        except Exception as e:
            raise CustomError(f"Error updating document status: {str(e)}", 400)