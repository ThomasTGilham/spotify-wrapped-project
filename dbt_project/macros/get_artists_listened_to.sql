{% macro get_artists_listened_to(start_date, end_date) %}
    SELECT
        COUNT(DISTINCT artist_name) AS total_artists
    FROM
        raw_spotify_songs
    WHERE
        played_at_ts BETWEEN cast('{{ start_date }}' as date) AND cast('{{ end_date }}' as date)
{% endmacro %}