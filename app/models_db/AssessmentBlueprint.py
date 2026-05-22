from datetime import datetime

from sqlalchemy import (
    Integer,
    String,
    ForeignKey,
    JSON,
    Boolean,
    DateTime,
    Index,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from sqlalchemy.sql import func

from app.models_db.base import Base


class AssessmentBlueprint(Base):
    """
    AssessmentBlueprint represents the planning layer of the assessment system.

    This table DOES NOT store actual questions.

    It stores:
    - assessment structure
    - question distribution
    - timing
    - scoring rules
    - skill distribution
    - difficulty distribution

    One blueprint can generate multiple assessments.

    Example:

    Blueprint
        ↓
    Assessment v1
    Assessment v2
    Assessment v3

    This allows recruiters to regenerate questions
    while keeping the same assessment strategy.
    """

    __tablename__ = "assessment_blueprints"

    __table_args__ = (
        Index("idx_blueprint_job", "job_id"),
        Index("idx_blueprint_status", "status"),
    )

    # =====================================================
    # PRIMARY KEY
    # =====================================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    # =====================================================
    # FOREIGN KEYS
    # =====================================================

    job_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
    )

    # =====================================================
    # TIMESTAMPS
    # =====================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # =====================================================
    # ASSESSMENT CONFIGURATION
    # =====================================================

    total_questions: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
    )

    total_duration_minutes: Mapped[int] = mapped_column(
        Integer,
        default=30,
        nullable=False,
    )

    # -----------------------------------------------------
    # QUESTION TYPE DISTRIBUTION
    # -----------------------------------------------------

    # Example:
    # mcq_count = 5
    # coding_count = 3
    # debugging_count = 2

    mcq_count: Mapped[int] = mapped_column(
        Integer,
        default=5,
        nullable=False,
    )

    coding_count: Mapped[int] = mapped_column(
        Integer,
        default=2,
        nullable=False,
    )

    debugging_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    # =====================================================
    # SKILL DISTRIBUTION
    # =====================================================

    """
    Stores how many questions belong to each skill.

    Example:

    {
        "Python": 4,
        "FastAPI": 3,
        "PostgreSQL": 2,
        "Docker": 1
    }

    This becomes the main input for question generation.
    """

    skill_distribution: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    # =====================================================
    # DIFFICULTY DISTRIBUTION
    # =====================================================

    """
    Stores assessment difficulty breakdown.

    Example:

    {
        "easy": 2,
        "medium": 5,
        "hard": 3
    }
    """

    difficulty_distribution: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    # =====================================================
    # EVALUATION CONFIGURATION
    # =====================================================

    passing_score_percentage: Mapped[int] = mapped_column(
        Integer,
        default=70,
        nullable=False,
    )

    # Optional future feature
    negative_marking_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Example:
    # 0.25 = -0.25 marks per incorrect answer

    negative_marking_percentage: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # =====================================================
    # RECRUITER REVIEW WORKFLOW
    # =====================================================

    """
    Suggested status flow:

    draft
        ↓
    pending_review
        ↓
    approved
        ↓
    published
        ↓
    archived
    """

    status: Mapped[str] = mapped_column(
        String,
        default="draft",
        nullable=False,
    )

    approved_by_recruiter: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Optional recruiter comments
    recruiter_feedback: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================

    assessments = relationship(
        "Assessment",
        back_populates="blueprint",
        cascade="all, delete-orphan",
    )


class Assessment(Base):
    """
    Assessment represents an actual generated assessment.

    Blueprint = strategy
    Assessment = generated assessment version

    Example:

    Blueprint
        ↓
    Assessment v1
    Assessment v2
    Assessment v3

    Recruiter may reject one version and regenerate another.
    """

    __tablename__ = "assessments"

    __table_args__ = (
        Index("idx_assessment_job", "job_id"),
        Index("idx_assessment_blueprint", "blueprint_id"),
        Index("idx_assessment_status", "status"),
    )

    # =====================================================
    # PRIMARY KEY
    # =====================================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    # =====================================================
    # FOREIGN KEYS
    # =====================================================

    job_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
    )

    blueprint_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("assessment_blueprints.id", ondelete="CASCADE"),
        nullable=False,
    )

    approved_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
    )

    # =====================================================
    # TIMESTAMPS
    # =====================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # =====================================================
    # VERSIONING
    # =====================================================

    """
    Allows multiple regenerated versions.

    Example:

    version=1
    version=2
    version=3
    """

    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    # =====================================================
    # REVIEW / PUBLISHING WORKFLOW
    # =====================================================

    """
    Suggested flow:

    pending_review
        ↓
    approved
        ↓
    published
        ↓
    archived
    """

    status: Mapped[str] = mapped_column(
        String,
        default="pending_review",
        nullable=False,
    )

    # =====================================================
    # RECRUITER REVIEW FEEDBACK
    # =====================================================

    # Example:
    # "Need harder coding questions"
    # "Too many MCQs"

    review_feedback: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================

    blueprint = relationship(
        "AssessmentBlueprint",
        back_populates="assessments",
    )

    questions = relationship(
        "AssessmentQuestion",
        back_populates="assessment",
        cascade="all, delete-orphan"
    )