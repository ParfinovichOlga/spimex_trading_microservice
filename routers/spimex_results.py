from datetime import date
from typing import Annotated, Optional
from fastapi import (
    APIRouter, Depends, Query,
    status, HTTPException, BackgroundTasks
                    )
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db_depends import get_db
from sqlalchemy import select, desc, and_, func
from models.spimex import SpimexTradingResults
from starlette.requests import Request
from schema import CreateSpimexTrading
from service import redis_service

router = APIRouter(prefix='/results', tags=['results'])


async def days_limit(limit: int = 5) -> int:
    """Set limit latest trade dates"""
    if limit < 0:
        return 0
    return limit


@router.get('/latest_trading_dates')
async def get_last_trading_dates(request: Request, backgroundtasks: BackgroundTasks,
                                 db: Annotated[AsyncSession, Depends(get_db)],
                                 limit: int = Depends(days_limit)
                                 ) -> JSONResponse:
    cached_result = await redis_service.get_cache(request)
    if cached_result:
        print('uuuuu')
        return cached_result
    results = await db.scalars(select(SpimexTradingResults.date).group_by(SpimexTradingResults.date).
                               order_by(desc(SpimexTradingResults.date)))
    results = str([str(r.date()) for r in results.all()[:limit]])
    backgroundtasks.add_task(redis_service.set_cache, request, results)
    return results


@router.get('/trading_period')
async def get_dynamics(request: Request, backgroundtasks: BackgroundTasks,
                       db: Annotated[AsyncSession, Depends(get_db)],
                       start_date: date, end_date: date = date.today(),
                       oil_id: Annotated[Optional[str], Query(max_length=4, min_length=4)] = None,
                       delivery_type_id: Annotated[Optional[str], Query(min_length=1, max_length=1)] = None,
                       delivery_basis_id: Annotated[Optional[str], Query(min_length=3)] = None,
                       ) -> JSONResponse:
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Start day should be lower than end date.'
        )
    cached_result = await redis_service.get_cache(request)
    if cached_result:
        return cached_result
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
    trades = trades.all()
    res = str([CreateSpimexTrading.model_validate(obj).model_dump() for obj in trades])
    backgroundtasks.add_task(redis_service.set_cache, request, res)
    return trades


@router.get('/latest_trade')
async def get_trading_results(request: Request, backgroundtasks: BackgroundTasks,
                              db: Annotated[AsyncSession, Depends(get_db)],
                              oil_id: Annotated[Optional[str], Query(max_length=4, min_length=4)] = None,
                              delivery_type_id: Annotated[
                                  Optional[str], Query(min_length=1, max_length=1)
                                                         ] = None,
                              delivery_basis_id: Annotated[Optional[str], Query(min_length=3)] = None
                              ) -> JSONResponse:
    cached_result = await redis_service.get_cache(request)
    if cached_result:
        return cached_result
    latest_trade_date = await db.scalar(select(func.max(SpimexTradingResults.date)))
    trades = await db.scalars(select(SpimexTradingResults).where(and_(
                    SpimexTradingResults.date == latest_trade_date,
                    SpimexTradingResults.oil_id == oil_id.upper() if oil_id else not None,
                    SpimexTradingResults.delivery_type_id == delivery_type_id.upper()
                    if delivery_type_id else not None,
                    SpimexTradingResults.delivery_basis_id == delivery_basis_id.upper()
                    if delivery_basis_id else not None)).order_by(SpimexTradingResults.oil_id))
    trades = trades.all()
    res = str([CreateSpimexTrading.model_validate(obj).model_dump() for obj in trades])
    backgroundtasks.add_task(redis_service.set_cache, request, res)
    return trades
