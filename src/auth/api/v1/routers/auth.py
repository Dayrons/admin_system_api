from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from dependencies.db_session import get_db
from auth.security import security

from auth.models.user import User
from auth.schema.user_eschema import UserCreate

router = APIRouter(prefix="/v1/auth",  tags=["Auth"])

@router.post("/signin")
def signin(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 1. Buscar al usuario
    user = db.query(User).filter(User.name == form_data.username).first()
    
    # 2. Validar existencia y contraseña
    if not user or not security.verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Crear el Token
    access_token = security.create_access_token(data={"sub": user.name})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"name": user.name, "id": user.id}
    }
    
@router.post("/signup", response_model=None)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    # 1. Verificar si el usuario ya existe
    user_exists = db.query(User).filter(User.name == user_in.name).first()
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está registrado"
        )

    # 2. Encriptar la contraseña antes de guardar
    
    print(user_in.password)
    hashed_password = security.get_password_hash(user_in.password)

    # 3. Crear el objeto para la DB
    new_user = User(
        name=user_in.name,
        password=hashed_password,
        is_active=True
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {
            "status": "success",
            "message": "Usuario creado correctamente",
            "user": {
                "id": new_user.id,
                "name": new_user.name
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar en base de datos: {str(e)}"
        )