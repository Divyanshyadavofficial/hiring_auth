from fastapi import APIRouter,Depends,HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select,func
from app.db import get_db
from app.models_db.job import Job
from app.models_db.job_skill import JobSkill
from app.models_db.user import User
from app.models_db.application import Application
from app.models.job import   JobCreate,JobResponse,JobCreateResponse,ApplyJobResponse,JobApplicationResponse,SkillReviewRequest,JobDashboardResponse
from app.models_db.AssessmentBlueprint import Assessment
from app.models_db.candidate_attempt import CandidateAttempt
from app.utils.dependencies import require_roles

from app.services.embedding_service import generate_embedding

from app.services.skill_extractor import extract_skills 

from app.services.matching_service import calculate_match_score

from app.vector_db.chroma_client import get_job_collection

from app.models_db.interview import (
    Interview,
    InterviewFeedback
)
from app.models_db.candidate_attempt import CandidateAttempt
from app.models_db.AssessmentBlueprint import Assessment
from app.models_db.offer import Offer

jobs_router = APIRouter( prefix="/jobs",tags=["Jobs"])


@jobs_router.post("/",response_model=JobCreateResponse)

async def create_job(
    job: JobCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(
        require_roles(
            ["recruiter", "admin"]
        )
    )
):
    try:
        skills = extract_skills(
            job.description
        )
        embedding = generate_embedding(
            job.description
        )
        new_job = Job(
            title=job.title,
            description=job.description,
            created_by=current_user["user_id"]
        )
        db.add(new_job)

        await db.flush()

        await db.refresh(new_job)

        for skill in skills:
            job_skill = JobSkill(
                job_id=new_job.id,
                skill_name=skill
            )
            db.add(job_skill)

        await db.commit()

        job_collection = get_job_collection()
        job_collection.upsert(
            ids=[str(new_job.id)],
            embeddings=[embedding],
            documents=[job.description],
            metadatas=[
                {
                    "job_id": new_job.id,
                    "title": new_job.title,
                    "skills": ",".join(skills)
                }
            ]
        )
        return {

            "message": "Job created",
            "job_id": new_job.id,
            "skills": skills
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to create job"
        )



@jobs_router.get("/{job_id}/skills")
async def get_skills(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(
        require_roles(["recruiter","admin"])
    )
):
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    if (
        current_user["role"] != "admin"
        and job.created_by != current_user["user_id"]
    ):
        raise HTTPException(
            status_code=403,
            detail="Not allowed"
        )
    result = await db.execute(
        select(JobSkill).where(
            JobSkill.job_id == job_id
        )
    )
    skills = result.scalars().all()
    return [
        {
            "id": skill.id,
            "skill_name": skill.skill_name,
            "skill_status": skill.skill_status,
            "importance_weight": skill.importance_weight,
            "difficulty_level": skill.difficulty_level
        }
        for skill in skills
    ]


@jobs_router.patch("/{job_id}/skills")
async def review_skills(
    job_id: int,
    payload: SkillReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user= Depends(require_roles(["recruiter","admin"]))
):
    try:
        job = await db.get(Job,job_id)
        if not job:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )
        if (
            current_user["role"] != "admin"
            and job.created_by != current_user["user_id"]
        ):
            raise HTTPException(
                status_code=403,
                detail="Not allowed"
            )
    
        for skill in payload.skills:
            if skill.id:
            
                existing_skill = await db.get(
                    JobSkill,
                    skill.id
                )
                if not existing_skill:

                    raise HTTPException(status_code=404,detail="Skill not found")

                if existing_skill.job_id != job_id:

                    raise HTTPException(status_code=403,detail="Skill does not belong to this job")
                existing_skill.skill_name = skill.skill_name
                existing_skill.skill_status = skill.skill_status 
            else:
                new_skill = JobSkill(
                    job_id = job_id,
                    skill_name = skill.skill_name,
                    skill_status = skill.skill_status
                )
                db.add(new_skill)
        await db.commit()

        return {
        "message": "Skills updated successfully"
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to review skills"
        )

    

@jobs_router.get("/",response_model=list[JobResponse])
async def get_jobs(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Job)
    )
    jobs = result.scalars().all()
    return jobs
@jobs_router.post("/{job_id}/apply",response_model=ApplyJobResponse)

async def apply_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(["candidate"]))

):

    job = await db.get(Job,job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    result = await db.execute(
        select(Application).where(
            Application.user_id== current_user["user_id"],
            Application.job_id== job_id
        )
    )

    existing = (result.scalar_one_or_none())

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Already applied"
        )

    score = calculate_match_score(
        current_user["user_id"],
        job_id
    )
    application = Application(
        user_id=current_user["user_id"],
        job_id=job_id,
        status="pending",
        match_score=score
    )
    db.add(application)
    await db.commit()
    return {
        "message": "Applied successfully",
        "match_score": score
    }


