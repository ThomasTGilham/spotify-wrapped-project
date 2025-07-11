
  create view "airflow"."public"."most_streamed_artists__dbt_tmp"
    
    
  as (
    
    SELECT
        artist_name,
        COUNT(*) AS streams
    FROM
        raw_spotify_songs
    WHERE
        played_at_ts BETWEEN cast('2025-07-11' as date) AND cast('2025-07-11' as date)
    GROUP BY
        artist_name
    ORDER BY
        streams DESC

  );