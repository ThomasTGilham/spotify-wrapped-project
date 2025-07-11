{% macro get_newly_discovered_artists(start_date) %}
    WITH all_artists AS (
        SELECT DISTINCT
            artist_name
        FROM
            raw_spotify_songs
        WHERE
            played_at_ts >= cast('{{ start_date }}' as date)
    ),
    previous_artists AS (
        SELECT DISTINCT
            artist_name
        FROM
            raw_spotify_songs
        WHERE
            played_at_ts < cast('{{ start_date }}' as date)
    )
    SELECT
        a.artist_name
    FROM
        all_artists a
    LEFT JOIN
        previous_artists p ON a.artist_name = p.artist_name
    WHERE
        p.artist_name IS NULL
{% endmacro %}