@jobs_router.get("/{job_id}/applications",response_model=list[JobApplicationResponse]
)
async def get_job_applications(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(["admin", "recruiter"]))
):
    job = await db.get(Job, job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    if (
        current_user["role"] != "admin"
        and job.created_by != current_user["user_id"]
    ):
        raise HTTPException(
            status_code=403,
            detail="Not allowed"
        )

    result = await db.execute(
        select(Application, User)
        .join(User, Application.user_id == User.id)
        .where(Application.job_id == job_id)
        .order_by(
            Application.match_score.desc()
        )
    )

    data = [
        {
            "application_id": app.id,
            "status": app.status,
            "candidate_name": user.name,
            "candidate_email": user.email,
            "match_score":app.match_score,
            "resume_url":user.resume_url,
            "shortlist_status": app.shortlist_status,
            "recruiter_notes": app.recruiter_notes
        }
        for app, user in result.all()
    ]

    return data


@jobs_router.get(
    "/{job_id}/dashboard",
    response_model=JobDashboardResponse
)
async def get_job_dashboard(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(
        require_roles(["admin","recruiter"])
    )
):
    try:
        job = await db.get(Job,job_id)

        if not job:
            raise HTTPException(
                status_code=404,
                detail= "Job not found"
            )
        if(
            current_user["role"] != "admin" and job.created_by
            != current_user["user_id"]
        ):
            raise HTTPException(
                status_code=403,
                detail="Not allowed"
            )
        total_applications = await db.scalar(
            select(func.count(Application.id))
            .where(Application.job_id == job_id)
        ) or 0
        assessment_result = await db.execute(
            select(Assessment.id)
            .where(Assessment.job_id == job_id)
        )
        assessment = assessment_result.scalar_one_or_none()

        assessment_completed = 0
        passed_candidates = 0
        failed_candidates = 0
        average_score = 0.0

        if assessment:
            assessment_completed = await db.scalar(
                select(
                        func.count(
                            CandidateAttempt.id
                        )
                    ).where(
                        CandidateAttempt.assessment_id
                        == assessment,
                        CandidateAttempt.status
                        == "completed"
                    )
                )or 0
            
            passed_candidates = (
                await db.scalar(
                    select(
                        func.count(
                            CandidateAttempt.id
                        )
                    ).where(
                        CandidateAttempt.assessment_id
                        == assessment,
                        CandidateAttempt.passed
                        == True
                    )
                )
                or 0
            )
            failed_candidates = (
                await db.scalar(
                    select(
                        func.count(
                            CandidateAttempt.id
                        )
                    ).where(
                        CandidateAttempt.assessment_id
                        == assessment,
                        CandidateAttempt.passed
                        == False,
                        CandidateAttempt.status
                        == "completed"
                    )
                )
                or 0
            )
            average_score = (
                await db.scalar(
                    select(
                        func.avg(
                            CandidateAttempt.percentage
                        )
                    ).where(
                        CandidateAttempt.assessment_id
                        == assessment,
                        CandidateAttempt.status
                        == "completed"
                    )
                )
                or 0.0
            )

        shortlisted_candidates = (
            await db.scalar(
                select(
                    func.count(
                        Application.id
                    )
                ).where(
                    Application.job_id == job_id,
                    Application.shortlist_status
                    == "shortlisted"
                )
            )
            or 0
        )
        interview_candidates = (
            await db.scalar(
                select(
                    func.count(
                        Application.id
                    )
                ).where(
                    Application.job_id == job_id,
                    Application.shortlist_status
                    == "interview"
                )
            )
            or 0
        )
        hired_candidates = (
            await db.scalar(
                select(
                    func.count(
                        Application.id
                    )
                ).where(
                    Application.job_id == job_id,
                    Application.shortlist_status
                    == "hired"
                )
            )
            or 0
        )
        return {
            "job_id": job.id,
            "job_title": job.title,
            "total_applications":
                total_applications,
            "assessment_completed":
                assessment_completed,
            "passed_candidates":
                passed_candidates,
            "failed_candidates":
                failed_candidates,
            "shortlisted_candidates":
                shortlisted_candidates,
            "interview_candidates":
                interview_candidates,
            "hired_candidates":
                hired_candidates,
            "average_score":
                round(average_score, 2)
        }
            
    except HTTPException:
        raise 
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Dashboard fetch failed:{str(e)}"
        )
    

