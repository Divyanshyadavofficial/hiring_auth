from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db import get_db

from app.models_db.application import Application
from app.models_db.job import Job
from app.models_db.offer import Offer
from app.models_db.user import User

from app.utils.dependencies import require_roles

from app.models.applications import (
    ApplicationResponse,
    ApplicationStatusUpdate,
    CandidateDashboardResponse,
    HiringDecisionRequest

)
from app.models_db.candidate_attempt import CandidateAttempt
from app.services.notification_service import create_notification
from app.models.applications import ShortlistRequest

from app.models.interview import InterviewCreateRequest,InterviewResposnse
from app.models_db.interview import Interview, InterviewFeedback
from datetime import datetime,timezone

applications_router = APIRouter(
    prefix="/applications",
    tags=["Applications"]
)

VALID_STATUS = ["pending", "accepted", "rejected"]


# ==================================================
# Candidate Dashboard
# ==================================================

@applications_router.get(
    "/dashboard",
    response_model=CandidateDashboardResponse
)
async def dashboard(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(["candidate"]))
):
    result = await db.execute(
        select(
            func.count().label("total"),

            func.count()
            .filter(Application.status == "pending")
            .label("pending"),

            func.count()
            .filter(Application.status == "accepted")
            .label("accepted"),

            func.count()
            .filter(Application.status == "rejected")
            .label("rejected")

        ).where(
            Application.user_id == current_user["user_id"]
        )
    )

    stats = result.one()

    return {
        "total": stats.total,
        "pending": stats.pending,
        "accepted": stats.accepted,
        "rejected": stats.rejected
    }


# ==================================================
# Candidate View Own Applications
# ==================================================

@applications_router.get("/me")
async def get_my_applications(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(["candidate"]))
):
    result = await db.execute(
        select(Application, Job)
        .join(Job, Application.job_id == Job.id)
        .where(
            Application.user_id == current_user["user_id"]
        )
    )

    return [
        {
            "application_id": app.id,
            "job_title": job.title,
            "status": app.status,
            "shortlist_status":app.shortlist_status
        }
        for app, job in result.all()
    ]


# ==================================================
# Recruiter/Admin Update Application Status
# ==================================================

@applications_router.patch(
    "/{application_id}",
    response_model=ApplicationResponse
)
async def update_application_status(
    application_id: int,
    data: ApplicationStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(["admin", "recruiter"]))
):
    application = await db.get(
        Application,
        application_id
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found"
        )

    if data.status not in VALID_STATUS:
        raise HTTPException(
            status_code=400,
            detail="Invalid status"
        )

    job = await db.get(Job, application.job_id)

    if (
        current_user["role"] != "admin"
        and job.created_by != current_user["user_id"]
    ):
        raise HTTPException(
            status_code=403,
            detail="Not allowed"
        )

    application.status = data.status

    await db.commit()
    await db.refresh(application)
    if data.status =="rejected":
        await create_notification(
            db=db,
            user_id=application.user_id,
            title="Application Rejected",
            message=f"Your application for {job.title} was rejected",
            event_type= "APPLICATION REJECTED"
        )
    elif data.status=="accepted":
        await create_notification(
            db=db,
            user_id=application.user_id,
            title="Application Accepted",
            message=f"Your application for {job.title} has moved to the next stage.",
            event_type="APPLICATION_ACCEPTED"

        )
    

    return application


