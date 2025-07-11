{% macro get_most_streamed_songs(start_date, end_date) %}
    SELECT
        track_name,
        artist_name,
        COUNT(*) AS streams
    FROM
        raw_spotify_songs
    WHERE
        played_at_ts BETWEEN cast('{{ start_date }}' as date) AND cast('{{ end_date }}' as date)
    GROUP BY
        track_name,
        artist_name
    ORDER BY
        streams DESC
{% endmacro %}