@jobs_router.get("/{job_id}/final-ranking")
async def get_final_ranking(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(
        require_roles(["admin","recruiter"])
    )
):
    try: 
        job = await db.get(Job,job_id)

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
        result = await db.execute(
            select(
                Application,
                User
            )
            .join(
                User,
                Application.user_id == User.id
            )
            .where(
                Application.job_id == job_id
            )
        )

        rows = result.all()

        rankings = []

        for application,user in rows:
            attempt_result = await db.execute(
                select(CandidateAttempt)
                .join(
                    Assessment,
                    CandidateAttempt.assessment_id == Assessment.id
                )
                .where(
                    CandidateAttempt.application_id == application.id,
                    CandidateAttempt.status =="completed"
                )
            )
            attempt = attempt_result.scalar_one_or_none()
            assessment_score = (attempt.percentage
            if attempt else 0
            )

            feedback_result = await db.execute(
                select(
                    func.avg(
                        (
                            InterviewFeedback.technical_score +
                            InterviewFeedback.communication_score +
                            InterviewFeedback.problem_solving_score

                        )/3
                    )
                )
                .join(
                    Interview,
                    InterviewFeedback.interview_id == Interview.id
                ).where(
                    Interview.application_id == application.id
                )
            )
            interview_score = (
                feedback_result.scalar() or 0
            )

            final_score = round(
                (
                    assessment_score * 0.6
                    +
                    interview_score * 0.4

                ),
                2
            )

            rankings.append(
                {
                    "candidate_id": user.id,
                    "candidate_name": user.name,
                    "candidate_email": user.email,
                    "assessment_score":
                        assessment_score,
                    "interview_score":
                        round(interview_score, 2),
                    "final_score":
                        final_score,
                    "shortlist_status":
                        application.shortlist_status
                }
            )
        rankings.sort(
            key=lambda x:x["final_score"],
            reverse=True
        )
        for idx,candidate in enumerate(
            rankings,
            start=1
        ):
            candidate["rank"] = idx
        return {
            "job_id":job.id,
            "job_title":job.title,
            "total_candidates":len(rankings),
            "rankings":rankings
        }
    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=(

                f"Failed to generate ranking: "

                f"{str(e)}"

            )

        )




@jobs_router.get("/{job_id}/offers")
async def get_job_offers(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(
        require_roles(["admin","recruiter"])
    )
):
    try:
        job = await db.get(Job, job_id)

        if not job:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )

        if (
            current_user["role"] != "admin"
            and job.created_by != current_user["user_id"]
        ):
            raise HTTPException(
                status_code=403,
                detail="Not allowed"
            )

        result = await db.execute(
            select(
                Offer,
                Application,
                User
            )
            .join(
                Application,
                Offer.application_id ==
                Application.id
            )
            .join(
                User,
                Application.user_id ==
                User.id
            )
            .where(
                Application.job_id == job_id
            )
        )

        rows = result.all()

        return [
            {
                "offer_id": offer.id,
                "candidate_id": user.id,
                "candidate_name": user.name,
                "candidate_email": user.email,
                "salary": offer.salary,
                "joining_date":
                    offer.joining_date,
                "status": offer.status,
                "created_at":
                    offer.created_at
            }
            for offer, app, user in rows
        ]
    except HTTPException as e:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"failed to fetch offers"
            f"{str(e)}"
        )
    


@jobs_router.get(

    "/{job_id}/offer-stats"

)

async def get_offer_stats(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(
        require_roles(["admin","recruiter"])
    )

):
    try:
        job = await db.get(Job, job_id)

        if not job:

            raise HTTPException(

                status_code=404,

                detail="Job not found"

            )

        if (

            current_user["role"] != "admin"

            and job.created_by != current_user["user_id"]

        ):

            raise HTTPException(

                status_code=403,

                detail="Not allowed"

            )

        result = await db.execute(

            select(

                func.count(Offer.id)

                .label("total"),

                func.count()

                .filter(

                    Offer.status == "pending"

                )

                .label("pending"),

                func.count()

                .filter(

                    Offer.status == "accepted"

                )

                .label("accepted"),

                func.count()

                .filter(

                    Offer.status == "declined"

                )

                .label("declined"),

                func.count()

                .filter(

                    Offer.status == "withdrawn"

                )

                .label("withdrawn")

            )

            .join(

                Application,

                Offer.application_id ==

                Application.id

            )

            .where(

                Application.job_id == job_id

            )

        )

        stats = result.one()

        return {

            "job_id": job_id,

            "total_offers":

                stats.total,

            "pending":

                stats.pending,

            "accepted":

                stats.accepted,

            "declined":

                stats.declined,

            "withdrawn":

                stats.withdrawn

        }
    except HTTPException as e:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"failed to fetch offer stats"
            f"{str(e)}"
        )



