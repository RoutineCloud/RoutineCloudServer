from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, or_

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.friendship import Friendship, FriendshipStatus
from app.models.user import User
from app.schemas.friend import FriendRead, FriendAdd

router = APIRouter(
    prefix="/api/friends",
    tags=["friends"],
)

@router.get("/", response_model=List[FriendRead], operation_id="friends_list")
async def list_friends(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all accepted friends of the current user.
    """
    # Bidirectional: find all friendships where user_id is current_user or friend_id is current_user, and status is ACCEPTED
    stmt = (
        select(Friendship)
        .where(
            or_(Friendship.user_id == current_user.id, Friendship.friend_id == current_user.id),
            Friendship.status == FriendshipStatus.ACCEPTED
        )
    )
    friendships = db.exec(stmt).all()
    
    friend_ids = []
    for f in friendships:
        if f.user_id == current_user.id:
            friend_ids.append(f.friend_id)
        else:
            friend_ids.append(f.user_id)
    
    if not friend_ids:
        return []
        
    friends = db.exec(select(User).where(User.id.in_(friend_ids))).all()
    
    result = []
    for friend in friends:
        result.append(FriendRead(
            id=friend.id,
            username=friend.username,
            profile_picture=friend.profile_picture,
            status=FriendshipStatus.ACCEPTED
        ))
    return result

@router.get("/requests", response_model=List[FriendRead], operation_id="friends_requests_list")
async def list_friend_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all pending friend requests sent TO the current user.
    """
    stmt = (
        select(Friendship, User)
        .join(User, Friendship.user_id == User.id)
        .where(
            Friendship.friend_id == current_user.id,
            Friendship.status == FriendshipStatus.PENDING
        )
    )
    rows = db.exec(stmt).all()
    
    result = []
    for friendship, user in rows:
        result.append(FriendRead(
            id=user.id,
            username=user.username,
            profile_picture=user.profile_picture,
            status=FriendshipStatus.PENDING
        ))
    return result

@router.post("/add", status_code=status.HTTP_201_CREATED, operation_id="friends_add")
async def add_friend(
    payload: FriendAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a friend request using a friend code.
    """
    if not payload.friend_code:
        raise HTTPException(status_code=400, detail="Friend code is required")
    
    friend = db.exec(select(User).where(User.friend_code == payload.friend_code.upper())).first()
    if not friend:
        raise HTTPException(status_code=404, detail="User with this friend code not found")
    
    if friend.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot add yourself as a friend")
    
    # Check if a friendship record already exists in any direction
    existing = db.exec(
        select(Friendship).where(
            or_(
                (Friendship.user_id == current_user.id) & (Friendship.friend_id == friend.id),
                (Friendship.user_id == friend.id) & (Friendship.friend_id == current_user.id)
            )
        )
    ).first()
    
    if existing:
        if existing.status == FriendshipStatus.ACCEPTED:
            raise HTTPException(status_code=400, detail="User is already your friend")
        if existing.user_id == current_user.id:
            raise HTTPException(status_code=400, detail="Friend request already sent")
        else:
            # If the other person already sent a request, accept it automatically? 
            # Or tell the user to check their requests. 
            # Let's just accept it for better UX.
            existing.status = FriendshipStatus.ACCEPTED
            db.add(existing)
            db.commit()
            return {"status": "success", "message": "Friend request accepted", "friend_username": friend.username}
    
    new_friendship = Friendship(user_id=current_user.id, friend_id=friend.id, status=FriendshipStatus.PENDING)
    db.add(new_friendship)
    db.commit()
    return {"status": "success", "message": "Friend request sent", "friend_username": friend.username}

@router.post("/{friend_id}/accept", operation_id="friends_accept")
async def accept_friend(
    friend_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Accept a friend request.
    """
    friendship = db.exec(
        select(Friendship).where(
            Friendship.user_id == friend_id,
            Friendship.friend_id == current_user.id,
            Friendship.status == FriendshipStatus.PENDING
        )
    ).first()
    
    if not friendship:
        raise HTTPException(status_code=404, detail="Friend request not found")
    
    friendship.status = FriendshipStatus.ACCEPTED
    db.add(friendship)
    db.commit()
    return {"status": "success"}

@router.post("/{friend_id}/decline", operation_id="friends_decline")
async def decline_friend(
    friend_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Decline a friend request.
    """
    friendship = db.exec(
        select(Friendship).where(
            Friendship.user_id == friend_id,
            Friendship.friend_id == current_user.id,
            Friendship.status == FriendshipStatus.PENDING
        )
    ).first()
    
    if not friendship:
        raise HTTPException(status_code=404, detail="Friend request not found")
    
    db.delete(friendship)
    db.commit()
    return {"status": "success"}

@router.delete("/{friend_id}", operation_id="friends_remove")
async def remove_friend(
    friend_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Remove a friend or cancel a request.
    """
    friendship = db.exec(
        select(Friendship).where(
            or_(
                (Friendship.user_id == current_user.id) & (Friendship.friend_id == friend_id),
                (Friendship.user_id == friend_id) & (Friendship.friend_id == current_user.id)
            )
        )
    ).first()
    
    if not friendship:
        raise HTTPException(status_code=404, detail="Friendship not found")
    
    db.delete(friendship)
    db.commit()
    return {"status": "success"}
