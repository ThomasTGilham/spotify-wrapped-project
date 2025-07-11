{% macro get_tracks_per_dow(start_date, end_date) %}
    SELECT
        EXTRACT(DOW FROM played_at_ts) AS day_of_week,
        EXTRACT(HOUR FROM played_at_ts) AS hour,
        SUM(duration_ms / (1000 * 60)) AS total_minutes
    FROM
        raw_spotify_songs
    WHERE
        played_at_ts BETWEEN cast('{{ start_date }}' as date) AND cast('{{ end_date }}' as date)
    GROUP BY
        1, 2
{% endmacro %}