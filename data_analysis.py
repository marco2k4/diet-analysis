import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json


CSV_PATH = os.environ.get("CSV_PATH", "All_Diets.csv")


def load_data(path=CSV_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(f"cant find the csv file at: {path}")
    df = pd.read_csv(path)
    return df


def clean_data(df):
    # convert protein/carbs/fat to numbers in case there's any weird string values
    for col in ["Protein(g)", "Carbs(g)", "Fat(g)"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # fill any missing values with the average of that column
    df.fillna(df.select_dtypes(include="number").mean(), inplace=True)
    return df


def analyse(df):
    # get average protein, carbs, fat for each diet type
    avg_macros = df.groupby("Diet_type")[["Protein(g)", "Carbs(g)", "Fat(g)"]].mean()

    # find top 5 highest protein recipes in each diet type
    top_protein = (
        df.sort_values("Protein(g)", ascending=False)
        .groupby("Diet_type")
        .head(5)
    )

    # which diet type has the highest protein overall
    best_protein_diet = avg_macros["Protein(g)"].idxmax()

    # most common cuisine for each diet type
    common_cuisine = (
        df.groupby("Diet_type")["Cuisine_type"]
        .agg(lambda x: x.value_counts().index[0])
    )

    # add ratio columns
    df["Protein_to_Carbs_ratio"] = df["Protein(g)"] / df["Carbs(g)"].replace(0, float("nan"))
    df["Carbs_to_Fat_ratio"] = df["Carbs(g)"] / df["Fat(g)"].replace(0, float("nan"))

    return avg_macros, top_protein, best_protein_diet, common_cuisine


def plot(avg_macros, top_protein, out_dir="outputs"):
    os.makedirs(out_dir, exist_ok=True)

    # bar chart for average macros
    avg_macros.plot(kind="bar", figsize=(12, 6))
    plt.title("Average Macronutrient Content by Diet Type")
    plt.ylabel("Amount (g)")
    plt.tight_layout()
    plt.savefig(f"{out_dir}/avg_macros_bar.png")
    plt.close()

    # heatmap to see the relationship between macros and diet types
    plt.figure(figsize=(10, 6))
    sns.heatmap(avg_macros, annot=True, fmt=".1f", cmap="YlOrRd")
    plt.title("Macronutrient Heatmap by Diet Type")
    plt.tight_layout()
    plt.savefig(f"{out_dir}/macros_heatmap.png")
    plt.close()

    # scatter plot for top protein recipes
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=top_protein, x="Protein(g)", y="Fat(g)", hue="Cuisine_type")
    plt.title("Top 5 Protein-Rich Recipes by Cuisine")
    plt.tight_layout()
    plt.savefig(f"{out_dir}/top_protein_scatter.png")
    plt.close()


def main():
    df = load_data()
    df = clean_data(df)
    avg_macros, top_protein, best_protein_diet, common_cuisine = analyse(df)

    print("Average macronutrients per diet type:")
    print(avg_macros.to_string())
    print(f"\nDiet type with highest average protein: {best_protein_diet}")
    print("\nMost common cuisine per diet type:")
    print(common_cuisine.to_string())

    # save results to json file (simulating nosql storage)
    summary = avg_macros.reset_index().to_dict(orient="records")
    os.makedirs("outputs", exist_ok=True)
    with open("outputs/summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    plot(avg_macros, top_protein)
    print("\ndone, charts saved to outputs folder")


if __name__ == "__main__":
    main()
