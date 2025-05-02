from fastapi import FastAPI
from routers import spimex_results

app = FastAPI()

app.include_router(spimex_results.router)


@app.get('/healthy')
async def health_check() -> dict:
    return {'status': 'Healthy'}
