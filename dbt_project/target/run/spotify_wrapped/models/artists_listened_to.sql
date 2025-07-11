
  create view "airflow"."public"."artists_listened_to__dbt_tmp"
    
    
  as (
    
    SELECT
        COUNT(DISTINCT artist_name) AS total_artists
    FROM
        raw_spotify_songs
    WHERE
        played_at_ts BETWEEN cast('2025-07-11' as date) AND cast('2025-07-11' as date)

  );