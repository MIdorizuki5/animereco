import streamlit as st
import pandas as pd
import pickle
from google.cloud import storage

# Instantiate a Google Cloud Storage client
storage_client = storage.Client()

# Define a function to load a CSV file from Google Cloud Storage into a pandas dataframe
def load_csv_from_gcs(bucket_name, blob_name):
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    s = blob.download_as_text()
    return pd.read_csv(StringIO(s))

# Define a function to load a pickle file from Google Cloud Storage
def load_pickle_from_gcs(bucket_name, blob_name):
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    s = blob.download_as_bytes()
    return pickle.loads(s)

# Load the data and models from Google Cloud Storage
bucket_name = "anime-reco"

AnimesDF = load_csv_from_gcs(bucket_name, "anime_cleaned.csv")
loaded_model = load_pickle_from_gcs(bucket_name, "baseline_model.pickle")
loaded_knn_model = load_pickle_from_gcs(bucket_name, "knn_model.pickle")

def get_item_recommendations(algo, algo_items, anime_title, anime_id=100000, k=10):
    anime_title = anime_title.strip().lower()
    matching_animes = AnimesDF[AnimesDF['title'].str.lower() == anime_title]

    if matching_animes.empty:
        st.write("No matching anime found. Please check your input.")
        return

    if anime_id == 100000:
        anime_id = matching_animes['anime_id'].iloc[0]

    iid = algo_items.trainset.to_inner_iid(anime_id)
    neighbors = algo_items.get_neighbors(iid, k=k)
    raw_neighbors = (algo.trainset.to_raw_iid(inner_id) for inner_id in neighbors)
    st.write("Here's a list of anime titles you might enjoy")
    df = pd.DataFrame(raw_neighbors, columns = ['Anime_ID'])
    df = pd.merge(df, AnimesDF, left_on = 'Anime_ID', right_on = 'anime_id', how = 'left')
    return df[['Anime_ID', 'title', 'genre']]

# Set up the Streamlit interface
st.title('Anime Recommendation System')

anime_title = st.text_input('Please enter an anime title')

if st.button('Get recommendations'):
    recommendations = get_item_recommendations(loaded_model, loaded_knn_model, anime_title)
    st.write(recommendations)