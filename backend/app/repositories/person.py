"""Person repositories for database operations."""

from datetime import datetime
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.person import Person, PersonFaceEncoding, PersonImage


class PersonRepository:
    """Repository for person records."""

    def __init__(self, db: AsyncSession):
        """Initialize repository."""
        self.db = db

    async def create(self, person_id: str, **kwargs) -> Person:
        """Create person."""
        person = Person(id=person_id, **kwargs)
        self.db.add(person)
        await self.db.commit()
        await self.db.refresh(person)
        return person

    async def get_by_id(self, person_id: str) -> Optional[Person]:
        """Get person by ID."""
        result = await self.db.execute(select(Person).where(Person.id == person_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[Person]:
        """Get person by email."""
        result = await self.db.execute(select(Person).where(Person.email == email))
        return result.scalar_one_or_none()

    async def get_by_id_number(self, id_number: str) -> Optional[Person]:
        """Get person by ID number."""
        result = await self.db.execute(select(Person).where(Person.id_number == id_number))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Person]:
        """Get all persons."""
        result = await self.db.execute(
            select(Person).offset(skip).limit(limit).order_by(Person.created_at.desc())
        )
        return result.scalars().all()

    async def get_by_status(self, status: str) -> list[Person]:
        """Get persons by status."""
        result = await self.db.execute(
            select(Person).where(Person.status == status).order_by(Person.created_at.desc())
        )
        return result.scalars().all()

    async def get_by_type(self, person_type: str) -> list[Person]:
        """Get persons by type."""
        result = await self.db.execute(
            select(Person).where(Person.person_type == person_type).order_by(Person.created_at.desc())
        )
        return result.scalars().all()

    async def get_by_department(self, department: str) -> list[Person]:
        """Get persons by department."""
        result = await self.db.execute(
            select(Person).where(Person.department == department).order_by(Person.created_at.desc())
        )
        return result.scalars().all()

    async def get_with_face_encodings(self) -> list[Person]:
        """Get persons with at least one face encoding."""
        result = await self.db.execute(
            select(Person).where(Person.face_encoding_count > 0).order_by(Person.created_at.desc())
        )
        return result.scalars().all()

    async def search(self, query: str) -> list[Person]:
        """Search persons by name, email, or ID number."""
        search_term = f"%{query}%"
        result = await self.db.execute(
            select(Person).where(
                (Person.first_name.ilike(search_term))
                | (Person.last_name.ilike(search_term))
                | (Person.email.ilike(search_term))
                | (Person.id_number.ilike(search_term))
            )
        )
        return result.scalars().all()

    async def count_all(self) -> int:
        """Count total persons."""
        result = await self.db.execute(select(func.count(Person.id)))
        return result.scalar() or 0

    async def count_by_status(self, status: str) -> int:
        """Count persons by status."""
        result = await self.db.execute(
            select(func.count(Person.id)).where(Person.status == status)
        )
        return result.scalar() or 0

    async def count_with_face_encodings(self) -> int:
        """Count persons with face encodings."""
        result = await self.db.execute(
            select(func.count(Person.id)).where(Person.face_encoding_count > 0)
        )
        return result.scalar() or 0

    async def update(self, person_id: str, **kwargs) -> Optional[Person]:
        """Update person."""
        person = await self.get_by_id(person_id)
        if not person:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(person, key):
                setattr(person, key, value)

        self.db.add(person)
        await self.db.commit()
        await self.db.refresh(person)
        return person

    async def delete(self, person_id: str) -> bool:
        """Delete person."""
        person = await self.get_by_id(person_id)
        if not person:
            return False

        await self.db.delete(person)
        await self.db.commit()
        return True


class PersonFaceEncodingRepository:
    """Repository for person face encodings."""

    def __init__(self, db: AsyncSession):
        """Initialize repository."""
        self.db = db

    async def create(self, encoding_id: str, **kwargs) -> PersonFaceEncoding:
        """Create face encoding."""
        encoding = PersonFaceEncoding(id=encoding_id, **kwargs)
        self.db.add(encoding)
        await self.db.commit()
        await self.db.refresh(encoding)
        return encoding

    async def get_by_id(self, encoding_id: str) -> Optional[PersonFaceEncoding]:
        """Get encoding by ID."""
        result = await self.db.execute(
            select(PersonFaceEncoding).where(PersonFaceEncoding.id == encoding_id)
        )
        return result.scalar_one_or_none()

    async def get_by_person(self, person_id: str) -> list[PersonFaceEncoding]:
        """Get encodings for a person."""
        result = await self.db.execute(
            select(PersonFaceEncoding)
            .where(PersonFaceEncoding.person_id == person_id)
            .order_by(PersonFaceEncoding.created_at.desc())
        )
        return result.scalars().all()

    async def get_by_person_active(self, person_id: str) -> list[PersonFaceEncoding]:
        """Get active encodings for a person."""
        result = await self.db.execute(
            select(PersonFaceEncoding)
            .where(
                and_(
                    PersonFaceEncoding.person_id == person_id,
                    PersonFaceEncoding.is_active == True,
                )
            )
            .order_by(PersonFaceEncoding.confidence.desc())
        )
        return result.scalars().all()

    async def get_all_active(self) -> list[PersonFaceEncoding]:
        """Get all active encodings."""
        result = await self.db.execute(
            select(PersonFaceEncoding)
            .where(PersonFaceEncoding.is_active == True)
            .order_by(PersonFaceEncoding.confidence.desc())
        )
        return result.scalars().all()

    async def update(self, encoding_id: str, **kwargs) -> Optional[PersonFaceEncoding]:
        """Update encoding."""
        encoding = await self.get_by_id(encoding_id)
        if not encoding:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(encoding, key):
                setattr(encoding, key, value)

        self.db.add(encoding)
        await self.db.commit()
        await self.db.refresh(encoding)
        return encoding

    async def delete(self, encoding_id: str) -> bool:
        """Delete encoding."""
        encoding = await self.get_by_id(encoding_id)
        if not encoding:
            return False

        await self.db.delete(encoding)
        await self.db.commit()
        return True


class PersonImageRepository:
    """Repository for person images."""

    def __init__(self, db: AsyncSession):
        """Initialize repository."""
        self.db = db

    async def create(self, image_id: str, **kwargs) -> PersonImage:
        """Create person image."""
        image = PersonImage(id=image_id, **kwargs)
        self.db.add(image)
        await self.db.commit()
        await self.db.refresh(image)
        return image

    async def get_by_id(self, image_id: str) -> Optional[PersonImage]:
        """Get image by ID."""
        result = await self.db.execute(
            select(PersonImage).where(PersonImage.id == image_id)
        )
        return result.scalar_one_or_none()

    async def get_by_person(self, person_id: str) -> list[PersonImage]:
        """Get images for a person."""
        result = await self.db.execute(
            select(PersonImage)
            .where(PersonImage.person_id == person_id)
            .order_by(PersonImage.is_primary.desc(), PersonImage.created_at.desc())
        )
        return result.scalars().all()

    async def get_primary_image(self, person_id: str) -> Optional[PersonImage]:
        """Get primary image for a person."""
        result = await self.db.execute(
            select(PersonImage).where(
                and_(
                    PersonImage.person_id == person_id,
                    PersonImage.is_primary == True,
                )
            )
        )
        return result.scalar_one_or_none()

    async def update(self, image_id: str, **kwargs) -> Optional[PersonImage]:
        """Update image."""
        image = await self.get_by_id(image_id)
        if not image:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(image, key):
                setattr(image, key, value)

        self.db.add(image)
        await self.db.commit()
        await self.db.refresh(image)
        return image

    async def delete(self, image_id: str) -> bool:
        """Delete image."""
        image = await self.get_by_id(image_id)
        if not image:
            return False

        await self.db.delete(image)
        await self.db.commit()
        return True
