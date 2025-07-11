{% macro get_total_minutes_streamed(start_date, end_date) %}
    SELECT
        SUM(duration_ms / (60 * 1000)) AS total_minutes_streamed
    FROM
        raw_spotify_songs
    WHERE
        played_at_ts BETWEEN cast('{{ start_date }}' as date) AND cast('{{ end_date }}' as date)
{% endmacro %}