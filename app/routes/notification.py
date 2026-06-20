from fastapi import APIRouter,Depends,HTTPException
from app.utils.dependencies import get_db,require_roles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,func,update
from app.models_db.notifications import Notifications
from app.models.notification import NotificationResponse

notification_router = APIRouter(

    prefix="/notifications",

    tags=["Notifications"]

)

@notification_router.get("/",response_model=list[NotificationResponse])
async def get_notifications(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(
        require_roles(
            ["candidate","recruiter","admin"]
        )
    )
):
    try:
        result = await db.execute(
            select(Notifications)
            .where(
                Notifications.user_id == current_user["user_id"]
            )
            .order_by(
                Notifications.created_at.desc()
            )
        )
        notifications = (
            result.scalars().all()
        )
        return notifications
    except HTTPException:
            raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch notifications: "
                f"{str(e)}"
        )

@notification_router.patch(
     "{notification_id}/read"
)
async def mark_notification_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(
         require_roles(
              ["candidate","recruiter","admin"]
         )
    )

):
    try: 
        notification = await db.get(
               Notifications,
               notification_id
        )
        if not notification:
            raise HTTPException(
                status_code=404,
                detail="Notification not found"
            )
        if(notification.user_id!=current_user["user_id"]):
            raise HTTPException(
                 status_code=403,
                 detail="Not allowed"
            )
        if notification.is_read:
            return{
                "message":"Notification already read"
            }
        notification.is_read = True

        await db.commit()
        await db.refresh(notification)

        return{
            "message":
            "Notification marked as read",
            "notification_id": notification.id
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to mark notifications as read: "
                f"{str(e)}"
            )
        )
    

@notification_router.get(
    "/unread-count"
)
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(
        require_roles(
            ["candidate","recruiter","admin"]
        )
    )
): 
    try: 
        count = await db.scalar(
            select(
                func.count(
                    Notifications.id
                )
            ).where(
                Notifications.user_id == current_user["user_id"],
                Notifications.is_read == False
            )
        )
        return {
            "unread_count": count or 0
        }
    except HTTPException:
        raise
    except Exception as e: 
        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to fetch unread count: "
                f"{str(e)}"
            )
        )
    
@notification_router.patch(
    "/read-all"
)
async def mark_all_notifications_read(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(
        require_roles(
            ["candidate","recruiter","admin"]
        )
    )
):
    try: 
        await db.execute(
            update(Notifications)
            .where(
                Notifications.user_id == current_user["user_id"],
                Notifications.is_read == False
            )
            .values(is_read=True)
        )
        await db.commit()
        return{
            "message":"All notifications marked as read"
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to mark notifications as read: "
                f"{str(e)}"
            )
        )