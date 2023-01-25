from typing import List

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from compute.rssa import RSSACompute
from compute.utils import *
from data.moviedatabase import SessionLocal
from data.models.schema import MovieSchema, RatingsSchema
from router import cybered, iers, users, study, admin
from data.movies import get_movies, get_movies_by_ids

from util.docs_metadata import tags_metadata

# app = FastAPI(root_path='/newrs/api/v1')
app = FastAPI(
    openapi_tags=tags_metadata,
    title='RSSA Project API',
    description='API for all the RSSA projects, experiments, and alternate movie databases.',
    version='0.0.1',
    terms_of_service='https://rssa.recsys.dev/terms'
)

# contact={
#     'name': '',
#     'url': '',
#     'email': '',
# },
# license_info={
#     'name': '',
#     'url': '',
# }

rssa_itm_pop, rssa_ave_scores = get_rssa_data()
rssa_model_path = get_rssa_model_path()
rssalgs = RSSACompute(rssa_model_path, rssa_itm_pop, rssa_ave_scores)

origins = [
    'https://cybered.recsys.dev',
    'https://cybered.recsys.dev/*',
    'http://localhost:3000',
    'http://localhost:3000/*',
]

app.include_router(cybered.router)
app.include_router(iers.router)
app.include_router(users.router)
app.include_router(study.router)
app.include_router(admin.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get('/')
async def root():
    """
    Hello World!
    """
    return {'message': 'Hello World'}


@app.get('/data/all/')
async def get_data_zip():
    """
    Downloads a zip file containing data files and models to bootstrap the
    project template for the Advanced Decision Support Systems course taught by
    Dr. Bart Knijnenburg during the Fall 2022 semester.
    
    Returns a a zip file containing the data files and models.
    """
    return FileResponse('datafiles/rssa_all.zip',
                        media_type='application/octet-stream',
                        filename='data/rssa_all.zip')


@app.get('/movies/', response_model=List[MovieSchema], tags=['movie'])
async def read_movies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    movies = get_movies(db, skip=skip, limit=limit)

    return movies


@app.post('/recommendation/', response_model=List[MovieSchema], tags=['movie'])
async def create_recommendations(rated_movies: RatingsSchema, db: Session = Depends(get_db)):
    recs = rssalgs.get_condition_prediction(rated_movies.ratings,
                                            rated_movies.user_id, rated_movies.rec_type, rated_movies.num_rec)
    movies = get_movies_by_ids(db, recs)

    return movies
