# BuildOptima Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete FastAPI backend with PostgreSQL, JWT auth, a CRUD builds API, and a weighted greedy optimizer engine that selects PC parts from a seeded database.

**Architecture:** FastAPI app with sync SQLAlchemy sessions; four tables (users, builds, build_components, parts); JWT access+refresh tokens via python-jose/bcrypt; optimization runs entirely in-process with a greedy budget-allocation algorithm; tests run against an in-memory SQLite database via a `get_db` override.

**Tech Stack:** Python 3.12, FastAPI 0.115, SQLAlchemy 2.0, PostgreSQL (psycopg2-binary), python-jose, passlib[bcrypt], pydantic-settings, pytest, SQLite (tests only)

---

## File Map

```
backend/
  main.py                        created Task 11
  seed.py                        created Task 10
  requirements.txt               created Task 1
  pytest.ini                     created Task 1
  .env.example                   created Task 1

  core/
    __init__.py                  created Task 1
    config.py                    created Task 2
    security.py                  created Task 5

  db/
    __init__.py                  created Task 1
    database.py                  created Task 2

  models/
    __init__.py                  created Task 3
    user.py                      created Task 3
    build.py                     created Task 3
    part.py                      created Task 3

  schemas/
    __init__.py                  created Task 4
    auth.py                      created Task 4
    build.py                     created Task 4
    optimizer.py                 created Task 4

  routers/
    __init__.py                  created Task 11
    auth.py                      created Task 7
    builds.py                    created Task 8
    optimizer.py                 created Task 9

  tests/
    __init__.py                  created Task 6
    conftest.py                  created Task 6
    test_auth.py                 created Task 7
    test_builds.py               created Task 8
    test_optimizer.py            created Task 9
```

---

## Task 1: Project Scaffold

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/pytest.ini`
- Create: `backend/.env.example`
- Create: `backend/core/__init__.py`, `backend/db/__init__.py`, `backend/models/__init__.py`, `backend/schemas/__init__.py`, `backend/routers/__init__.py`, `backend/tests/__init__.py`

- [ ] **Step 1: Create the backend directory and all package init files**

```bash
mkdir -p backend/core backend/db backend/models backend/schemas backend/routers backend/tests
touch backend/core/__init__.py backend/db/__init__.py backend/models/__init__.py \
      backend/schemas/__init__.py backend/routers/__init__.py backend/tests/__init__.py
```

- [ ] **Step 2: Write `backend/requirements.txt`**

```
fastapi==0.115.5
sqlalchemy==2.0.36
psycopg2-binary==2.9.10
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
pydantic-settings==2.6.1
pydantic[email]==2.10.2
python-dotenv==1.0.1
uvicorn[standard]==0.32.1
pytest==8.3.4
httpx==0.28.0
```

- [ ] **Step 3: Write `backend/pytest.ini`**

```ini
[pytest]
pythonpath = .
testpaths = tests
```

- [ ] **Step 4: Write `backend/.env.example`**

```
DATABASE_URL=postgresql://user:password@localhost:5432/buildoptima
JWT_SECRET_KEY=your-secret-key-here-minimum-32-characters
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

- [ ] **Step 5: Install dependencies (run from `backend/` with venv active)**

```bash
pip install -r requirements.txt
```

Expected: packages install without errors.

- [ ] **Step 6: Commit**

```bash
git add backend/
git commit -m "feat: scaffold backend project structure and dependencies"
```

---

## Task 2: Configuration and Database Session

**Files:**
- Create: `backend/core/config.py`
- Create: `backend/db/database.py`

- [ ] **Step 1: Write `backend/core/config.py`**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    jwt_secret_key: str
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    model_config = {"env_file": ".env"}


settings = Settings()
```

- [ ] **Step 2: Write `backend/db/database.py`**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from core.config import settings


engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 3: Verify imports resolve (run from `backend/`)**

```bash
python -c "from db.database import Base, get_db; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/core/config.py backend/db/database.py
git commit -m "feat: add settings config and SQLAlchemy session setup"
```

---

## Task 3: SQLAlchemy Models

**Files:**
- Create: `backend/models/user.py`
- Create: `backend/models/build.py`
- Create: `backend/models/part.py`
- Modify: `backend/models/__init__.py`

- [ ] **Step 1: Write `backend/models/user.py`**

```python
from datetime import datetime, timezone
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    builds: Mapped[list["Build"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
```

- [ ] **Step 2: Write `backend/models/build.py`**

```python
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, ForeignKey, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base


class Build(Base):
    __tablename__ = "builds"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    build_name: Mapped[str] = mapped_column(String(255))
    use_case: Mapped[str] = mapped_column(String(50))
    budget: Mapped[int] = mapped_column(Integer)
    total_price: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="builds")
    components: Mapped[list["BuildComponent"]] = relationship(
        back_populates="build", cascade="all, delete-orphan"
    )


class BuildComponent(Base):
    __tablename__ = "build_components"

    id: Mapped[int] = mapped_column(primary_key=True)
    build_id: Mapped[int] = mapped_column(ForeignKey("builds.id", ondelete="CASCADE"))
    component_category: Mapped[str] = mapped_column(String(50))
    part_name: Mapped[str] = mapped_column(String(255))
    part_price: Mapped[float] = mapped_column(Float)
    reason_selected: Mapped[str] = mapped_column(Text)

    build: Mapped["Build"] = relationship(back_populates="components")
```

- [ ] **Step 3: Write `backend/models/part.py`**

```python
from sqlalchemy import String, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column
from db.database import Base


class Part(Base):
    __tablename__ = "parts"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String(255))
    brand: Mapped[str] = mapped_column(String(100))
    price: Mapped[float] = mapped_column(Float)
    specs: Mapped[dict] = mapped_column(JSON)
```

- [ ] **Step 4: Write `backend/models/__init__.py`**

```python
from .user import User
from .build import Build, BuildComponent
from .part import Part

__all__ = ["User", "Build", "BuildComponent", "Part"]
```

- [ ] **Step 5: Verify models import cleanly**

```bash
python -c "import models; print('OK')"
```

Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add backend/models/
git commit -m "feat: add SQLAlchemy models for users, builds, and parts"
```

---

## Task 4: Pydantic Schemas

