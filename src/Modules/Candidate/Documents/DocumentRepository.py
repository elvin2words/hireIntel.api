import os

from src.Modules.Integration.FileWatcherService import Document
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