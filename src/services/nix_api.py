import httpx
import asyncio
from config.settings import settings
from loguru import logger
from typing import Optional, Dict, Any, List

class NixAPI:
    def __init__(self):
        self.base_url = settings.NIX_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {settings.NIX_API_TOKEN}",
            "Content-Type": "application/json"
        }
        # Cliente HTTP/2 com pool de conexões massivo e timeouts curtos para velocidade máxima
        self.client = httpx.AsyncClient(
            headers=self.headers,
            http2=True,
            timeout=httpx.Timeout(12.0, connect=4.0), 
            limits=httpx.Limits(
                max_keepalive_connections=100, 
                max_connections=200,
                keepalive_expiry=30.0
            )
        )

    async def create_room(self, password: str, start_delay: int, config_type: str = "ap_padrao", 
                          room_name: str = "Sala FF", max_players: int = 30, team_count: int = 8) -> Dict[str, Any]:
        url = f"{self.base_url}rooms"
        payload = {
            "password": password,
            "start_delay_minutes": start_delay,
            "config_type": config_type,
            "room_name": room_name,
            "max_players": max_players,
            "team_count": team_count
        }
        
        try:
            logger.info(f"🚀 Enviando comando de criação: {payload}")
            response = await self.client.post(url, json=payload)
            
            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"✅ Comando aceito pela API: {response.status_code}")
                return data
            else:
                logger.error(f"❌ API Error: {response.status_code} - {response.text}")
                return {"status": "error", "code": response.status_code, "msg": response.text}
                
        except httpx.TimeoutException:
            logger.warning("⚠️ Timeout inicial na API NixBot. A sala pode estar sendo processada.")
            return {"status": "processing"}
        except Exception as e:
            logger.error(f"🔥 Unexpected API Error: {str(e)}")
            return {"status": "error", "msg": str(e)}

    async def get_room_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}rooms/{session_id}"
        try:
            response = await self.client.get(url)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None

    async def get_latest_rooms(self) -> List[Dict[str, Any]]:
        """Busca a lista de salas ativas para encontrar salas criadas via timeout."""
        url = f"{self.base_url}rooms"
        try:
            # A documentação mostra que GET /rooms retorna a lista de sessões ativas
            response = await self.client.get(url)
            if response.status_code == 200:
                rooms = response.json()
                # Garante que retornamos uma lista
                if isinstance(rooms, list):
                    return rooms
                elif isinstance(rooms, dict) and "rooms" in rooms:
                    return rooms["rooms"]
                return []
            return []
        except Exception as e:
            logger.error(f"Error listing rooms: {str(e)}")
            return []

    async def start_room(self, session_id: str) -> bool:
        url = f"{self.base_url}rooms/{session_id}/start"
        try:
            response = await self.client.post(url)
            return response.status_code in [200, 201]
        except Exception:
            return False

    async def kick_player(self, session_id: str, player_uid: str) -> bool:
        url = f"{self.base_url}rooms/{session_id}/kick"
        payload = {"player_uid": player_uid}
        try:
            response = await self.client.post(url, json=payload)
            return response.status_code in [200, 201]
        except Exception:
            return False

    async def close(self):
        await self.client.aclose()

nix_api = NixAPI()
