from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, require_admin
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate
from fastapi import HTTPException, status

router = APIRouter(prefix="/categories", tags=["categories"])


async def _get_or_404(db: AsyncSession, category_id: int) -> Category:
    result = await db.execute(select(Category).where(Category.id == category_id))
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")
    return cat


@router.get("/", response_model=list[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category))
    return list(result.scalars().all())


@router.get("/{category_id}", response_model=CategoryOut)
async def get_category(category_id: int, db: AsyncSession = Depends(get_db)):
    return await _get_or_404(db, category_id)


@router.post("/", response_model=CategoryOut, status_code=201, dependencies=[Depends(require_admin)])
async def create_category(data: CategoryCreate, db: AsyncSession = Depends(get_db)):
    # Check unique name/slug
    existing = await db.execute(
        select(Category).where((Category.name == data.name) | (Category.slug == data.slug))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nome ou slug já existente.")
    cat = Category(**data.model_dump())
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


@router.put("/{category_id}", response_model=CategoryOut, dependencies=[Depends(require_admin)])
async def update_category(
    category_id: int, data: CategoryUpdate, db: AsyncSession = Depends(get_db)
):
    cat = await _get_or_404(db, category_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(cat, field, value)
    await db.commit()
    await db.refresh(cat)
    return cat


@router.delete("/{category_id}", status_code=204, dependencies=[Depends(require_admin)])
async def delete_category(category_id: int, db: AsyncSession = Depends(get_db)):
    cat = await _get_or_404(db, category_id)
    await db.delete(cat)
    await db.commit()
