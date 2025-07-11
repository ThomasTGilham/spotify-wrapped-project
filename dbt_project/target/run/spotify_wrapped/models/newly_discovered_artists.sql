
  create view "airflow"."public"."newly_discovered_artists__dbt_tmp"
    
    
  as (
    
    WITH all_artists AS (
        SELECT DISTINCT
            artist_name
        FROM
            raw_spotify_songs
        WHERE
            played_at_ts >= cast('2025-07-11' as date)
    ),
    previous_artists AS (
        SELECT DISTINCT
            artist_name
        FROM
            raw_spotify_songs
        WHERE
            played_at_ts < cast('2025-07-11' as date)
    )
    SELECT
        a.artist_name
    FROM
        all_artists a
    LEFT JOIN
        previous_artists p ON a.artist_name = p.artist_name
    WHERE
        p.artist_name IS NULL

  );