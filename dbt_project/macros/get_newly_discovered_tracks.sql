{% macro get_newly_discovered_tracks(start_date) %}
    WITH all_tracks AS (
        SELECT DISTINCT
            track_name
        FROM
            raw_spotify_songs
        WHERE
            played_at_ts >= cast('{{ start_date }}' as date)
    ),
    previous_tracks AS (
        SELECT DISTINCT
            track_name
        FROM
            raw_spotify_songs
        WHERE
            played_at_ts < cast('{{ start_date }}' as date)
    )
    SELECT
        a.track_name
    FROM
        all_tracks a
    LEFT JOIN
        previous_tracks p ON a.track_name = p.track_name
    WHERE
        p.track_name IS NULL
{% endmacro %}