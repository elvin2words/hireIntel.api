import os

from src.Modules.Candidate.Documents.DocumentModels import Document
# from src.Modules.Integration.FileWatcherService import Document
from src.config.DBModelsConfig import db

class DocumentRepository:
    def __init__(self):
        self.__db = db

    def save_document(self, document):
        self.__db.session.add(document)
        self.__db.session.commit()
        return document

    def get_candidate_documents(self, candidate_id):
        return self.__db.session.query(Document).filter_by(candidate_id=candidate_id).all()

    def get_document_by_id(self, document_id):
        return self.__db.session.query(Document).filter_by(id=document_id).first()

    def get_latest_candidate_resume(self, candidate_id):
        """Get the most recent resume document for a candidate"""
        return (Document.query
                .filter_by(candidate_id=candidate_id, document_type='resume')
                .order_by(Document.created_at.desc())
                .first())

    def update_document(self, document):
        """Update document in database"""
        try:
            self.__db.session.add(document)
            self.__db.session.commit()
            return document
        except Exception as e:
            self.__db.session.rollback()
            raise Exception(f"Error updating document: {str(e)}")

