
    SELECT
        artist_name,
        SUM(duration_ms / (1000 * 60)) AS total_minutes_played
    FROM
        raw_spotify_songs
    WHERE
        played_at_ts BETWEEN cast('2025-07-11' as date) AND cast('2025-07-11' as date)
    GROUP BY
        artist_name
    ORDER BY
        total_minutes_played DESC