@applications_router.patch(
        "/{application_id}/shortlist"
)
async def shortlist_candidate(
    application_id: int,
    data:ShortlistRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(
        require_roles(["admin","recruiter"])
    )

):
    application = await db.get(
        Application,application_id
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
            detail= "Job not found"
        )
    if(current_user["role"]!="admin"and 
       job.created_by!=current_user["user_id"]):
        raise HTTPException(
            status_code=403,
            detail="Not allowed"
        )
    application.shortlist_status = data.status
    application.recruiter_notes = data.notes
    if data.status == "shortlisted":
        application.shortlisted_at = datetime.utcnow()
    elif data.status == "interview":
        application.interview_started_at = datetime.utcnow()
    elif data.status == "rejected":
        application.rejected_at = datetime.utcnow()

    await db.commit()
    await db.refresh(application)
    if data.status=="shortlisted":
        await create_notification(
            db=db,
            user_id=application.user_id,
            title="Application shortlisted",
            message=f"Your application for {job.title} has been shortlisted for the next stage.",
            event_type="SHORTLISTED"

        )
    elif data.status == "interview":
        await create_notification(
            db=db,
            user_id=application.user_id,
            title="Interview Stage",
            message=f"Your application for {job.title} has moved to the interview stage.",
            event_type="INTERVIEW_SCHEDULED"

        )

    elif data.status == "rejected":
        await create_notification(
            db=db,
            user_id=application.user_id,
            title="Application Rejected",
            message=f"Your application for {job.title} was rejected.",
            event_type="APPLICATION_REJECTED"
        )

    return{
        "message":

            "Candidate shortlist status updated",

        "application_id":

            application.id,

        "candidate_id":

            application.user_id,

        "shortlist_status":

            application.shortlist_status,

        "recruiter_notes":

            application.recruiter_notes
    }

# ==================================================
# Admin View All Applications
# ==================================================

@applications_router.get("/")
async def get_all_applications(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(["admin"]))
):
    result = await db.execute(
        select(Application, User, Job)
        .join(User, Application.user_id == User.id)
        .join(Job, Application.job_id == Job.id)
    )

    return [
        {
            "application_id": app.id,
            "candidate": user.name,
            "job": job.title,
            "status": app.status
        }
        for app, user, job in result.all()
    ]

@applications_router.post("/{application_id}/interviews",response_model=InterviewResposnse
)
async def schedule_interview(
    application_id:int,
    payload: InterviewCreateRequest,
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
                detail="application not found"
            )
    
        job = await db.get(
            Job,
            application.job_id
        )

        if not job: 
            raise HTTPException(
                status_code=404,
                detail= "job not found"
            )
    
        if(
            current_user["role"]!="admin" and job.created_by!=current_user["user_id"]
        ):
            raise HTTPException(
                status_code=403,
                detail="Not allowed"
            )
    
        if application.shortlist_status not in [
            "shortlisted",
            "interview"
        ]:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Candidate must be shortlisted "
                    "before scheduling interview"
                )
            )
        
        if application.status =="rejected":
            raise HTTPException(
                status_code=400,
                detail="Cannot schedule interview for " \
                "rejected candidates"
            )
        

        
        existing_result = await db.execute(

            select(Interview).where(

                Interview.application_id == application.id,

             Interview.round_number == payload.round_number

            )

        )
        existing_interview = (
            existing_result.scalar_one_or_none()
        )

        if existing_interview:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Round {payload.round_number} "
                    "already exists"
                )
            )
        interviewer = await db.get(
            User,
            payload.interviewer_id
        )

        if not interviewer:
            raise HTTPException(
                status_code=404,
                detail="Interviewer not found"
            )
    
        if interviewer.role not in ["recruiter","admin"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid interviewer"
            )
        if payload.scheduled_at < datetime.now(timezone.utc):

            raise HTTPException(

                status_code=400,

                detail="Interview time must be in future"

            )

        interview = Interview(
            application_id=application.id,
            interviewer_id = payload.interviewer_id,
            round_number=payload.round_number,
            scheduled_at = payload.scheduled_at,
            meeting_link=payload.meeting_link,
            status="scheduled"
        )


        db.add(interview)
        application.status = "accepted"
        application.shortlist_status = "interview"
        await db.commit()
        await db.refresh(interview)
        await create_notification(
            db=db,
            user_id=application.user_id,
            event_type="INTERVIEW_SCHEDULED",
            message=(
                f"Interview Round "
                f"{payload.round_number} scheduled"
            )
        )
        return interview
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to schedule interview: {str(e)}"
        )
    
