from typing import TypeVar, Generic, Type, List, Optional
from src.config.DBModelsConfig import db
from sqlalchemy.exc import SQLAlchemyError 

import logging # Error logging 

T = TypeVar('T') # Generic type variable 

"""
Generic repository which handles the base CRUD operations for any DB model. 
Abstracts the repetitive db interaction logic (quering, creating, updating, deleting).
Also provides a unified interface to work with the db.

"""

# Set up logging configuration for each method of the Base Repository
logging.basicConfig(level=logging.INFO, format='%(asctime)s-%(levelname)s-%(message)s') # 
logger = logging.getLogger(__name__) #Create a logger instance


class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T]):
        # Sets up repo to interact with speciic db model and session
        self._model = model
        self._db = db 

    def get_by_id(self, id: str) -> Optional[T]:
        """
        Retrieve an entity from db by its ID otherwise None
        """
        try:
            return self._db.session.query(self._model).filter_by(id=id).first() # query db
        except SQLAlchemyError as e:
            # log error with details
            logger.error(f"Error retrieving entity by ID in {self.__class__.__name__}. Error: {str(e)}") 
            self._db.session.rollback() 
            raise e

    def get_all(self) -> List[T]:
        """
        Retrieve all entities of a particular model type from db as a list
        """
        try:
            return self._db.session.query(self._model).all() #list of all records
        except SQLAlchemyError as e:
            # log error with details
            logger.error(f"Error retrieving all entities in {self.__class__.__name__}. Error: {str(e)}") 
            self._db.session.rollback()
            raise e

    def create(self, entity: T) -> T:
        """
        Create a new entity and add it to the session and commits the transaction to persist the entity in the db
        """
        try:
            self._db.session.add(entity)
            self._db.session.commit()
            return entity # created entity
        except SQLAlchemyError as e:
            # log error with details
            logger.error(f"Error creating entity in {self.__class__.__name__}. Error: {str(e)}") 
            self._db.session.rollback()
            raise e

    def update(self, entity: T) -> T:
        """
        Update an existing entity in the db - already loaded and tracked by SQLAlchemy
        """
        try:
            self._db.session.commit()
            return entity
        except SQLAlchemyError as e:
            # log error with details
            logger.error(f"Error updating entity in {self.__class__.__name__}. Error: {str(e)}") 
            self._db.session.rollback()
            raise e

    def delete(self, entity: T) -> None:
        """
        Delete an entity from db
        """
        try:
            self._db.session.delete(entity)
            self._db.session.commit()
        except SQLAlchemyError as e:
            # log error with details
            logger.error(f"Error deleting entity in {self.__class__.__name__}. Error: {str(e)}") 
            self._db.session.rollback()
            raise e

    # def bulk_create(self, entities: List[T]) -> List[T]:
    def bulk_create(self, entities: List[T], commit:bool=True) -> List[T]:
        # Added an optional commit parameter
        """
        Creates multiple entities at once in bulk - batch operation if commit is true, otherwise not immediately if false
        """
        try:
            self._db.session.bulk_save_objects(entities)
            if commit:
                self._db.session.commit() # commit the specified transactions
            return entities
        except SQLAlchemyError as e:
            # log error with details
            logger.error(f"Error bulk creating entities in {self.__class__.__name__}. Error: {str(e)}") 
            self._db.session.rollback()
            raise e