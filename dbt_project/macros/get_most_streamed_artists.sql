{% macro get_most_streamed_artists(start_date, end_date) %}
    SELECT
        artist_name,
        COUNT(*) AS streams
    FROM
        raw_spotify_songs
    WHERE
        played_at_ts BETWEEN cast('{{ start_date }}' as date) AND cast('{{ end_date }}' as date)
    GROUP BY
        artist_name
    ORDER BY
        streams DESC
{% endmacro %}
