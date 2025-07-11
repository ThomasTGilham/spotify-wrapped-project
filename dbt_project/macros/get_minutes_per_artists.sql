{% macro get_minutes_per_artists(start_date, end_date) %}
    SELECT
        artist_name,
        SUM(duration_ms / (1000 * 60)) AS total_minutes_played
    FROM
        raw_spotify_songs
    WHERE
        played_at_ts BETWEEN cast('{{ start_date }}' as date) AND cast('{{ end_date }}' as date)
    GROUP BY
        artist_name
    ORDER BY
        total_minutes_played DESC
{% endmacro %}