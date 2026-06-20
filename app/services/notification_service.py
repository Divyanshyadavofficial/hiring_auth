from app.models_db.notifications import Notifications

async def create_notification(
        db,
        user_id: int,
        title: str,
        message: str,
        type: str
):
    Notification = Notifications(
        user_id=user_id,
        title = title,
        message=message,
        type=type
    )
    db.add(Notification)