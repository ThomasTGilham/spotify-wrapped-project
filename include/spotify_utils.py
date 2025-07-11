import requests
import base64
import pandas as pd
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
from airflow.models import Variable
from airflow.providers.postgres.hooks.postgres import PostgresHook
import warnings
import logging
import json

# Use a non-interactive backend for Matplotlib to prevent it from trying to open a UI
matplotlib.use('Agg')
warnings.filterwarnings("ignore")

# --- Task 1: Refresh Spotify Token ---

def refresh_spotify_token(**kwargs):
    """
    Refreshes the Spotify access token using the refresh token and saves it to Airflow Variables.
    Pushes the new access token to XComs for the next task.
    """
    client_id = Variable.get("SPOTIFY_CLIENT_ID")
    client_secret = Variable.get("SPOTIFY_CLIENT_SECRET")
    refresh_token = Variable.get("SPOTIFY_REFRESH_TOKEN")

    auth_string = f"{client_id}:{client_secret}"
    auth_b64 = base64.b64encode(auth_string.encode()).decode()

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }

    logging.info("Requesting new access token from Spotify...")
    result = requests.post(url, headers=headers, data=data)
    result.raise_for_status()  # Raise an exception for bad status codes
    
    response_json = result.json()
    new_access_token = response_json.get("access_token")

    if not new_access_token:
        logging.error("Could not get new access token from Spotify.")
        raise ValueError("Failed to get new access token.")

    logging.info("Successfully received new access token.")
    
    # Push the new access token to XComs for the next task to use
    ti = kwargs['ti']
    ti.xcom_push(key='spotify_access_token', value=new_access_token)


# --- Task 2: Get Recently Played Songs ---

def get_spotify_songs(postgres_conn_id, **kwargs):
    """
    Fetches recently played songs from the Spotify API after the last recorded timestamp.
    """
    ti = kwargs['ti']
    access_token = ti.xcom_pull(key='spotify_access_token', task_ids='refresh_spotify_token')

    if not access_token:
        logging.error("Access token not found in XComs.")
        raise ValueError("Access token is missing.")

    # Get the timestamp of the last song played from our database
    hook = PostgresHook(postgres_conn_id=postgres_conn_id)
    # Note: Assumes a 'raw_spotify_songs' table exists.
    # The 'played_at' column should be a UNIX timestamp (in milliseconds).
    last_played_at_ms = hook.get_first("SELECT MAX(played_at_ms) FROM raw_spotify_songs;")
    
    # If the table is empty, last_played_at_ms[0] will be None
    if last_played_at_ms and last_played_at_ms[0]:
        after_timestamp = int(last_played_at_ms[0])
        logging.info(f"Fetching songs played after timestamp: {after_timestamp}")
    else:
        after_timestamp = None
        logging.info("No previous songs found. Fetching most recent songs.")

    headers = {"Authorization": f"Bearer {access_token}"}
    url = "https://api.spotify.com/v1/me/player/recently-played"
    
    params = {"limit": 50}
    if after_timestamp:
        params["after"] = after_timestamp

    logging.info(f"Making request to Spotify API with params: {params}")
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    data = response.json()
    songs = data.get("items", [])

    if not songs:
        logging.info("No new songs to add.")
        return # Stop if there are no new songs

    logging.info(f"Successfully fetched {len(songs)} new songs.")
    
    # Push the list of songs to XComs
    ti.xcom_push(key='spotify_songs_data', value=songs)


# --- Task 3: Load Songs to Database ---


