from typing import TypeVar, Generic, Type, List, Optional
from src.config.DBModelsConfig import db
from sqlalchemy.exc import SQLAlchemyError

T = TypeVar('T')

class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T]):
        self._model = model
        self._db = db

    def get_by_id(self, id: str) -> Optional[T]:
        """
        Retrieve an entity by its ID
        """
        try:
            return self._db.session.query(self._model).filter_by(id=id).first()
        except SQLAlchemyError as e:
            self._db.session.rollback()
            raise e

    def get_all(self) -> List[T]:
        """
        Retrieve all entities of this type
        """
        try:
            return self._db.session.query(self._model).all()
        except SQLAlchemyError as e:
            self._db.session.rollback()
            raise e

    def create(self, entity: T) -> T:
        """
        Create a new entity
        """
        try:
            self._db.session.add(entity)
            self._db.session.commit()
            return entity
        except SQLAlchemyError as e:
            self._db.session.rollback()
            raise e

    def update(self, entity: T) -> T:
        """
        Update an existing entity
        """
        try:
            self._db.session.commit()
            return entity
        except SQLAlchemyError as e:
            self._db.session.rollback()
            raise e

    def delete(self, entity: T) -> None:
        """
        Delete an entity
        """
        try:
            self._db.session.delete(entity)
            self._db.session.commit()
        except SQLAlchemyError as e:
            self._db.session.rollback()
            raise e

    def bulk_create(self, entities: List[T]) -> List[T]:
        """
        Create multiple entities at once
        """
        try:
            self._db.session.bulk_save_objects(entities)
            self._db.session.commit()
            return entities
        except SQLAlchemyError as e:
            self._db.session.rollback()
            raise e