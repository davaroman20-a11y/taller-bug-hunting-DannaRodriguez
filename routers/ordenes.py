from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
from typing import List

from core.database import obtener_bd
from models.orden import Orden as OrdenModel
from models.mecanico import Mecanico as MecanicoModel
from schemas.schemas import OrdenCreate, OrdenPatch, OrdenResponse

router = APIRouter(prefix="/ordenes", tags=["Órdenes"])

@router.get("/", response_model=List[OrdenResponse])
async def obtener_ordenes(db: AsyncSession = Depends(obtener_bd)):
    resultado = await db.execute(
        select(OrdenModel).options(
            selectinload(OrdenModel.mecanico)
        )
    )

    ordenes = resultado.scalars().all()

    return ordenes

@router.post("/", status_code=201, response_model=OrdenResponse)
async def crear_orden(orden: OrdenCreate, db: AsyncSession = Depends(obtener_bd)):

    resultado = await db.execute(
        select(MecanicoModel).where(
            MecanicoModel.id == orden.mecanico_id,
            MecanicoModel.activo == True
        )
    )

    mecanico = resultado.scalar_one_or_none()

    if not mecanico:
        raise HTTPException(
            status_code=400,
            detail="El mecánico no existe o está inactivo"
        )

    nueva_orden = OrdenModel(**orden.model_dump())
    db.add(nueva_orden)
    await db.commit()
    await db.refresh(nueva_orden)

    return nueva_orden


@router.patch("/{orden_id}", response_model=OrdenResponse)
async def actualizar_orden(orden_id: int, orden_patch: OrdenPatch, db: AsyncSession = Depends(obtener_bd)):
    resultado = await db.execute(select(OrdenModel).where(OrdenModel.id == orden_id))
    orden_db = resultado.scalar_one_or_none()
    if not orden_db:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    datos = orden_patch.model_dump()
    for campo, valor in datos.items():
        setattr(orden_db, campo, valor)

    await db.commit()
    await db.refresh(orden_db)
    return orden_db

@router.delete("/{orden_id}", status_code=204)
async def eliminar_orden(orden_id: int, db: AsyncSession = Depends(obtener_bd)):
    resultado = await db.execute(select(OrdenModel).where(OrdenModel.id == orden_id))
    orden_db = resultado.scalar_one_or_none()
    if not orden_db:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    db.delete(orden_db)
    await db.commit()
    return None