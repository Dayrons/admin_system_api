from fastapi import APIRouter

from . import  system 

api_router = APIRouter()


api_router.include_router(system.router)