**Files:**
- Create: `backend/schemas/auth.py`
- Create: `backend/schemas/build.py`
- Create: `backend/schemas/optimizer.py`
- Modify: `backend/schemas/__init__.py`

- [ ] **Step 1: Write `backend/schemas/auth.py`**

```python
from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str
```

- [ ] **Step 2: Write `backend/schemas/build.py`**

```python
from datetime import datetime
from pydantic import BaseModel


class ComponentIn(BaseModel):
    category: str
    part_name: str
    part_price: float
    reason_selected: str


class BuildSaveRequest(BaseModel):
    build_name: str
    use_case: str
    budget: int
    total_price: float
    components: list[ComponentIn]


class ComponentOut(BaseModel):
    id: int
    component_category: str
    part_name: str
    part_price: float
    reason_selected: str

    model_config = {"from_attributes": True}


class BuildOut(BaseModel):
    id: int
    build_name: str
    use_case: str
    budget: int
    total_price: float
    created_at: datetime

    model_config = {"from_attributes": True}


class BuildDetailOut(BuildOut):
    components: list[ComponentOut]
```

- [ ] **Step 3: Write `backend/schemas/optimizer.py`**

```python
from typing import Any, Literal
from pydantic import BaseModel, field_validator


class OptimizeRequest(BaseModel):
    budget: int
    use_case: Literal["gaming", "content_creation", "workstation", "general"]
    future_proofing: bool = False
    owns_gpu: bool = False
    prefer_quiet_cooling: bool = False

    @field_validator("budget")
    @classmethod
    def budget_in_range(cls, v: int) -> int:
        if not 300 <= v <= 5000:
            raise ValueError("Budget must be between 300 and 5000")
        return v


class ComponentResult(BaseModel):
    category: str
    name: str
    brand: str
    price: float
    reason: str
    specs: dict[str, Any]


class OptimizeResponse(BaseModel):
    use_case: str
    budget: int
    total_price: float
    components: list[ComponentResult]
```

- [ ] **Step 4: Verify schemas import cleanly**

```bash
python -c "from schemas.auth import RegisterRequest; from schemas.build import BuildDetailOut; from schemas.optimizer import OptimizeRequest; print('OK')"
```

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add backend/schemas/
git commit -m "feat: add Pydantic schemas for auth, builds, and optimizer"
```

---

## Task 5: Security Utilities

**Files:**
- Create: `backend/core/security.py`
- Create: `backend/tests/test_security.py`

- [ ] **Step 1: Write the failing tests for security utilities**

Create `backend/tests/test_security.py`:

```python
import pytest
from core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


def test_hash_password_produces_different_hash_each_time():
    h1 = hash_password("secret123")
    h2 = hash_password("secret123")
    assert h1 != h2


def test_verify_password_correct_password_returns_true():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed) is True


def test_verify_password_wrong_password_returns_false():
    hashed = hash_password("secret123")
    assert verify_password("wrongpass", hashed) is False


def test_create_access_token_decode_returns_sub():
    token = create_access_token({"sub": "42"})
    payload = decode_token(token)
    assert payload["sub"] == "42"
    assert payload["type"] == "access"


def test_create_refresh_token_decode_returns_sub():
    token = create_refresh_token({"sub": "42"})
    payload = decode_token(token)
    assert payload["sub"] == "42"
    assert payload["type"] == "refresh"


def test_decode_token_invalid_token_raises():
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        decode_token("not.a.valid.token")
    assert exc_info.value.status_code == 401
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && pytest tests/test_security.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` — `core.security` does not exist yet.

- [ ] **Step 3: Write `backend/core/security.py`**

```python
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from core.config import settings
from db.database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm="HS256")


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    from models.user import User

    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
        )
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_security.py -v
```

Expected: 6 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/core/security.py backend/tests/test_security.py
git commit -m "feat: add JWT and bcrypt security utilities"
```

---

## Task 6: Test Infrastructure

**Files:**
- Create: `backend/tests/conftest.py`

- [ ] **Step 1: Write `backend/tests/conftest.py`**

```python
import os

# Set env vars before any app import so pydantic-settings picks them up.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-32chars!!"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import models  # noqa: F401 — registers all ORM models with Base
from db.database import Base, get_db
from main import app

_engine = create_engine(
    "sqlite:///:memory:", connect_args={"check_same_thread": False}
)
_TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture
def db(reset_db):
    session = _TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

Note: `main` is imported here, so `main.py` must exist before running tests. Create a stub in Task 11 Step 1 before running any full test suite. The security-only tests in Task 5 do not use this conftest.

- [ ] **Step 2: Commit**

```bash
git add backend/tests/conftest.py
git commit -m "feat: add pytest test infrastructure with SQLite override"
```

---

## Task 7: Auth Router + Tests

**Files:**
- Create: `backend/routers/auth.py`
- Create: `backend/tests/test_auth.py`

- [ ] **Step 1: Write the failing auth tests**

Create `backend/tests/test_auth.py`:

```python
def test_register_returns_201_with_tokens(client):
    res = client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "password123"},
    )
    assert res.status_code == 201
    body = res.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_register_duplicate_email_returns_400(client):
    payload = {"email": "dup@example.com", "password": "password123"}
    client.post("/auth/register", json=payload)
    res = client.post("/auth/register", json=payload)
    assert res.status_code == 400


def test_register_short_password_returns_422(client):
    res = client.post(
        "/auth/register", json={"email": "user@example.com", "password": "short"}
    )
    assert res.status_code == 422


def test_login_valid_credentials_returns_tokens(client):
    client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "password123"},
    )
    res = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "password123"},
    )
    assert res.status_code == 200
    assert "access_token" in res.json()
    assert "refresh_token" in res.json()


def test_login_wrong_password_returns_401(client):
    client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "password123"},
    )
    res = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "wrongpass"},
    )
    assert res.status_code == 401


def test_login_unknown_email_returns_401(client):
    res = client.post(
        "/auth/login",
        json={"email": "ghost@example.com", "password": "password123"},
    )
    assert res.status_code == 401


def test_refresh_returns_new_access_token_only(client):
    reg = client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "password123"},
    )
    refresh_token = reg.json()["refresh_token"]
    res = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert res.status_code == 200
    body = res.json()
    assert "access_token" in body
    assert "refresh_token" not in body


