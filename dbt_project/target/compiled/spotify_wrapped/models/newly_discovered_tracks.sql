
    WITH all_tracks AS (
        SELECT DISTINCT
            track_name
        FROM
            raw_spotify_songs
        WHERE
            played_at_ts >= cast('2025-07-11' as date)
    ),
    previous_tracks AS (
        SELECT DISTINCT
            track_name
        FROM
            raw_spotify_songs
        WHERE
            played_at_ts < cast('2025-07-11' as date)
    )
    SELECT
        a.track_name
    FROM
        all_tracks a
    LEFT JOIN
        previous_tracks p ON a.track_name = p.track_name
    WHERE
        p.track_name IS NULL