def load_songs_to_db(postgres_conn_id, **kwargs):
    """
    Pulls song data from XComs, filters out any songs that are already
    in the database, and loads only the new songs into the staging table.
    This function is idempotent.
    """
    ti = kwargs['ti']
    songs_data = ti.xcom_pull(key='spotify_songs_data', task_ids='get_spotify_songs')

    if not songs_data:
        logging.info("No song data found in XComs. Skipping database load.")
        return

    # --- 1. Transform the raw JSON data into a structured DataFrame ---
    song_records = []
    for song in songs_data:
        record = {
            "played_at_ts": song["played_at"],
            "track_id": song["track"]["id"],
            "track_name": song["track"]["name"],
            "artist_id": song["track"]["artists"][0]["id"],
            "artist_name": song["track"]["artists"][0]["name"],
            "album_id": song["track"]["album"]["id"],
            "album_name": song["track"]["album"]["name"],
            "duration_ms": song["track"]["duration_ms"],
            "raw_json": json.dumps(song) # Convert dict to JSON string for storage
        }
        song_records.append(record)
    
    df = pd.DataFrame(song_records)
    
    # Ensure played_at_ts is a proper datetime object for comparison
    df['played_at_ts'] = pd.to_datetime(df['played_at_ts'])

    # --- 2. Filter out songs that already exist in the database ---
    hook = PostgresHook(postgres_conn_id=postgres_conn_id)
    
    # Get existing primary keys from the database
    # This is more efficient than loading the whole table
    try:
        existing_keys_df = hook.get_pandas_df("SELECT track_id, played_at_ts FROM raw_spotify_songs")
    except Exception as e:
        logging.error(f"Could not query existing songs. Assuming table is empty. Error: {e}")
        existing_keys_df = pd.DataFrame(columns=['track_id', 'played_at_ts'])

    # If there are existing keys, ensure the timestamp column is a datetime object
    if not existing_keys_df.empty:
        existing_keys_df['played_at_ts'] = pd.to_datetime(existing_keys_df['played_at_ts'], utc=True)

    # Merge the new data with existing keys to find which songs are truly new
    # The '_merge' column will indicate the source of each row
    merged_df = df.merge(
        existing_keys_df, 
        on=['track_id', 'played_at_ts'], 
        how='left', 
        indicator=True
    )
    
    # Keep only the rows that are unique to the new data (from the 'left' df)
    new_songs_df = merged_df[merged_df['_merge'] == 'left_only'].copy()
    
    # Drop the merge indicator column as it's no longer needed
    new_songs_df.drop(columns=['_merge'], inplace=True)

    # --- 3. Load the new, unique songs into the database ---
    if new_songs_df.empty:
        logging.info("No new unique songs to load.")
        return

    logging.info(f"Loading {len(new_songs_df)} new unique records into 'raw_spotify_songs' table.")
    
    # Use the hook to get a SQLAlchemy engine for pandas
    engine = hook.get_sqlalchemy_engine()
    new_songs_df.to_sql(
        'raw_spotify_songs', 
        engine, 
        if_exists='append', 
        index=False,
        chunksize=500 # Optional: load data in chunks for better performance
    )
    
    logging.info("Successfully loaded new data into PostgreSQL.")

