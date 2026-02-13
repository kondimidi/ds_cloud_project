import os
import zipfile
from kaggle.api.kaggle_api_extended import KaggleApi


def download_dataset(dataset_name, download_path):
    """Pobiera dane z Kaggle i rozpakowuje je do folderu data/"""
    api = KaggleApi()
    api.authenticate()

    print(f"Pobieranie zbioru {dataset_name}...")
    api.dataset_download_files(dataset_name, path=download_path, unzip=True)
    print("Gotowe!")


if __name__ == "__main__":
    # Przykład: dane o cenach domów (House Prices)
    DATASET = 'syedanwarafridi/vehicle-sales-data'  # Możesz tu wpisać dowolny slug z Kaggle
    PATH = './data'

    if not os.path.exists(PATH):
        os.makedirs(PATH)

    download_dataset(DATASET, PATH)