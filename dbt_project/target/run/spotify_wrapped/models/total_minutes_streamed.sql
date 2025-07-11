
  create view "airflow"."public"."total_minutes_streamed__dbt_tmp"
    
    
  as (
    
    SELECT
        SUM(duration_ms / (60 * 1000)) AS total_minutes_streamed
    FROM
        raw_spotify_songs
    WHERE
        played_at_ts BETWEEN cast('2025-07-11' as date) AND cast('2025-07-11' as date)

  );