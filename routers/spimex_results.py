from datetime import date
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException, Header
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db_depends import get_db
from sqlalchemy import select, desc, and_, func
from models.spimex import SpimexTradingResults
from config import DEFAULT_CACHE_TTL
from fastapi.encoders import jsonable_encoder


router = APIRouter(prefix='/results', tags=['results'])


async def days_limit(limit: int = 5) -> int:
    return limit


@router.get('/latest_trading_dates')
async def get_last_trading_dates(db: Annotated[AsyncSession, Depends(get_db)],
                                 limit: int = Depends(days_limit),
                                 cache_control: Annotated[str, Header()] = f'max-age={DEFAULT_CACHE_TTL}'
                                 ) -> JSONResponse:
    results = await db.scalars(select(SpimexTradingResults.date).group_by(SpimexTradingResults.date).
                               order_by(desc(SpimexTradingResults.date)))
    results = [r.date() for r in results.all()[:limit]]
    return JSONResponse(jsonable_encoder(results))


@router.get('/trading_period')
async def get_dynamics(
                       db: Annotated[AsyncSession, Depends(get_db)],
                       start_date: date, end_date: date = date.today(),
                       oil_id: Annotated[Optional[str], Query(max_length=4, min_length=4)] = None,
                       delivery_type_id: Annotated[Optional[str], Query(min_length=1, max_length=1)] = None,
                       delivery_basis_id: Annotated[Optional[str], Query(min_length=3)] = None,
                       cache_control: Annotated[str, Header()] = f'max-age={DEFAULT_CACHE_TTL}'
                       ) -> JSONResponse:
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Start day should be lower than end date.'
        )
    trades = await db.scalars(select(
        SpimexTradingResults
                ).where(and_(
                            SpimexTradingResults.date >= start_date,
                            SpimexTradingResults.date <= end_date,
                            SpimexTradingResults.oil_id == oil_id.upper() if oil_id else not None,
                            SpimexTradingResults.delivery_type_id == delivery_type_id.upper()
                            if delivery_type_id else not None,
                            SpimexTradingResults.delivery_basis_id == delivery_basis_id.upper()
                            if delivery_basis_id else not None
                            )
                        ).order_by(desc(SpimexTradingResults.date))
                )

    return JSONResponse(jsonable_encoder(trades.all()))


@router.get('/latest_trade')
async def get_trading_results(db: Annotated[AsyncSession, Depends(get_db)],
                              oil_id: Annotated[Optional[str], Query(max_length=4, min_length=4)] = None,
                              delivery_type_id: Annotated[Optional[str], Query(min_length=1, max_length=1)] = None,
                              delivery_basis_id: Annotated[Optional[str], Query(min_length=3)] = None,
                              cache_control: Annotated[str, Header()] = f'max-age={DEFAULT_CACHE_TTL}'
                              ) -> JSONResponse:
    latest_trade_date = await db.scalar(select(func.max(SpimexTradingResults.date)))
    trades = await db.scalars(select(SpimexTradingResults).where(and_(
                    SpimexTradingResults.date == latest_trade_date,
                    SpimexTradingResults.oil_id == oil_id.upper() if oil_id else not None,
                    SpimexTradingResults.delivery_type_id == delivery_type_id.upper()
                    if delivery_type_id else not None,
                    SpimexTradingResults.delivery_basis_id == delivery_basis_id.upper()
                    if delivery_basis_id else not None)).order_by(SpimexTradingResults.oil_id))

    return JSONResponse(jsonable_encoder(trades.all()))
