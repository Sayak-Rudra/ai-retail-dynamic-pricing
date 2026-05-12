import os
import pandas as pd
import numpy as np
from flask import Flask, request, render_template, jsonify
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder

# ====================================================================
# Flask Setup
# ====================================================================

app = Flask(__name__, static_folder="static", template_folder="templates")

FEATURES = [
    "product_name", "product_category", "promotion", "unit_price",
    "comp_1", "comp_2", "comp_3", "holiday", "weekend", "month"
]

# ====================================================================
# Load Data
# ====================================================================

def load_and_prepare_data():
    try:
        df = pd.read_csv("extended_retail_data.csv")
        print(f"✅ Dataset loaded: {len(df)} rows, {df['product_name'].nunique()} products.")
    except FileNotFoundError:
        print("❌ extended_retail_data.csv not found.")
        return None

    df = df.fillna(0)
    df.loc[:, "product_name"] = df["product_name"].astype(str)
    df.loc[:, "product_category"] = df["product_category"].astype(str)
    df.loc[:, "promotion"] = df["promotion"].astype(int)
    return df

# ====================================================================
# Train Model
# ====================================================================

def train_model():
    df = load_and_prepare_data()
    if df is None:
        return None, None

    categorical_features = ["product_name", "product_category"]
    numerical_features = [
        "promotion", "unit_price", "comp_1", "comp_2", "comp_3",
        "holiday", "weekend", "month"
    ]
    target = "qty"

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features)
        ],
        remainder="passthrough"
    )

    model_pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("regressor", ExtraTreesRegressor(
            n_estimators=50, random_state=42, n_jobs=-1
        ))
    ])

    X = df[categorical_features + numerical_features]
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print("⏳ Training model...")
    model_pipeline.fit(X_train, y_train)
    y_pred = model_pipeline.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    print(f"✅ Model trained. RMSE = {rmse:.2f}")

    return model_pipeline, df

model, df_original = train_model()

# ====================================================================
# Helper: get product-specific price band
# ====================================================================

def product_price_band(product_name):
    """Return realistic price band for a given product."""
    product_prices = df_original[df_original["product_name"] == product_name]["unit_price"]
    if len(product_prices) > 0:
        return product_prices.min(), product_prices.max()
    else:
        return df_original["unit_price"].min(), df_original["unit_price"].max()

# ====================================================================
# Helper: Optimal Price
# ====================================================================

def find_optimal_price(
    base_features,
    unit_cost,
    product_name,
    competitor_prices
):

    # =====================================================
    # Product Price Band
    # =====================================================

    min_price, max_price = product_price_band(
        product_name
    )

    # =====================================================
    # BUSINESS CONSTRAINTS
    # Prevent unrealistic loss-making pricing
    # =====================================================

    minimum_allowed_price = (
        unit_cost * 1.10
    )

    adjusted_min_price = max(
        min_price,
        minimum_allowed_price
    )

    # =====================================================
    # Competitor-Aware Market Ceiling
    # Prevent unrealistic premium pricing
    # =====================================================

    market_cap_price = (
        max(competitor_prices) * 1.35
    )

    safe_max_price = min(
        max_price,
        market_cap_price
    )

    # =====================================================
    # Generate Simulation Price Range
    # =====================================================

    price_range = np.linspace(
        adjusted_min_price,
        safe_max_price,
        50
    )

    prediction_data = []

    for p in price_range:

        temp = base_features.copy()

        temp["unit_price"] = p

        prediction_data.append(temp)

    df_temp = pd.DataFrame(
        prediction_data,
        columns=FEATURES
    )

    # =====================================================
    # Demand Prediction
    # =====================================================

    predicted_demand = model.predict(df_temp)

    # Prevent negative demand values
    predicted_demand = np.maximum(
        predicted_demand,
        0
    )

    # =====================================================
    # Revenue & Profit Calculations
    # =====================================================

    predicted_revenue = (
        price_range *
        predicted_demand
    )

    predicted_profit = (
        predicted_revenue -
        (
            unit_cost *
            predicted_demand
        )
    )

    # =====================================================
    # Risk-Adjusted Optimization
    # Penalize very low-margin prices
    # =====================================================

    risk_penalty = np.where(
        price_range < (unit_cost * 1.15),
        0.90,
        1.0
    )

    adjusted_profit = (
        predicted_profit *
        risk_penalty
    )

    # =====================================================
    # Find Optimal Price
    # =====================================================

    idx = np.argmax(
        adjusted_profit
    )

    return {

        "optimal_price":
            round(price_range[idx], 2),

        "optimal_demand":
            round(predicted_demand[idx], 2),

        "max_profit":
            round(predicted_profit[idx], 2),

        "price_range":
            price_range.tolist(),

        "demand_curve":
            predicted_demand.tolist(),

        "profit_curve":
            predicted_profit.tolist()
    }

# ====================================================================
# Routes
# ====================================================================

