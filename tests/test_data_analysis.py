import pandas as pd
import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data_analysis import clean_data, analyse

# some fake data to use in the tests
@pytest.fixture
def sample_df():
    data = {
        "Diet_type":    ["Paleo", "Paleo", "Keto", "Keto", "Keto", "Vegan", "Vegan"],
        "Recipe_name":  ["Recipe A", "Recipe B", "Recipe C", "Recipe D", "Recipe E", "Recipe F", "Recipe G"],
        "Cuisine_type": ["american", "mexican", "american", "american", "italian", "indian", "french"],
        "Protein(g)":   [30.0, 50.0, 20.0, 80.0, 60.0, 10.0, 15.0],
        "Carbs(g)":     [10.0, 20.0, 5.0, 15.0, 10.0, 40.0, 30.0],
        "Fat(g)":       [15.0, 25.0, 30.0, 40.0, 20.0, 5.0, 8.0],
    }
    return pd.DataFrame(data)


# data with some missing values to test the cleaning function
@pytest.fixture
def dirty_df():
    data = {
        "Diet_type":    ["Paleo", "Keto", "Vegan"],
        "Recipe_name":  ["R1", "R2", "R3"],
        "Cuisine_type": ["american", "italian", "french"],
        "Protein(g)":   [30.0, None, 10.0],
        "Carbs(g)":     [10.0, 5.0, None],
        "Fat(g)":       [None, 30.0, 5.0],
    }
    return pd.DataFrame(data)


class TestCleanData:
    def test_no_nulls_after_cleaning(self, dirty_df):
        cleaned = clean_data(dirty_df)
        assert cleaned[["Protein(g)", "Carbs(g)", "Fat(g)"]].isnull().sum().sum() == 0

    def test_missing_protein_filled_with_mean(self, dirty_df):
        # keto row has no protein value, should be filled with mean of the other two
        expected_mean = dirty_df["Protein(g)"].mean()
        cleaned = clean_data(dirty_df.copy())
        assert cleaned.loc[1, "Protein(g)"] == pytest.approx(expected_mean)

    def test_handles_string_values(self):
        # sometimes the csv has "N/A" or other strings in numeric columns
        # use two rows so the mean can actually be calculated
        df = pd.DataFrame({
            "Diet_type":    ["Paleo", "Paleo"],
            "Recipe_name":  ["R1", "R2"],
            "Cuisine_type": ["american", "american"],
            "Protein(g)":   ["N/A", 20.0],
            "Carbs(g)":     [5.0, 5.0],
            "Fat(g)":       [3.0, 3.0],
        })
        cleaned = clean_data(df)
        assert not np.isnan(cleaned.loc[0, "Protein(g)"])


class TestAnalyse:
    def test_returns_correct_number_of_diet_types(self, sample_df):
        avg_macros, *_ = analyse(sample_df.copy())
        # we have 3 diet types in our test data
        assert avg_macros.shape == (3, 3)

    def test_average_protein_is_correct(self, sample_df):
        avg_macros, *_ = analyse(sample_df.copy())
        # paleo has protein values 30 and 50, so average should be 40
        expected = (30.0 + 50.0) / 2
        assert avg_macros.loc["Paleo", "Protein(g)"] == pytest.approx(expected)

    def test_keto_has_highest_protein(self, sample_df):
        _, _, best_diet, _ = analyse(sample_df.copy())
        # keto average is (20+80+60)/3 = 53.3 which is the highest
        assert best_diet == "Keto"

    def test_most_common_cuisine_keto(self, sample_df):
        _, _, _, common_cuisine = analyse(sample_df.copy())
        # keto has american twice and italian once so american wins
        assert common_cuisine["Keto"] == "american"

    def test_ratio_columns_added(self, sample_df):
        df = sample_df.copy()
        analyse(df)
        assert "Protein_to_Carbs_ratio" in df.columns
        assert "Carbs_to_Fat_ratio" in df.columns

    def test_top_protein_no_more_than_5(self, sample_df):
        _, top_protein, *_ = analyse(sample_df.copy())
        counts = top_protein.groupby("Diet_type").size()
        assert (counts <= 5).all()
