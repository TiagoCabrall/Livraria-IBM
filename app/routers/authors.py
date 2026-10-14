from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, require_admin
from app.models.author import Author
from app.schemas.author import AuthorCreate, AuthorOut, AuthorUpdate

router = APIRouter(prefix="/authors", tags=["authors"])


async def _get_or_404(db: AsyncSession, author_id: int) -> Author:
    result = await db.execute(select(Author).where(Author.id == author_id))
    author = result.scalar_one_or_none()
    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Autor não encontrado."
        )
    return author


@router.get("/", response_model=list[AuthorOut])
async def list_authors(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Author))
    return list(result.scalars().all())


@router.get("/{author_id}", response_model=AuthorOut)
async def get_author(author_id: int, db: AsyncSession = Depends(get_db)):
    return await _get_or_404(db, author_id)


@router.post("/", response_model=AuthorOut, status_code=201, dependencies=[Depends(require_admin)])
async def create_author(data: AuthorCreate, db: AsyncSession = Depends(get_db)):
    author = Author(**data.model_dump())
    db.add(author)
    await db.commit()
    await db.refresh(author)
    return author


@router.put("/{author_id}", response_model=AuthorOut, dependencies=[Depends(require_admin)])
async def update_author(
    author_id: int, data: AuthorUpdate, db: AsyncSession = Depends(get_db)
):
    author = await _get_or_404(db, author_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(author, field, value)
    await db.commit()
    await db.refresh(author)
    return author


@router.delete("/{author_id}", status_code=204, dependencies=[Depends(require_admin)])
async def delete_author(author_id: int, db: AsyncSession = Depends(get_db)):
    author = await _get_or_404(db, author_id)
    await db.delete(author)
    await db.commit()
