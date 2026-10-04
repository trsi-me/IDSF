from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Tuple, List, Optional
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline


def build_preprocessing_pipeline(df: pd.DataFrame, label_column: str = 'label') -> Tuple[Pipeline, List[str]]:
    """إنشاء بايبلاين معالجة مسبقة: ترميز للأصناف وتطبيع للأرقام.

    يعيد البايبلاين وقائمة أعمدة الميزات المستخدمة.
    """
    features = [c for c in df.columns if c != label_column]
    cat_cols = [c for c in features if df[c].dtype == 'object']
    num_cols = [c for c in features if c not in cat_cols]

    numeric_transformer = StandardScaler()
    categorical_transformer = OneHotEncoder(handle_unknown='ignore', sparse=False)

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, num_cols),
            ('cat', categorical_transformer, cat_cols),
        ]
    )

    pipeline = Pipeline(steps=[('pre', preprocessor)])
    return pipeline, features


def clean_dataframe(df: pd.DataFrame, label_column: str = 'label') -> pd.DataFrame:
    """تنظيف بسيط: إزالة القيم المفقودة والأسطر المكررة."""
    if label_column in df.columns:
        df = df.dropna(subset=[label_column])
    df = df.dropna()
    df = df.drop_duplicates()
    return df


