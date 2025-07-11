
  create view "airflow"."public"."tracks_listened_to__dbt_tmp"
    
    
  as (
    
    SELECT
        COUNT(DISTINCT track_name) AS total_tracks
    FROM
        raw_spotify_songs
    WHERE
        played_at_ts BETWEEN cast('2025-07-11' as date) AND cast('2025-07-11' as date)

  );