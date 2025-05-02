import pytest
from fastapi import status
from models.spimex import SpimexTradingResults
from sqlalchemy import select, desc, and_
from datetime import date, timedelta, datetime


@pytest.mark.asyncio
async def test_return_health_check(client):
    response = await client.get('/healthy')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'status': 'Healthy'}


@pytest.mark.asyncio
async def test_get_last_trading_dates(client, create_list_trade):
    response = await client.get('results/latest_trading_dates')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == str([str(date.today()), str(date.today() - timedelta(days=1)),
                                   str(date.today() - timedelta(days=2))])


@pytest.mark.asyncio
async def test_get_last_trading_dates_limit_1(client, create_list_trade):
    response2 = await client.get('results/latest_trading_dates?limit=1')
    assert response2.status_code == status.HTTP_200_OK
    response2.json() == date.today()


@pytest.mark.asyncio
async def test_get_last_trading_dates_negative_limit(client, create_list_trade):
    response = await client.get('results/latest_trading_dates?limit=-6')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == '[]'


@pytest.mark.asyncio
async def test_get_last_trading_dates_extra_param(client, create_list_trade):
    response = await client.get('results/latest_trading_dates?limit=2?page=1')
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_dynamics(client, create_list_trade, db):
    start_date = datetime(year=2025, month=4, day=1)
    response = await client.get(f'results/trading_period?start_date={start_date}')
    trades = await db.scalars(select(SpimexTradingResults).where(
        SpimexTradingResults.date >= start_date).order_by(desc(SpimexTradingResults.date)))
    trades = trades.all()
    assert response.status_code == status.HTTP_200_OK
    assert len(trades) == len(response.json())
    for i in range(len(trades)):
        assert trades[i].id == response.json()[i]['id']
        assert trades[i].oil_id == response.json()[i]['oil_id']


@pytest.mark.asyncio
async def test_get_dynamics_invalid_period(client, create_list_trade, db):
    start_date = date.today() + timedelta(days=2)
    response = await client.get(f'results/trading_period?start_date={start_date}')
    assert response.status_code == 400
    assert response.json() == {'detail': 'Start day should be lower than end date.'}


@pytest.mark.asyncio
async def test_get_dynamics_with_params(client, create_list_trade, db):
    start_date = date.today() - timedelta(days=2)
    oil_id = 'DSC5'
    response = await client.get(f'results/trading_period?start_date={start_date}&oil_id={oil_id}')
    trades = await db.scalars(select(SpimexTradingResults).where(and_(
        SpimexTradingResults.oil_id == oil_id,
        SpimexTradingResults.date >= start_date)).order_by(desc(SpimexTradingResults.date)))
    trades = trades.all()
    assert response.status_code == 200
    assert len(trades) == len(response.json()) == 1
    assert response.json()[0]['oil_id'] == trades[0].oil_id


@pytest.mark.asyncio
async def test_get_dynamics_with_invalid_params(client, create_list_trade):
    start_date = date.today() - timedelta(days=2)
    oil_id = 'A1OO'
    delivery_type_id = 'F'
    response = await client.get(f'results/trading_period?start_date={start_date}&oil_id={oil_id}&'
                                f'delivery_type_id={delivery_type_id}')
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_trading_results_empty_db(client):
    response = await client.get(f'results/latest_trade')
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_trading_results(client, create_list_trade, db):
    response = await client.get('results/latest_trade')
    trades = await db.scalars(select(SpimexTradingResults).where(SpimexTradingResults.date == date.today()).
                              order_by(desc(SpimexTradingResults.date)))
    trades = trades.all()
    assert response.status_code == 200
    assert len(response.json()) == len(trades) == 1
    assert response.json()[0]['id'] == trades[0].id
    assert response.json()[0]['oil_id'] == trades[0].oil_id
    assert response.json()[0]['date'].split('T')[0] == str(trades[0].date.date()) == str(date.today())


@pytest.mark.asyncio
async def test_get_trading_results_with_params(client, create_list_trade, db):
    oil_id = 'DSC5'
    delivery_type_id = 'U'
    response = await client.get(f'results/latest_trade?oil_id={oil_id}&delivery_type_id={delivery_type_id}')
    trades = await db.scalars(select(SpimexTradingResults).where(and_(
        SpimexTradingResults.oil_id == oil_id,
        SpimexTradingResults.delivery_type_id == delivery_type_id)).order_by(desc(SpimexTradingResults.date)))
    trades = trades.all()
    assert response.status_code == 200
    assert len(response.json()) == len(trades) == 1
    assert response.json()[0]['id'] == trades[0].id
    assert response.json()[0]['oil_id'] == trades[0].oil_id
    assert (response.json()[0]['date'].split('T')[0] == str(trades[0].date.date()) ==
            str(date.today() - timedelta(days=1)))

