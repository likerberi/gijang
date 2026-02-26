"""WebSocket 연결 관리자"""
from fastapi import WebSocket
from typing import Dict, List
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket 연결 관리"""
    
    def __init__(self):
        # user_id -> List[WebSocket]
        self.active_connections: Dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """클라이언트 연결"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        logger.info(f"WebSocket 연결: user_id={user_id}, 총 연결 수={len(self.active_connections[user_id])}")
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        """클라이언트 연결 해제"""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
                logger.info(f"WebSocket 연결 해제: user_id={user_id}")
            
            # 연결이 없으면 딕셔너리에서 제거
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def send_personal_message(self, message: dict, user_id: int):
        """특정 사용자에게 메시지 전송"""
        if user_id in self.active_connections:
            disconnected = []
            
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"메시지 전송 실패: {e}")
                    disconnected.append(connection)
            
            # 연결 끊긴 것들 제거
            for conn in disconnected:
                self.disconnect(conn, user_id)
    
    async def broadcast(self, message: dict):
        """모든 연결된 클라이언트에게 메시지 전송"""
        for user_id, connections in self.active_connections.items():
            await self.send_personal_message(message, user_id)
    
    def get_connection_count(self, user_id: int) -> int:
        """사용자의 연결 수"""
        return len(self.active_connections.get(user_id, []))
    
    def get_total_connections(self) -> int:
        """전체 연결 수"""
        return sum(len(conns) for conns in self.active_connections.values())


# 전역 연결 관리자
manager = ConnectionManager()