def generate_dashboard_image(postgres_conn_id, output_path, **kwargs):
    """
    Connects to Postgres, queries the transformed data (from dbt),
    generates a dashboard image, and saves it to the specified path.
    """
    # Use an Airflow Hook to connect to the database
    hook = PostgresHook(postgres_conn_id=postgres_conn_id)
    conn = hook.get_conn()
    
    # --- Load data from dbt models ---
    # These SQL queries assume your dbt models have already run successfully
    artists_listened_to = pd.read_sql_query("SELECT * FROM artists_listened_to", conn)
    minutes_per_artist = pd.read_sql_query("SELECT * FROM minutes_per_artist", conn)
    most_streamed_artists = pd.read_sql_query("SELECT * FROM most_streamed_artists", conn)
    most_streamed_songs = pd.read_sql_query("SELECT * FROM most_streamed_songs", conn)
    total_minutes_streamed = pd.read_sql_query("SELECT * FROM total_minutes_streamed", conn)
    tracks_listened_to = pd.read_sql_query("SELECT * FROM tracks_listened_to", conn)
    newly_discovered_tracks = pd.read_sql_query("SELECT * FROM newly_discovered_tracks", conn)
    newly_discovered_artists = pd.read_sql_query("SELECT DISTINCT(artist_name) FROM newly_discovered_artists", conn)
    tracks_per_dow = pd.read_sql_query("SELECT * FROM tracks_per_dow ", conn)

    conn.close() # Close connection once data is loaded

    # --- Setup for plotting ---
    sns.set_style("darkgrid")
    sns.set(rc={"axes.facecolor": "#FFF9ED", "figure.facecolor": "#FFF9ED"})
    colors = ["#EE1E14", "#364BA5"]
    cmap = plt.cm.get_cmap("PuRd")
    
    fig = plt.figure(figsize=(40, 28))
    
    # --- Define all subplots (ax1, ax2, etc.) ---
    ax1 = plt.subplot2grid((3, 3), (0, 0))
    ax2 = plt.subplot2grid((3, 3), (0, 1))
    ax3 = plt.subplot2grid((3, 3), (0, 2))
    ax4 = plt.subplot2grid((3, 3), (1, 0))
    ax5 = plt.subplot2grid((3, 3), (1, 1))
    ax6 = plt.subplot2grid((3, 3), (1, 2))
    ax7 = plt.subplot2grid((3, 3), (2, 0), colspan=2)
    ax8 = plt.subplot2grid((3, 3), (2, 2))

    for ax in fig.get_axes():
        if ax in [ax1, ax2, ax3, ax5, ax6]:
            ax.axis("off")
            
    # --- Your entire plotting logic from the dashboard.py file ---

    # -- Plot for Axis 1 --
    color1 = "crimson"
    color2 = "navy"
    total_minutes = str(total_minutes_streamed.values[0][0])
    ax1.text(0.45, 0.70, "Total Minutes Streamed", fontweight="bold", fontsize=35, color=color1, fontfamily="serif", ha="center")
    ax1.text(0.52, 0.45, total_minutes, fontweight="bold", fontsize=160, color=color2, fontfamily="serif", ha="center", va="center")

    # -- Plot for Axis 2 --
    artists_listened = artists_listened_to.values[0][0]
    ax2.text(0.45, 0.70, "Total Artists Streamed", fontweight="bold", fontsize=35, color=color1, fontfamily="serif", ha="center")
    ax2.text(0.52, 0.45, artists_listened, fontweight="bold", fontsize=160, color=color2, fontfamily="serif", ha="center", va="center")

    # -- Plot for Axis 3 --
    tracks_no = tracks_listened_to.values[0][0]
    ax3.text(0.45, 0.70, "Total Tracks Streamed", fontweight="bold", fontsize=35, color=color1, fontfamily="serif", ha="center")
    ax3.text(0.52, 0.45, tracks_no, fontweight="bold", fontsize=160, color=color2, fontfamily="serif", ha="center", va="center")

    # -- Plot for Axis 4 --
    ax4.set_title("Most Streamed Artists", fontweight="bold", fontsize=35, color=color1, fontfamily="serif")
    sns.barplot(y="artist_name", x="streams", data=most_streamed_artists.head(), palette=colors, ax=ax4)
    ax4.set_xlabel("Streams", fontsize=24, fontweight="bold", labelpad=10)
    ax4.set_ylabel("Artist Name", fontsize=24, fontweight="bold", labelpad=10)
    ax4.tick_params(axis="y", labelsize=12, labelcolor="black")
    ax4.tick_params(axis="x", labelsize=12, labelcolor="black")
    ax4.spines["top"].set_visible(False)
    ax4.spines["right"].set_visible(False)
    ax4.set_yticklabels(ax4.get_yticklabels(), fontsize=16, fontweight="bold", fontfamily="serif")

    # -- Plot for Axis 5 --
    table = ax5.table(cellText=newly_discovered_tracks.head(10).values, colLabels=["Track Name"], loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(18)
    table.scale(1, 2)
    for cell in table._cells:
        table._cells[cell].set_text_props(weight="bold", ha="left")
    header_cells = table._cells[(0, 0)]
    header_cells.set_text_props(weight="bold", ha="center")
    header_cells.set_color("lightgray")
    ax5.set_title("Discovered Tracks this week", fontweight="bold", fontsize=35, color=color1, fontfamily="serif")

    # -- Plot for Axis 6 --
    table = ax6.table(cellText=newly_discovered_artists.head(10).values, colLabels=["Artist Name"], loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(18)
    table.scale(1, 2)
    for cell in table._cells:
        table._cells[cell].set_text_props(weight="bold", ha="left")
    header_cells = table._cells[(0, 0)]
    header_cells.set_text_props(weight="bold", ha="center")
    header_cells.set_color("lightgray")
    ax6.set_title("Discovered Artists this week", fontweight="bold", fontsize=35, color=color1, fontfamily="serif")

    # -- Plot for Axis 7 --
    dow_mapping = {0: "Sunday", 1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday", 6: "Saturday"}
    tracks_per_dow["day_of_week"] = tracks_per_dow["day_of_week"].replace(dow_mapping)
    df = pd.crosstab(
        index=tracks_per_dow["day_of_week"],
        columns=tracks_per_dow["hour"].astype("int"),
        values=tracks_per_dow["total_minutes"],
        aggfunc="sum"
    ).fillna(0)
    sns.heatmap(df, square=True, linewidth=2.5, cbar=False, cmap=cmap, ax=ax7)
    ax7.set_title("Listening Habits by Day and Hour", fontweight="bold", fontsize=35, color=color1, fontfamily="serif")
    ax7.set_xlabel("Hour", fontsize=24, fontweight="bold")
    ax7.set_ylabel("Day of the Week", fontsize=24, fontweight="bold")
    ax7.set_yticklabels(ax7.get_yticklabels(), fontsize=12, fontweight="bold", fontfamily="serif")
    ax7.set_xticklabels(ax7.get_xticklabels(), fontsize=16, fontweight="bold", fontfamily="serif")
    ax7.spines["top"].set_visible = False

    # -- Plot for Axis 8 --
    sns.barplot(y="track_name", x="streams", data=most_streamed_songs.head(), palette=colors, ax=ax8)
    ax8.set_xlabel("Streams", fontsize=24, fontweight="bold")
    ax8.set_ylabel("Track Name", fontsize=24, fontweight="bold")
    ax8.set_yticklabels(ax8.get_yticklabels(), fontsize=16, fontweight="bold", fontfamily="serif")
    num_ticks = len(most_streamed_songs["streams"].head()) + 2
    ax8.set_xticks(range(num_ticks))
    ax8.set_xticklabels([int(x) for x in ax8.get_xticks()], fontsize=16, fontweight="bold", fontfamily="serif")
    ax8.set_title("Most Played Song this week", fontweight="bold", fontsize=35, color=color1, fontfamily="serif")
        
    # --- Save the final figure ---
    plt.suptitle("Your Spotify Wrapped for the Last Week", fontweight="bold", fontsize=55, color="black", fontfamily="serif")
    plt.tight_layout()
    fig.savefig(output_path)
    
    logging.info(f"Dashboard image saved to {output_path}")