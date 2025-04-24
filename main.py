from fastapi import FastAPI
from routers import spimex_results

app = FastAPI()

app.include_router(spimex_results.router)


@app.get('/')
async def start() -> dict:
    return {'API': 'Spimex Trading Results'}
