
  create view "airflow"."public"."tracks_per_dow__dbt_tmp"
    
    
  as (
    
    SELECT
        EXTRACT(DOW FROM played_at_ts) AS day_of_week,
        EXTRACT(HOUR FROM played_at_ts) AS hour,
        SUM(duration_ms / (1000 * 60)) AS total_minutes
    FROM
        raw_spotify_songs
    WHERE
        played_at_ts BETWEEN cast('2025-07-11' as date) AND cast('2025-07-11' as date)
    GROUP BY
        1, 2

  );