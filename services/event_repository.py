from typing import Any

import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor
from functools import lru_cache


load_dotenv()


def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
        )
        print("[Debug] DB 연결 성공")
        return conn

    except Exception as e:
        print(f"[Error] DB 연결 실패: {e}")
        raise


class EventRepository:
    @lru_cache(maxsize=1)
    def load_events_dataframe(self) -> pd.DataFrame:
        query = """
            SELECT event_id, payload::jsonb -> 'source_row' AS source_row
            FROM public.events
            WHERE jsonb_typeof(payload::jsonb -> 'source_row') = 'object'
        """

        conn = get_db_connection()

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                rows: list[dict[str, Any]] = cur.fetchall()
        finally:
                conn.close()

        records: list[dict[str, Any]] = []

        for row in rows:
            source_row = dict(row["source_row"])
            source_row["event_id"] = str(row["event_id"])
            records.append(source_row)

        event_df = pd.DataFrame(records)
        print(f"[debug] DB조회 : {event_df.head()}")
        return event_df

    def clear_cache(self):
        self.load_events_dataframe.cache_clear()
        



# repository = EventRepository()
# event_df = repository.load_events_dataframe()

# print(event_df.head())