def test_refresh_with_access_token_returns_401(client):
    reg = client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "password123"},
    )
    access_token = reg.json()["access_token"]
    res = client.post("/auth/refresh", json={"refresh_token": access_token})
    assert res.status_code == 401
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_auth.py -v
```

Expected: errors — `routers/auth.py` does not exist yet (also need the `main.py` stub from Task 11 Step 1 first — see note below).

> **Note:** Before running tests that use `client`, you must first create the stub `main.py` from Task 11 Step 1. Do that now, then return here.

- [ ] **Step 3: Write `backend/routers/auth.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.database import get_db
from models.user import User
from schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    AccessTokenResponse,
    RefreshRequest,
)
from core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=body.email, hashed_password=hash_password(body.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(
        access_token=create_access_token({"sub": str(user.id)}),
        refresh_token=create_refresh_token({"sub": str(user.id)}),
    )


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(
        access_token=create_access_token({"sub": str(user.id)}),
        refresh_token=create_refresh_token({"sub": str(user.id)}),
    )


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    payload = decode_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return AccessTokenResponse(
        access_token=create_access_token({"sub": str(user.id)})
    )
```

- [ ] **Step 4: Register the router in `main.py` (update the stub)**

Open `backend/main.py` and ensure it includes:
```python
from routers import auth as auth_router
app.include_router(auth_router.router)
```

(Full `main.py` is written in Task 11; for now add auth only.)

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_auth.py -v
```

Expected: 8 tests pass.

- [ ] **Step 6: Commit**

```bash
git add backend/routers/auth.py backend/tests/test_auth.py
git commit -m "feat: add auth endpoints — register, login, refresh"
```

---

## Task 8: Builds Router + Tests

**Files:**
- Create: `backend/routers/builds.py`
- Create: `backend/tests/test_builds.py`

- [ ] **Step 1: Write the failing builds tests**

Create `backend/tests/test_builds.py`:

```python
import pytest
from core.security import hash_password
from models.user import User
from models.build import Build

SAMPLE_BUILD = {
    "build_name": "My Gaming Rig",
    "use_case": "gaming",
    "budget": 1500,
    "total_price": 1423.0,
    "components": [
        {
            "category": "cpu",
            "part_name": "Ryzen 5 7600X",
            "part_price": 229.0,
            "reason_selected": "Great gaming CPU",
        }
    ],
}


@pytest.fixture
def auth_headers(client):
    client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "password123"},
    )
    res = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "password123"},
    )
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_save_build_returns_201_with_components(client, auth_headers):
    res = client.post("/builds/save", json=SAMPLE_BUILD, headers=auth_headers)
    assert res.status_code == 201
    body = res.json()
    assert body["build_name"] == "My Gaming Rig"
    assert len(body["components"]) == 1
    assert body["components"][0]["part_name"] == "Ryzen 5 7600X"


def test_save_build_without_auth_returns_401(client):
    res = client.post("/builds/save", json=SAMPLE_BUILD)
    assert res.status_code == 401


def test_list_builds_returns_only_current_user_builds(client, auth_headers, db):
    client.post("/builds/save", json=SAMPLE_BUILD, headers=auth_headers)
    # Another user's build — inserted directly
    other = User(email="other@example.com", hashed_password=hash_password("pass1234"))
    db.add(other)
    db.flush()
    db.add(
        Build(
            user_id=other.id,
            build_name="Other Build",
            use_case="gaming",
            budget=1000,
            total_price=900.0,
        )
    )
    db.commit()
    res = client.get("/builds", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["build_name"] == "My Gaming Rig"


def test_get_build_returns_components(client, auth_headers):
    saved = client.post(
        "/builds/save", json=SAMPLE_BUILD, headers=auth_headers
    ).json()
    res = client.get(f"/builds/{saved['id']}", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()["components"]) == 1


def test_get_build_other_users_build_returns_403(client, auth_headers, db):
    other = User(email="other@example.com", hashed_password=hash_password("pass1234"))
    db.add(other)
    db.flush()
    build = Build(
        user_id=other.id,
        build_name="Other Build",
        use_case="gaming",
        budget=1000,
        total_price=900.0,
    )
    db.add(build)
    db.commit()
    res = client.get(f"/builds/{build.id}", headers=auth_headers)
    assert res.status_code == 403


def test_get_build_not_found_returns_404(client, auth_headers):
    res = client.get("/builds/9999", headers=auth_headers)
    assert res.status_code == 404


def test_delete_build_returns_204(client, auth_headers):
    saved = client.post(
        "/builds/save", json=SAMPLE_BUILD, headers=auth_headers
    ).json()
    res = client.delete(f"/builds/{saved['id']}", headers=auth_headers)
    assert res.status_code == 204
    assert client.get(f"/builds/{saved['id']}", headers=auth_headers).status_code == 404


def test_delete_other_users_build_returns_403(client, auth_headers, db):
    other = User(email="other@example.com", hashed_password=hash_password("pass1234"))
    db.add(other)
    db.flush()
    build = Build(
        user_id=other.id,
        build_name="Other Build",
        use_case="gaming",
        budget=1000,
        total_price=900.0,
    )
    db.add(build)
    db.commit()
    res = client.delete(f"/builds/{build.id}", headers=auth_headers)
    assert res.status_code == 403
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_builds.py -v
```

Expected: errors — `routers/builds.py` does not exist yet.

- [ ] **Step 3: Write `backend/routers/builds.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.database import get_db
from models.user import User
from models.build import Build, BuildComponent
from schemas.build import BuildSaveRequest, BuildOut, BuildDetailOut
from core.security import get_current_user

router = APIRouter(prefix="/builds", tags=["builds"])


@router.post("/save", response_model=BuildDetailOut, status_code=status.HTTP_201_CREATED)
def save_build(
    body: BuildSaveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    build = Build(
        user_id=current_user.id,
        build_name=body.build_name,
        use_case=body.use_case,
        budget=body.budget,
        total_price=body.total_price,
    )
    db.add(build)
    db.flush()
    for comp in body.components:
        db.add(
            BuildComponent(
                build_id=build.id,
                component_category=comp.category,
                part_name=comp.part_name,
                part_price=comp.part_price,
                reason_selected=comp.reason_selected,
            )
        )
    db.commit()
    db.refresh(build)
    return build


@router.get("", response_model=list[BuildOut])
def list_builds(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Build)
        .filter(Build.user_id == current_user.id)
        .order_by(Build.created_at.desc())
        .all()
    )


@router.get("/{build_id}", response_model=BuildDetailOut)
def get_build(
    build_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    build = db.query(Build).filter(Build.id == build_id).first()
    if not build:
        raise HTTPException(status_code=404, detail="Build not found")
    if build.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return build


@router.delete("/{build_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_build(
    build_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    build = db.query(Build).filter(Build.id == build_id).first()
    if not build:
        raise HTTPException(status_code=404, detail="Build not found")
    if build.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    db.delete(build)
    db.commit()
```

- [ ] **Step 4: Add router to `main.py`**

Ensure `main.py` includes:
```python
from routers import builds as builds_router
app.include_router(builds_router.router)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_builds.py -v
```

Expected: 8 tests pass.

- [ ] **Step 6: Commit**

```bash
git add backend/routers/builds.py backend/tests/test_builds.py
git commit -m "feat: add builds CRUD endpoints with ownership enforcement"
```

---

## Task 9: Optimizer Engine + Router + Tests

**Files:**
- Create: `backend/routers/optimizer.py`
- Create: `backend/tests/test_optimizer.py`

- [ ] **Step 1: Write the failing optimizer tests**

Create `backend/tests/test_optimizer.py`:

```python
import pytest
from models.part import Part

# Minimal seed: 2-3 parts per category, enough to exercise the algorithm.
def _make_parts(db):
    parts = [
        # CPU
        Part(category="cpu", name="Budget CPU", brand="AMD", price=130.0,
             specs={"cores": 4, "base_clock_ghz": 3.8, "tdp_watts": 65, "architecture": "Zen 3"}),
        Part(category="cpu", name="Mid CPU", brand="AMD", price=250.0,
             specs={"cores": 6, "base_clock_ghz": 4.7, "tdp_watts": 105, "architecture": "Zen 4"}),
        Part(category="cpu", name="High CPU", brand="Intel", price=420.0,
             specs={"cores": 8, "base_clock_ghz": 5.0, "tdp_watts": 125, "architecture": "Raptor Lake"}),
        # GPU
        Part(category="gpu", name="Budget GPU", brand="AMD", price=200.0,
             specs={"vram_gb": 8, "tdp_watts": 100, "benchmark_score": 50, "tier": "budget"}),
        Part(category="gpu", name="Mid GPU", brand="Nvidia", price=500.0,
             specs={"vram_gb": 12, "tdp_watts": 200, "benchmark_score": 75, "tier": "mid"}),
        Part(category="gpu", name="High GPU", brand="Nvidia", price=800.0,
             specs={"vram_gb": 16, "tdp_watts": 285, "benchmark_score": 90, "tier": "high"}),
        # RAM
        Part(category="ram", name="16GB DDR4", brand="Corsair", price=50.0,
             specs={"size_gb": 16, "speed_mhz": 3200}),
        Part(category="ram", name="32GB DDR5", brand="Corsair", price=100.0,
             specs={"size_gb": 32, "speed_mhz": 6000}),
        # Storage
        Part(category="storage", name="500GB SATA", brand="Samsung", price=45.0,
             specs={"size_gb": 500, "read_speed_mbs": 560, "type": "sata"}),
        Part(category="storage", name="1TB NVMe", brand="WD", price=85.0,
             specs={"size_gb": 1000, "read_speed_mbs": 7300, "type": "nvme"}),
        # Motherboard
        Part(category="motherboard", name="Budget MOBO", brand="MSI", price=90.0,
             specs={"socket": "AM5", "form_factor": "ATX", "chipset": "B650"}),
        Part(category="motherboard", name="Mid MOBO", brand="ASUS", price=190.0,
             specs={"socket": "AM5", "form_factor": "ATX", "chipset": "X670"}),
        # PSU
        Part(category="psu", name="550W Bronze", brand="EVGA", price=60.0,
             specs={"wattage": 550, "efficiency_rating": "bronze"}),
        Part(category="psu", name="750W Gold", brand="Corsair", price=100.0,
             specs={"wattage": 750, "efficiency_rating": "gold"}),
        # Case
        Part(category="case", name="Budget Case", brand="NZXT", price=60.0,
             specs={"form_factor": "ATX", "max_gpu_length_mm": 360}),
        Part(category="case", name="Mid Case", brand="Fractal", price=110.0,
             specs={"form_factor": "ATX", "max_gpu_length_mm": 430}),
        # Cooler
        Part(category="cooler", name="Budget Air", brand="CM", price=30.0,
             specs={"type": "air", "tdp_rating_watts": 150, "noise_db": 36, "is_quiet": False}),
        Part(category="cooler", name="Quiet AIO", brand="NZXT", price=90.0,
             specs={"type": "aio", "tdp_rating_watts": 250, "noise_db": 22, "is_quiet": True}),
    ]
    for p in parts:
        db.add(p)
    db.commit()


@pytest.fixture
def seeded(client, db):
    _make_parts(db)
    return client


def test_optimize_returns_200_with_all_categories(seeded):
    res = seeded.post("/optimize", json={"budget": 1200, "use_case": "gaming"})
    assert res.status_code == 200
    body = res.json()
    assert body["use_case"] == "gaming"
    cats = {c["category"] for c in body["components"]}
    assert cats == {"cpu", "gpu", "ram", "storage", "motherboard", "psu", "case", "cooler"}


def test_optimize_total_never_exceeds_budget(seeded):
    for budget in [700, 1000, 1500, 2000]:
        res = seeded.post("/optimize", json={"budget": budget, "use_case": "gaming"})
        assert res.status_code == 200
        assert res.json()["total_price"] <= budget


def test_optimize_owns_gpu_excludes_gpu_category(seeded):
    res = seeded.post(
        "/optimize", json={"budget": 1000, "use_case": "gaming", "owns_gpu": True}
    )
    assert res.status_code == 200
    cats = {c["category"] for c in res.json()["components"]}
    assert "gpu" not in cats


def test_optimize_prefer_quiet_selects_quiet_cooler(seeded):
    res = seeded.post(
        "/optimize",
        json={"budget": 1500, "use_case": "general", "prefer_quiet_cooling": True},
    )
    assert res.status_code == 200
    cooler = next(c for c in res.json()["components"] if c["category"] == "cooler")
    assert cooler["specs"]["is_quiet"] is True


def test_optimize_future_proofing_flag_accepted(seeded):
    res = seeded.post(
        "/optimize",
        json={"budget": 1500, "use_case": "workstation", "future_proofing": True},
    )
    assert res.status_code == 200
    assert res.json()["total_price"] <= 1500


def test_optimize_budget_below_300_returns_422(seeded):
    res = seeded.post("/optimize", json={"budget": 100, "use_case": "gaming"})
    assert res.status_code == 422


def test_optimize_invalid_use_case_returns_422(seeded):
    res = seeded.post("/optimize", json={"budget": 1000, "use_case": "mining"})
    assert res.status_code == 422


def test_optimize_all_components_have_reason(seeded):
    res = seeded.post("/optimize", json={"budget": 1000, "use_case": "content_creation"})
    assert res.status_code == 200
    for comp in res.json()["components"]:
        assert len(comp["reason"]) > 10
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_optimizer.py -v
```

Expected: errors — `routers/optimizer.py` does not exist yet.

- [ ] **Step 3: Write `backend/routers/optimizer.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from models.part import Part
from schemas.optimizer import OptimizeRequest, OptimizeResponse

router = APIRouter(prefix="/optimize", tags=["optimizer"])

WEIGHTS: dict[str, dict[str, float]] = {
    "gaming": {
        "cpu": 0.18, "gpu": 0.38, "ram": 0.10, "storage": 0.08,
        "motherboard": 0.10, "psu": 0.07, "case": 0.05, "cooler": 0.04,
    },
    "content_creation": {
        "cpu": 0.28, "gpu": 0.20, "ram": 0.18, "storage": 0.12,
        "motherboard": 0.08, "psu": 0.06, "case": 0.04, "cooler": 0.04,
    },
    "workstation": {
        "cpu": 0.32, "gpu": 0.10, "ram": 0.18, "storage": 0.16,
        "motherboard": 0.08, "psu": 0.07, "case": 0.05, "cooler": 0.04,
    },
    "general": {
        "cpu": 0.22, "gpu": 0.18, "ram": 0.16, "storage": 0.12,
        "motherboard": 0.12, "psu": 0.08, "case": 0.06, "cooler": 0.06,
    },
}


def _perf_scores(parts_by_cat: dict) -> dict[int, float]:
    scores: dict[int, float] = {}
    for parts in parts_by_cat.values():
        if not parts:
            continue
        sorted_p = sorted(parts, key=lambda p: p.price)
        lo, hi = sorted_p[0].price, sorted_p[-1].price
        span = hi - lo
        for p in sorted_p:
            scores[p.id] = 1.0 if span == 0 else 0.1 + 0.9 * (p.price - lo) / span
    return scores


def _generate_reason(category: str, part: Part, use_case: str, weight: float) -> str:
    priority = (
        "Top-weighted" if weight >= 0.25
        else "Mid-priority" if weight >= 0.12
        else "Supporting"
    )
    uc = use_case.replace("_", " ")
    s = part.specs
    templates = {
        "cpu": (
            f"{priority} for {uc} — {s.get('cores')} cores at "
            f"{s.get('base_clock_ghz')}GHz ({s.get('architecture')}) handles "
            "demanding workloads with headroom."
        ),
        "gpu": (
            f"{priority} for {uc} — {s.get('vram_gb')}GB VRAM drives smooth "
            "visuals at high resolution."
        ),
        "ram": (
            f"{priority} for {uc} — {s.get('size_gb')}GB at "
            f"{s.get('speed_mhz')}MHz keeps multitasking fluid."
        ),
        "storage": (
            f"{priority} for {uc} — {s.get('size_gb')}GB "
            f"{str(s.get('type', 'nvme')).upper()} at "
            f"{s.get('read_speed_mbs')} MB/s read speed minimises load times."
        ),
        "motherboard": (
            f"Reliable {s.get('form_factor')} board with {s.get('socket')} socket "
            f"and {s.get('chipset')} chipset — solid foundation for this build."
        ),
        "psu": (
            f"{s.get('wattage')}W "
            f"{str(s.get('efficiency_rating', '80+')).upper()} PSU provides "
            "stable power with headroom for upgrades."
        ),
        "case": (
            f"{s.get('form_factor')} case with {s.get('max_gpu_length_mm')}mm "
            "GPU clearance — good airflow and cable management."
        ),
        "cooler": (
            f"{'Quiet ' if s.get('is_quiet') else ''}"
            f"{str(s.get('type', 'air')).upper()} cooler rated for "
            f"{s.get('tdp_rating_watts')}W TDP keeps the CPU cool"
            f"{' and silent' if s.get('is_quiet') else ''}."
        ),
    }
    return templates.get(category, f"Best value {category} for this build.")


def run_optimizer(
    parts_by_cat: dict,
    budget: int,
    use_case: str,
    future_proofing: bool,
    owns_gpu: bool,
    prefer_quiet_cooling: bool,
) -> dict:
    weights = dict(WEIGHTS[use_case])
    active = list(weights.keys())

    # owns_gpu: remove GPU, redistribute its weight proportionally
    if owns_gpu and "gpu" in active:
        gpu_w = weights.pop("gpu")
        active.remove("gpu")
        remaining_w = sum(weights.values())
        for cat in active:
            weights[cat] += gpu_w * (weights[cat] / remaining_w)

    perf = _perf_scores({cat: parts_by_cat.get(cat, []) for cat in active})

    # future_proofing: boost perf scores of top-quartile parts
    if future_proofing:
        for cat in active:
            cat_parts = parts_by_cat.get(cat, [])
            if not cat_parts:
                continue
            prices = sorted(p.price for p in cat_parts)
            p75 = prices[int(len(prices) * 0.75)]
            for p in cat_parts:
                if p.price >= p75:
                    perf[p.id] = perf.get(p.id, 0.5) * 1.3

    target = {cat: budget * w for cat, w in weights.items()}
    selected: dict[str, Part] = {}

    for cat in active:
        parts = parts_by_cat.get(cat, [])
        if not parts:
            continue
        if cat == "cooler" and prefer_quiet_cooling:
            quiet = [p for p in parts if p.specs.get("is_quiet")]
            pool = quiet if quiet else parts
        else:
            pool = parts
        affordable = [p for p in pool if p.price <= target[cat]]
        selected[cat] = (
            max(affordable, key=lambda p: perf.get(p.id, 0))
            if affordable
            else min(pool, key=lambda p: p.price)
        )

    # Budget correction: if cheapest parts exceed budget, downgrade costliest
    total = sum(p.price for p in selected.values())
    for _ in range(50):
        if total <= budget:
            break
        worst = max(active, key=lambda c: selected[c].price if c in selected else 0)
        pool = parts_by_cat.get(worst, [])
        cheaper = sorted(
            [p for p in pool if p.price < selected[worst].price],
            key=lambda p: p.price,
            reverse=True,
        )
        if not cheaper:
            break
        total -= selected[worst].price - cheaper[0].price
        selected[worst] = cheaper[0]

    # Greedy upgrade pass: spend leftover budget on best incremental upgrades
    remaining = budget - sum(p.price for p in selected.values())
    improved = True
    while improved:
        improved = False
        best: tuple | None = None
        best_cost = float("inf")
        for cat in active:
            if cat not in selected:
                continue
            if cat == "cooler" and prefer_quiet_cooling:
                quiet = [p for p in parts_by_cat.get(cat, []) if p.specs.get("is_quiet")]
                pool = quiet if quiet else parts_by_cat.get(cat, [])
            else:
                pool = parts_by_cat.get(cat, [])
            upgrades = [
                p for p in pool
                if p.price > selected[cat].price
                and (p.price - selected[cat].price) <= remaining
            ]
            if upgrades:
                upgrade = min(upgrades, key=lambda p: p.price - selected[cat].price)
                cost = upgrade.price - selected[cat].price
                if cost < best_cost:
                    best_cost = cost
                    best = (cat, upgrade)
        if best:
            cat, new_part = best
            remaining -= new_part.price - selected[cat].price
            selected[cat] = new_part
            improved = True

    components = [
        {
            "category": cat,
            "name": part.name,
            "brand": part.brand,
            "price": part.price,
            "reason": _generate_reason(cat, part, use_case, weights[cat]),
            "specs": part.specs,
        }
        for cat, part in selected.items()
    ]

    return {
        "use_case": use_case,
        "budget": budget,
        "total_price": round(sum(p.price for p in selected.values()), 2),
        "components": components,
    }


@router.post("", response_model=OptimizeResponse)
def optimize(body: OptimizeRequest, db: Session = Depends(get_db)):
    all_parts = db.query(Part).all()
    by_cat: dict[str, list[Part]] = {}
    for p in all_parts:
        by_cat.setdefault(p.category, []).append(p)

    return run_optimizer(
        parts_by_cat=by_cat,
        budget=body.budget,
        use_case=body.use_case,
        future_proofing=body.future_proofing,
        owns_gpu=body.owns_gpu,
        prefer_quiet_cooling=body.prefer_quiet_cooling,
    )
```

- [ ] **Step 4: Add optimizer router to `main.py`**

Ensure `main.py` includes:
```python
from routers import optimizer as optimizer_router
app.include_router(optimizer_router.router)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_optimizer.py -v
```

Expected: 8 tests pass.

- [ ] **Step 6: Commit**

```bash
git add backend/routers/optimizer.py backend/tests/test_optimizer.py
git commit -m "feat: add weighted greedy optimizer engine and /optimize endpoint"
```

---

## Task 10: Parts Seed Data

**Files:**
- Create: `backend/seed.py`

- [ ] **Step 1: Write `backend/seed.py`**

```python
"""
Run from backend/ with the venv active:
    python seed.py
Requires DATABASE_URL in .env or environment.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import models  # noqa: F401 — registers all models with Base
from db.database import Base, engine, SessionLocal
from models.part import Part

PARTS = [
    # ── CPU (8) ──────────────────────────────────────────────────────────────
    {"category": "cpu", "name": "AMD Ryzen 5 5600", "brand": "AMD", "price": 129.0,
     "specs": {"cores": 6, "base_clock_ghz": 3.5, "tdp_watts": 65, "architecture": "Zen 3"}},
    {"category": "cpu", "name": "AMD Ryzen 5 7600X", "brand": "AMD", "price": 229.0,
     "specs": {"cores": 6, "base_clock_ghz": 4.7, "tdp_watts": 105, "architecture": "Zen 4"}},
    {"category": "cpu", "name": "Intel Core i5-13600K", "brand": "Intel", "price": 269.0,
     "specs": {"cores": 14, "base_clock_ghz": 3.5, "tdp_watts": 125, "architecture": "Raptor Lake"}},
    {"category": "cpu", "name": "AMD Ryzen 7 7700X", "brand": "AMD", "price": 299.0,
     "specs": {"cores": 8, "base_clock_ghz": 4.5, "tdp_watts": 105, "architecture": "Zen 4"}},
    {"category": "cpu", "name": "Intel Core i7-13700K", "brand": "Intel", "price": 379.0,
     "specs": {"cores": 16, "base_clock_ghz": 3.4, "tdp_watts": 125, "architecture": "Raptor Lake"}},
    {"category": "cpu", "name": "AMD Ryzen 9 7900X", "brand": "AMD", "price": 429.0,
     "specs": {"cores": 12, "base_clock_ghz": 4.7, "tdp_watts": 170, "architecture": "Zen 4"}},
    {"category": "cpu", "name": "Intel Core i9-13900K", "brand": "Intel", "price": 549.0,
     "specs": {"cores": 24, "base_clock_ghz": 3.0, "tdp_watts": 125, "architecture": "Raptor Lake"}},
    {"category": "cpu", "name": "AMD Ryzen 9 7950X", "brand": "AMD", "price": 699.0,
     "specs": {"cores": 16, "base_clock_ghz": 4.5, "tdp_watts": 170, "architecture": "Zen 4"}},

    # ── GPU (8) ──────────────────────────────────────────────────────────────
    {"category": "gpu", "name": "AMD Radeon RX 6600", "brand": "AMD", "price": 199.0,
     "specs": {"vram_gb": 8, "tdp_watts": 132, "benchmark_score": 45, "tier": "budget"}},
    {"category": "gpu", "name": "NVIDIA GeForce RTX 3060", "brand": "NVIDIA", "price": 249.0,
     "specs": {"vram_gb": 12, "tdp_watts": 170, "benchmark_score": 55, "tier": "budget"}},
    {"category": "gpu", "name": "AMD Radeon RX 6700 XT", "brand": "AMD", "price": 299.0,
     "specs": {"vram_gb": 12, "tdp_watts": 230, "benchmark_score": 63, "tier": "mid"}},
    {"category": "gpu", "name": "NVIDIA GeForce RTX 4060", "brand": "NVIDIA", "price": 299.0,
     "specs": {"vram_gb": 8, "tdp_watts": 115, "benchmark_score": 65, "tier": "mid"}},
    {"category": "gpu", "name": "NVIDIA RTX 4070 SUPER", "brand": "NVIDIA", "price": 599.0,
     "specs": {"vram_gb": 12, "tdp_watts": 220, "benchmark_score": 82, "tier": "high"}},
    {"category": "gpu", "name": "AMD Radeon RX 7900 XT", "brand": "AMD", "price": 749.0,
     "specs": {"vram_gb": 20, "tdp_watts": 315, "benchmark_score": 88, "tier": "high"}},
    {"category": "gpu", "name": "NVIDIA RTX 4080 SUPER", "brand": "NVIDIA", "price": 999.0,
     "specs": {"vram_gb": 16, "tdp_watts": 320, "benchmark_score": 93, "tier": "flagship"}},
    {"category": "gpu", "name": "NVIDIA RTX 4090", "brand": "NVIDIA", "price": 1599.0,
     "specs": {"vram_gb": 24, "tdp_watts": 450, "benchmark_score": 100, "tier": "flagship"}},

    # ── RAM (6) ──────────────────────────────────────────────────────────────
    {"category": "ram", "name": "16GB Corsair Vengeance DDR4 3200", "brand": "Corsair", "price": 44.0,
     "specs": {"size_gb": 16, "speed_mhz": 3200}},
    {"category": "ram", "name": "32GB G.Skill Ripjaws DDR4 3600", "brand": "G.Skill", "price": 72.0,
     "specs": {"size_gb": 32, "speed_mhz": 3600}},
    {"category": "ram", "name": "32GB Corsair Vengeance DDR5 5200", "brand": "Corsair", "price": 89.0,
     "specs": {"size_gb": 32, "speed_mhz": 5200}},
    {"category": "ram", "name": "32GB G.Skill Trident Z5 DDR5 6000", "brand": "G.Skill", "price": 109.0,
     "specs": {"size_gb": 32, "speed_mhz": 6000}},
    {"category": "ram", "name": "64GB Corsair Dominator DDR5 5600", "brand": "Corsair", "price": 169.0,
     "specs": {"size_gb": 64, "speed_mhz": 5600}},
    {"category": "ram", "name": "64GB G.Skill Trident Z5 DDR5 6400", "brand": "G.Skill", "price": 219.0,
     "specs": {"size_gb": 64, "speed_mhz": 6400}},

    # ── Storage (6) ──────────────────────────────────────────────────────────
    {"category": "storage", "name": "500GB Samsung 870 EVO SATA", "brand": "Samsung", "price": 49.0,
     "specs": {"size_gb": 500, "read_speed_mbs": 560, "type": "sata"}},
    {"category": "storage", "name": "1TB Crucial MX500 SATA", "brand": "Crucial", "price": 69.0,
     "specs": {"size_gb": 1000, "read_speed_mbs": 560, "type": "sata"}},
    {"category": "storage", "name": "1TB Samsung 980 NVMe Gen3", "brand": "Samsung", "price": 79.0,
     "specs": {"size_gb": 1000, "read_speed_mbs": 3500, "type": "nvme"}},
    {"category": "storage", "name": "1TB WD Black SN850X NVMe Gen4", "brand": "WD", "price": 89.0,
     "specs": {"size_gb": 1000, "read_speed_mbs": 7300, "type": "nvme"}},
    {"category": "storage", "name": "2TB Samsung 990 Pro NVMe Gen4", "brand": "Samsung", "price": 149.0,
     "specs": {"size_gb": 2000, "read_speed_mbs": 7450, "type": "nvme"}},
    {"category": "storage", "name": "2TB WD Black SN850X NVMe Gen4", "brand": "WD", "price": 179.0,
     "specs": {"size_gb": 2000, "read_speed_mbs": 7300, "type": "nvme"}},

    # ── Motherboard (6) ──────────────────────────────────────────────────────
    {"category": "motherboard", "name": "MSI B450 Tomahawk Max II", "brand": "MSI", "price": 89.0,
     "specs": {"socket": "AM4", "form_factor": "ATX", "chipset": "B450"}},
    {"category": "motherboard", "name": "ASUS Prime B650M-A WiFi", "brand": "ASUS", "price": 139.0,
     "specs": {"socket": "AM5", "form_factor": "Micro-ATX", "chipset": "B650"}},
    {"category": "motherboard", "name": "MSI B650 Tomahawk WiFi", "brand": "MSI", "price": 189.0,
     "specs": {"socket": "AM5", "form_factor": "ATX", "chipset": "B650"}},
    {"category": "motherboard", "name": "ASUS ROG Strix B650-A Gaming", "brand": "ASUS", "price": 239.0,
     "specs": {"socket": "AM5", "form_factor": "ATX", "chipset": "B650"}},
    {"category": "motherboard", "name": "MSI MEG X670E ACE", "brand": "MSI", "price": 349.0,
     "specs": {"socket": "AM5", "form_factor": "ATX", "chipset": "X670E"}},
    {"category": "motherboard", "name": "ASUS ROG Crosshair X670E Hero", "brand": "ASUS", "price": 499.0,
     "specs": {"socket": "AM5", "form_factor": "ATX", "chipset": "X670E"}},

    # ── PSU (6) ──────────────────────────────────────────────────────────────
    {"category": "psu", "name": "EVGA 550W B5 80+ Bronze", "brand": "EVGA", "price": 59.0,
     "specs": {"wattage": 550, "efficiency_rating": "bronze"}},
    {"category": "psu", "name": "Corsair CV650 80+ Bronze", "brand": "Corsair", "price": 69.0,
     "specs": {"wattage": 650, "efficiency_rating": "bronze"}},
    {"category": "psu", "name": "Corsair RM750x 80+ Gold", "brand": "Corsair", "price": 99.0,
     "specs": {"wattage": 750, "efficiency_rating": "gold"}},
    {"category": "psu", "name": "Seasonic Focus GX-850 80+ Gold", "brand": "Seasonic", "price": 129.0,
     "specs": {"wattage": 850, "efficiency_rating": "gold"}},
    {"category": "psu", "name": "Corsair RM1000x 80+ Gold", "brand": "Corsair", "price": 169.0,
     "specs": {"wattage": 1000, "efficiency_rating": "gold"}},
    {"category": "psu", "name": "Seasonic Prime TX-1000 80+ Titanium", "brand": "Seasonic", "price": 239.0,
     "specs": {"wattage": 1000, "efficiency_rating": "platinum"}},

    # ── Case (6) ─────────────────────────────────────────────────────────────
    {"category": "case", "name": "Fractal Design Core 1000", "brand": "Fractal", "price": 49.0,
     "specs": {"form_factor": "Micro-ATX", "max_gpu_length_mm": 310}},
    {"category": "case", "name": "NZXT H5 Flow", "brand": "NZXT", "price": 79.0,
     "specs": {"form_factor": "ATX", "max_gpu_length_mm": 365}},
    {"category": "case", "name": "Fractal Design Meshify C", "brand": "Fractal", "price": 89.0,
     "specs": {"form_factor": "ATX", "max_gpu_length_mm": 315}},
    {"category": "case", "name": "Lian Li Lancool 216", "brand": "Lian Li", "price": 109.0,
     "specs": {"form_factor": "ATX", "max_gpu_length_mm": 400}},
    {"category": "case", "name": "Fractal Design North", "brand": "Fractal", "price": 139.0,
     "specs": {"form_factor": "ATX", "max_gpu_length_mm": 355}},
    {"category": "case", "name": "Lian Li O11 Dynamic EVO XL", "brand": "Lian Li", "price": 179.0,
     "specs": {"form_factor": "Full Tower", "max_gpu_length_mm": 446}},

    # ── Cooler (6) ───────────────────────────────────────────────────────────
    {"category": "cooler", "name": "Cooler Master Hyper 212", "brand": "Cooler Master", "price": 29.0,
     "specs": {"type": "air", "tdp_rating_watts": 150, "noise_db": 36, "is_quiet": False}},
    {"category": "cooler", "name": "Thermalright Peerless Assassin 120", "brand": "Thermalright", "price": 39.0,
     "specs": {"type": "air", "tdp_rating_watts": 250, "noise_db": 26, "is_quiet": True}},
    {"category": "cooler", "name": "be quiet! Dark Rock 4", "brand": "be quiet!", "price": 69.0,
     "specs": {"type": "air", "tdp_rating_watts": 200, "noise_db": 24, "is_quiet": True}},
    {"category": "cooler", "name": "NZXT Kraken 240 AIO", "brand": "NZXT", "price": 89.0,
     "specs": {"type": "aio", "tdp_rating_watts": 250, "noise_db": 33, "is_quiet": False}},
    {"category": "cooler", "name": "Corsair iCUE H150i Elite 360 AIO", "brand": "Corsair", "price": 159.0,
     "specs": {"type": "aio", "tdp_rating_watts": 350, "noise_db": 28, "is_quiet": True}},
    {"category": "cooler", "name": "NZXT Kraken 360 Elite AIO", "brand": "NZXT", "price": 229.0,
     "specs": {"type": "aio", "tdp_rating_watts": 400, "noise_db": 21, "is_quiet": True}},
]


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Part).count() > 0:
            print("Parts table already seeded — skipping.")
            return
        for row in PARTS:
            db.add(Part(**row))
        db.commit()
        print(f"Seeded {len(PARTS)} parts successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
```

- [ ] **Step 2: Commit**

```bash
git add backend/seed.py
git commit -m "feat: add parts seed data — 50 real-world parts across 8 categories"
```

---

## Task 11: App Entry Point and Final Wiring

**Files:**
- Create: `backend/main.py`
- Modify: `backend/routers/__init__.py`

> **Note:** A stub `main.py` should have been created before Task 7 to allow tests to run. This task writes the final complete version.

- [ ] **Step 1: Write the stub `main.py` (do this before Task 7 if not done yet)**

Create this minimal version so conftest can import `app`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="BuildOptima API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

- [ ] **Step 2: Write the final `backend/main.py`**

Replace the stub with the complete version:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import models  # noqa: F401 — registers all ORM models with Base
from db.database import Base, engine
from routers import auth, builds, optimizer

Base.metadata.create_all(bind=engine)

app = FastAPI(title="BuildOptima API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(builds.router)
app.include_router(optimizer.router)


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 3: Run the full test suite**

```bash
pytest -v
```

Expected: all tests pass (auth, builds, optimizer, security).

- [ ] **Step 4: Verify the app starts (requires `.env` with a real PostgreSQL DATABASE_URL)**

```bash
uvicorn main:app --reload
```

Open `http://localhost:8000/health` → `{"status": "ok"}`
Open `http://localhost:8000/docs` → Swagger UI shows all routes.

- [ ] **Step 5: Seed the database**

```bash
python seed.py
```

Expected: `Seeded 50 parts successfully.`

- [ ] **Step 6: Smoke-test the optimizer end-to-end**

```bash
curl -s -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{"budget": 1500, "use_case": "gaming"}' | python -m json.tool
```

Expected: JSON response with `components` array of 8 parts, `total_price <= 1500`.

- [ ] **Step 7: Final commit**

```bash
git add backend/main.py backend/routers/__init__.py
git commit -m "feat: wire all routers into main FastAPI app — backend complete"
```
