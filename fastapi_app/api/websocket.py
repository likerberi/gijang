"""WebSocket API"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
import logging

from ..core.websocket import manager
from ..core.security import decode_token
from ..db.session import get_db
from ..models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """WebSocket 연결 엔드포인트"""
    
    # 토큰 검증
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=1008, reason="Invalid token")
        return
    
    user_id_str = payload.get("sub")
    if not user_id_str:
        await websocket.close(code=1008, reason="Invalid token")
        return
    
    try:
        user_id = int(user_id_str)
    except (TypeError, ValueError):
        await websocket.close(code=1008, reason="Invalid token")
        return
    
    # 사용자 확인
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        await websocket.close(code=1008, reason="User not found or inactive")
        return
    
    # 연결
    await manager.connect(websocket, user_id)
    
    try:
        # 환영 메시지
        await manager.send_personal_message(
            {
                "type": "connection",
                "message": "WebSocket 연결 성공",
                "user_id": user_id
            },
            user_id
        )
        
        # 메시지 수신 루프
        while True:
            # 클라이언트로부터 메시지 수신 (keep-alive)
            data = await websocket.receive_text()
            logger.debug(f"메시지 수신 from user {user_id}: {data}")
            
            # Echo back (선택적)
            # await manager.send_personal_message(
            #     {"type": "echo", "data": data},
            #     user_id
            # )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        logger.info(f"WebSocket 연결 종료: user_id={user_id}")
    
    except Exception as e:
        logger.error(f"WebSocket 오류: {e}", exc_info=True)
        manager.disconnect(websocket, user_id)
