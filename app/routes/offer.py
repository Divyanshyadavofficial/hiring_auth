from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.models_db.offer import Offer
from app.models_db.application import Application
from app.models_db.job import Job
from sqlalchemy import select
from app.models.offer import (
    OfferCreateRequest,
    OfferResponse
)
from datetime import datetime
from app.utils.dependencies import require_roles

offer_router = APIRouter(
    prefix="/offers",
    tags=["offers"]
)

@offer_router.post(
    "/applications/{application_id}",
    response_model=OfferResponse
)
async def create_offer(
    application_id: int,
    payload: OfferCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(
        require_roles(["admin","recruiter"])
    )
):
    try: 
        application = await db.get(
            Application,
            application_id
        )

        if not application:
            raise HTTPException(
                status_code=404,
                detail="Application not found"
            )
        
        job = await db.get(
            Job,
            application.job_id
        )
        if not job:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )
        if(
            current_user["role"]!="admin" and job.created_by!=current_user["user_id"]

        ):
            raise HTTPException(
                status_code=403,
                detail="Not allowed"
            )
        
        if application.shortlist_status!="hired":
            raise HTTPException(
                status_code=400,
                detail="Candidate is not hired"
            )
        
        existing = await db.execute(
            select(Offer).where(
                Offer.application_id == application_id
            )
        )

        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="offer already exists"
            )
        
        offer = Offer(
                application_id = application_id,
                salary = payload.salary,
                joining_date = payload.joining_date,
                offer_letter_url=payload.offer_letter_url,
                status="pending"
        )
        db.add(offer)
        await db.commit()
        await db.refresh(offer)
        return offer
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"failed to create offer: "
            f"{str(e)}"
        )
    



@offer_router.get(
    "/{offer_id}",
    response_model=OfferResponse
)
async def get_offer(
    offer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(
        require_roles(
            ["admin","recruiter","candidate"]
        )
    )
):
    try: 
        offer = await db.get(
            Offer,
            offer_id
        )
        if not offer:
            raise HTTPException(
                status_code=404,
                detail="offer not found"
            )
        
        application = await db.get(
            Application,
            offer.application_id
        )
        if not application: 
            raise HTTPException(
                status_code=404,
                detail="Application not found"
            )
        
        job = await db.get(
            Job,
            application.job_id
        )

        if current_user["role"] == "candidate":
            if (
                application.user_id
                != current_user["user_id"]

            ):
                raise HTTPException(
                    status_code=403,
                    detail="Not allowed"
                )
        elif current_user["role"] == "recruiter":
            if (
                job.created_by
                != current_user["user_id"]
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Not allowed"
                )
        return offer
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(
                f"failed to fetch offer: "
                f"{str(e)}"
            )
        )


@offer_router.patch("/{offer_id}/accept")
async def accept_offer(
    offer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user= Depends(
        require_roles(["candidate"])
    )
):
    try:
        offer = await db.get(
            Offer,
            offer_id
        )
        if not offer:
            raise HTTPException(
                status_code=404,
                detail="Offer not found"
            )
        application = await db.get(
            Application,
            offer.application_id
        )

        if application.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=403,
                detail="Not allowed"
            )
        if offer.status != "pending":
            raise HTTPException(
                status_code=400,
                detail=f"Offer already {offer.status}"
            )
        offer.status = "accepted"
        offer.accepted_at = datetime.utcnow()
        await db.commit()
        return {
            "message":
                "offer accepted"
        }
    except HTTPException as e:
        raise
    except Exception as e:
        await db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"failed to accept offer: "
            f"{str(e)}"
        )
    

@offer_router.patch(
    "/{offer_id}/decline"
)
async def decline_offer(
    offer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(
        require_roles(["candidate"])
    )

):
    try: 
        offer = await db.get(
            Offer,
            offer_id
        )
        if not offer:
            raise HTTPException(
                status_code=404,
                detail="Offer not found"
            )
        application = await db.get(
            Application,
            offer.application_id
        )

        if application.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=403,
                detail="Not allowed"
            )
        if offer.status != "pending":
            raise HTTPException(
                status_code=400,
                detail=f"Offer already {offer.status}"
            )

        offer.status = "declined"
        offer.declined_at = datetime.utcnow()

        await db.commit()

        return {
            "message":
                "Offer declined"
        }
    except HTTPException as e:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"failed to decline offer: "
            f"{str(e)}"
        )


@offer_router.get("/my-offers")
async def get_my_offers(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(
        require_roles(["candidate"])
    )
):
    try:
        result = await db.execute(
            select(
                Offer,
                Application,
                Job
            )
            .join(
                Application,
                Offer.application_id ==
                Application.id
            )
            .join(
                Job,
                Application.job_id ==
                Job.id
            )
            .where(
                Application.user_id ==
                current_user["user_id"]
            )
            .order_by(
                Offer.created_at.desc()
            )
        )

        rows = result.all()

        return [
            {
                "offer_id": offer.id,
                "job_id": job.id,
                "job_title": job.title,
                "salary": offer.salary,
                "joining_date": offer.joining_date,
                "status": offer.status
            }
            for offer, app, job in rows
        ]

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch offers: {str(e)}"
        )
    

@offer_router.patch(
    "/{offer_id}/withdraw"
)
async def withdraw_offer(
    offer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(
        require_roles(["admin","recruiter"])
    )
):
    try:
        offer = await db.get(
            Offer,
            offer_id
        )

        if not offer:
            raise HTTPException(
                status_code=404,
                detail="Offer not found"
            )

        application = await db.get(
            Application,
            offer.application_id
        )

        job = await db.get(
            Job,
            application.job_id
        )

        if (
            current_user["role"] != "admin"
            and job.created_by != current_user["user_id"]
        ):
            raise HTTPException(
                status_code=403,
                detail="Not allowed"
            )

        if offer.status in [
            "accepted",
            "declined"
        ]:
            raise HTTPException(
                status_code=400,
                detail="Offer already finalized"
            )

        offer.status = "withdrawn"

        await db.commit()

        return {
            "message":
                "Offer withdrawn successfully"
        }

    except HTTPException:
        raise

    except Exception as e:
        await db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to withdraw offer: "
                f"{str(e)}"
            )
        )