@applications_router.patch("/{application_id}/hire")
async def hiring_decision(
    application_id:int,
    payload: HiringDecisionRequest,
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
            current_user["role"]!="admin"and 
            job.created_by!=current_user["user_id"]
        ):
            raise HTTPException(
                status_code=403,
                detail="Not allowed"
            )
        if application.shortlist_status !="interview":
            raise HTTPException(
                status_code=400,
                detail=(
                    "Candidate has not completed "
                    "interview process"
                )
            )
        if payload.decision =="hired":
            application.status = "accepted"
            application.shortlist_status = "hired"
            application.hired_at = datetime.utcnow()
        else: 
            application.status = "rejected"
            application.shortlist_status = "rejected"
            application.rejected_at = datetime.utcnow()
        application.recruiter_notes = (
            payload.notes
        )
        await db.commit()
        await db.refresh(
            application
        )
        await create_notification(
            db=db,
            user_id=application.user_id,
            event_type="HIRED",
            message=(
                f"Congratulations! "
                f"You have been selected for "
                f"{job.title}"
            )
        )

        return {
            "message":
                "Hiring decision updated",
            "application_id":
                application.id,
            "candidate_id":
                application.user_id,
            "decision":
                payload.decision,
            "status":
                application.status
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to update decision: "
                f"{str(e)}"
            )

        )

@applications_router.get("/{application_id}/timeline")
async def get_timeline(
    application_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(["candidate"]))
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
        if application.user_id!=current_user["user_id"]:
            raise HTTPException(
                status_code=403,
                detail="Not allowed"
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
        timeline = []
        timeline.append({
            "event": "APPLICATION_APPLIED",
            "status":"completed",
            "timestamp":application.created_at
        })
        if application.shortlisted_at: 
            timeline.append({
                "event":"SHORTLISTED",
                "status":"completed",
                "timestamp": application.shortlisted_at
            })
        
        if application.interview_started_at:

            timeline.append({

                "event": "INTERVIEW_STARTED",

                "status": "completed",

                "timestamp": application.interview_started_at
            })

        if application.hired_at:

            timeline.append({

                "event": "HIRED",

                "status": "completed",

                "timestamp": application.hired_at

            })

        if application.rejected_at:

            timeline.append({

                "event": "REJECTED",

                "status": "completed",

                "timestamp": application.rejected_at

            })
        
        attempt_result = await db.execute(
            select(CandidateAttempt)
            .where(
                CandidateAttempt.application_id ==application.id,
                CandidateAttempt.status == "completed"
            )
        )
        attempt = attempt_result.scalar_one_or_none()
        if attempt:
            timeline.append({
                "event":"ASSESSMENT_COMPLETED",
                "status":"completed",
                "timestamp":attempt.completed_at,
                "percentage":attempt.percentage,
                "passed":attempt.passed
            })

        interview_result = await db.execute(
            select(Interview)
            .where(
                Interview.application_id == application.id
            )
        )
        interview = interview_result.scalar_one_or_none()

        if interview:
            timeline.append({
                "event":"INTERVIEW_SCHEDULED",
                "status": "completed",
                "timestamp":interview.scheduled_at
            })

            feedback_result = await db.execute(
                select(InterviewFeedback)
                .where(
                InterviewFeedback.interview_id == interview.id
                )
            )
            feedback = feedback_result.scalar_one_or_none()
            if feedback:
                timeline.append({
                    "event": "INTERVIEW_COMPLETED",
                    "status": "completed",
                    "timestamp": feedback.created_at
                })

        
        offer_result = await db.execute(
            select(Offer)
            .where(
            Offer.application_id == application.id  
            )
        )
        offer = offer_result.scalar_one_or_none()
        if offer:
            timeline.append({
                "event":"OFFER_CREATED",
                "status":"completed",
                "timestamp":offer.created_at
            })
        
            if offer.accepted_at:
                timeline.append({
                    "event": "OFFER_ACCEPTED",
                    "status": "completed",
                    "timestamp": offer.accepted_at
                })
            elif offer.declined_at:
                timeline.append({
                    "event": "OFFER_DECLINED",
                    "status": "completed",
                    "timestamp": offer.declined_at
                })
            elif offer.withdrawn_at:
                timeline.append({
                    "event": "OFFER_WITHDRAWN",
                    "status": "completed",
                    "timestamp": offer.withdrawn_at
                })
        timeline.sort(
            key=lambda item: item["timestamp"]
        )

        return {
            "application_id": application.id,
            "job_id": job.id,
            "job_title": job.title,
            "application_status": application.status,
            "shortlist_status": application.shortlist_status,
            "timeline": timeline
        }     
        
    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"failed to get timeline: "
            f"{str(e)}"
        )