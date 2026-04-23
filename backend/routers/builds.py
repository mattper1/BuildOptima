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
