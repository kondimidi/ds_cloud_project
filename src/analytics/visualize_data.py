import matplotlib.pyplot as plt
import seaborn as sns
import os
import pandas as pd

def create_visualizations(df):
    print("Generating charts...")
    plt.figure(figsize=(12, 6))

    # 1. Top 10 brands in terms of average selling price
    top_makes = df.groupby('make')['sellingprice'].mean().sort_values(ascending=False).head(10)

    sns.barplot(x=top_makes.index, y=top_makes.values, palette='viridis')

    plt.title('Top 10 Most Expensive Car Makes (Average Sale Price)')
    plt.xticks(rotation=45)
    plt.ylabel('Price (USD)')
    plt.xlabel('Make')

    # Creating directory for reports if it doesn'y exist
    os.makedirs('reports', exist_ok=True)

    # Saving chart to a file
    plt.tight_layout()
    plt.savefig('reports/top_makes_prices.png')
    print("Chart saved to reports/top_makes_prices.png")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    df = pd.read_csv('data/car_prices.csv')
    create_visualizations(df)