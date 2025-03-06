import asyncpg
from datetime import datetime
from app.config import Config

class RequestLogger:
    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def save_request(self, request_id, input_type, input_data, response_data, status="completed"):
        """Insert a request and response into the DB with error handling."""
        insert_query = """
        INSERT INTO requests (id, input_type, input_data, status, response, created_at)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (id) 
        DO UPDATE SET 
            status = $4,
            response = $5,
            updated_at = $6;
        """
        await self._execute_query(
            insert_query,
            (request_id, input_type, str(input_data), status, str(response_data), datetime.utcnow())
        )

    async def get_request(self, request_id):
        """Fetch a request and response by ID, handling errors."""
        select_query = "SELECT id, input_type, input_data, status, response, created_at FROM requests WHERE id = $1;"
        result = await self._execute_query(select_query, (request_id,), fetchone=True)
        if result:
            return {
                "request_id": result[0],
                "input_type": result[1],
                "input_data": result[2],
                "status": result[3],
                "response": result[4],
                "created_at": result[5].isoformat() if result[5] else None,
            }
        return None

    async def delete_old_requests(self, days=30):
        """Cleanup old requests (default: older than 30 days)."""
        delete_query = "DELETE FROM requests WHERE created_at < NOW() - INTERVAL %s DAY;"
        await self._execute_query(delete_query, (days,), commit=True)

    async def _execute_query(self, query, params=None, commit=False, fetchone=False):
        """Utility function for executing DB queries safely."""
        try:
            async with self.db_pool.acquire() as conn:
                if fetchone:
                    return await conn.fetchrow(query, *params)
                else:
                    await conn.execute(query, *params)
                    return None
        except Exception as e:
            print(f"Database error: {e}")
            return None
