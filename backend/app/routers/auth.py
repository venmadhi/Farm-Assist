from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import datetime

from ..database import get_db
from ..models import Farmer
from ..schemas import FarmerRegister, FarmerLogin, Token
from ..utils.security import verify_password, get_password_hash, create_access_token
from ..config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login-form-fallback", auto_error=False)

def get_current_farmer(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Farmer:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
        
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        phone_number: str = payload.get("sub")
        if phone_number is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    farmer = db.query(Farmer).filter(Farmer.phone_number == phone_number).first()
    if farmer is None:
        raise credentials_exception
    return farmer

@router.post("/register", response_model=Token)
def register(farmer_in: FarmerRegister, db: Session = Depends(get_db)):
    # Check if phone number already exists
    phone_clean = farmer_in.phone_number.strip()
    existing = db.query(Farmer).filter(Farmer.phone_number == phone_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A farmer with this phone number is already registered."
        )
        
    hashed_password = get_password_hash(farmer_in.password)
    new_farmer = Farmer(
        full_name=farmer_in.full_name,
        phone_number=phone_clean,
        password_hash=hashed_password,
        preferred_language=farmer_in.preferred_language or "english"
    )
    db.add(new_farmer)
    db.commit()
    db.refresh(new_farmer)
    
    # Create default Farm for the farmer
    from ..models import Farm
    default_farm = Farm(
        farmer_id=new_farmer.id,
        farm_name="Primary Farm",
        location_district=farmer_in.location_district or "Palakkad",
        soil_type=farmer_in.soil_type or "Laterite",
        land_area_acres=farmer_in.land_area_acres or 1.0,
        water_availability="medium",
        irrigation_type="manual"
    )
    db.add(default_farm)
    db.commit()
    
    # Generate token
    access_token = create_access_token(data={"sub": new_farmer.phone_number})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
def login(login_in: FarmerLogin, db: Session = Depends(get_db)):
    phone_clean = login_in.phone_number.strip()
    print(f"DEBUG LOGIN INPUT - Phone: '{phone_clean}' (len: {len(phone_clean)}), Password: '{login_in.password}'")
    farmer = db.query(Farmer).filter(Farmer.phone_number == phone_clean).first()
    if farmer:
        print(f"DEBUG LOGIN - Found farmer with ID: {farmer.id}, Hashed password in DB: '{farmer.password_hash}'")
        match = verify_password(login_in.password, farmer.password_hash)
        print(f"DEBUG LOGIN - Password match result: {match}")
    else:
        print(f"DEBUG LOGIN - No farmer found in database with phone number '{login_in.phone_number}'")
        
    if not farmer or not verify_password(login_in.password, farmer.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect phone number or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(data={"sub": farmer.phone_number})
    return {"access_token": access_token, "token_type": "bearer"}