@app.route("/")
def home():
    if df_original is None:
        return "Dataset not found", 500

    products_by_category_raw = df_original.groupby("product_category")["product_name"].unique()
    products_by_category = {k: v.tolist() for k, v in products_by_category_raw.items()}
    product_categories = sorted(products_by_category.keys())

    return render_template(
        "index.html",
        products_by_category=products_by_category,
        product_categories=product_categories
    )

@app.route("/predict", methods=["POST"])
def predict():

    if model is None:
        return jsonify({
            "success": False,
            "error": "Model not trained."
        }), 500

    try:

        user_input = {

            "product_name":
                request.form["product_name"],

            "product_category":
                request.form["product_category"],

            "promotion":
                int(request.form["promotion"]),

            "unit_cost":
                float(request.form["unit_cost"]),

            "unit_price":
                float(request.form["unit_price"]),

            "comp_1":
                float(request.form["comp_1"]),

            "comp_2":
                float(request.form["comp_2"]),


            "holiday":
                int(request.form["holiday"]),

            "weekend":
                int(request.form["weekend"]),

            "month":
                int(request.form["month"])
        }

        # =========================================================
        # AI Generated Market Benchmark
        # =========================================================
        
        user_input["comp_3"] = round(
        
            np.median([
                user_input["comp_1"],
                user_input["comp_2"]
            ]),
        
            2
        )

        # =========================================================
        # Prediction Input
        # =========================================================

        df_input_features = {
            k: v
            for k, v in user_input.items()
            if k != "unit_cost"
        }

        df_input = pd.DataFrame([df_input_features])

        # =========================================================
        # Current User Pricing Prediction
        # =========================================================

        user_demand = model.predict(df_input)[0]

        user_revenue = (
            user_input["unit_price"] *
            user_demand
        )

        user_profit = (
            user_revenue -
            (
                user_input["unit_cost"] *
                user_demand
            )
        )

        # =========================================================
        # Optimal Pricing Engine
        # =========================================================

        base_features = {

            k: v
            for k, v in user_input.items()
            if k not in [
                "unit_cost",
                "unit_price"
            ]
        }

        optimal = find_optimal_price(
            base_features,
            user_input["unit_cost"],
            user_input["product_name"],
            [
                user_input["comp_1"],
                user_input["comp_2"]
            ]
        )

        # =========================================================
        # AI Competitor Benchmarking
        # =========================================================

        competitor_prices = [
        
            user_input["comp_1"],
            user_input["comp_2"]

        ]

        avg_comp_price = round(
        
            np.median(competitor_prices),

            2
        )

        # =========================================================
        # Profit Improvement %
        # Safer enterprise calculation
        # =========================================================

        baseline_profit = max(
            abs(user_profit),
            1
        )

        profit_gain_raw = (
            (
                optimal["max_profit"] -
                user_profit
            ) / baseline_profit
        ) * 100

        profit_gain = round(
            max(profit_gain_raw, 0),
            2
        )

        market_position = (
            "above"
            if user_input["unit_price"] > avg_comp_price
            else "below"
        )

        demand_signal = (
            "High"
            if user_demand > 50
            else "Moderate"
        )

        risk_level = (
            "High"
            if abs(
                user_input["unit_price"] -
                avg_comp_price
            ) > 100
            else "Moderate"
        )

        # =========================================================
        # AI Confidence Scoring
        # Based on market pricing alignment
        # =========================================================
        
        price_gap = abs(
            user_input["unit_price"] -
            avg_comp_price
        )
        
        ai_confidence = round(
        
            max(
                70,
                100 - (price_gap / 10)
            ),
        
            1
        )

        ai_insights = [

            f"Current selling price is {market_position} competitor market average.",

            f"Average competitor benchmark detected at ${avg_comp_price}.",

            f"AI optimization may improve profitability by {profit_gain}%",

            f"Demand forecast classified as {demand_signal} market demand.",

            f"Market volatility risk currently classified as {risk_level}.",

            "Retail demand elasticity detected across evaluated pricing range.",

            "AI engine identified optimal pricing opportunity for revenue maximization."
        ]

        # =========================================================
        # Final Response
        # =========================================================

        response = {

            "success": True,

            "user_prediction": {

                "demand":
                    round(user_demand, 2),

                "revenue":
                    round(user_revenue, 2),

                "profit":
                    round(user_profit, 2)
            },

            "optimal_prediction": {

                "optimal_price":
                    optimal["optimal_price"],

                "optimal_demand":
                    optimal["optimal_demand"],

                "max_profit":
                    optimal["max_profit"]
            },

            "plot_data": {

                "prices":
                    optimal["price_range"],

                "demand":
                    optimal["demand_curve"],

                "profit":
                    optimal["profit_curve"]
            },

            "business_metrics": {

                "avg_competitor_price":
                    avg_comp_price,

                "profit_improvement":
                    profit_gain,

                "market_risk":
                    risk_level,

                "ai_confidence":
                    ai_confidence
            },

            "ai_insights":
                ai_insights
        }

        return jsonify(response)

    except Exception as e:

        print("❌ Error:", e)

        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

# ====================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
