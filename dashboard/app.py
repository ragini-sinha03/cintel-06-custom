import pandas as pd
import plotly.express as px
from shinywidgets import render_plotly, render_widget, output_widget
from shiny import reactive, render, req
from shiny.express import input, ui, render
from collections import deque
from datetime import datetime
import random
import os

# Check if the file exists and is not empty
if os.path.exists('healthexp.csv') and os.path.getsize('healthexp.csv') > 0:
    # Define column names if the CSV file does not have headers
    column_names = ['age', 'gender', 'expenditure', 'smoker', 'region', 'timestamp']
    
    # Load the healthcare expenditure dataset
    healthexp = pd.read_csv('healthexp.csv', names=column_names, skip_blank_lines=True)
    
    # Check the first few rows of the dataset
    print(healthexp.head())
else:
    print("Error: The CSV file does not exist or is empty.")
    healthexp = pd.DataFrame(columns=['age', 'gender', 'expenditure', 'smoker', 'region', 'timestamp'])

UPDATE_INTERVAL_SECS: int = 10
DEQUE_SIZE: int = 10
reactive_value_wrapper = reactive.value(deque(maxlen=DEQUE_SIZE))

# Page title
ui.page_opts(title="Healthcare Expenditure Dashboard", fillable=True)

# Sidebar with Inputs
with ui.sidebar(open="open"):
    ui.h5("Filters and Options")

    # Filter for gender
    ui.input_checkbox_group(
        "selected_gender",
        "Select Gender",
        ["Male", "Female"],
        selected=["Male", "Female"],
        inline=True
    )

    # Filter for smoker status
    ui.input_checkbox_group(
        "selected_smoker",
        "Smoker?",
        ["Yes", "No"],
        selected=["Yes", "No"],
        inline=True
    )

    # Range slider for healthcare expenditure
    ui.input_slider("expenditure_range", "Expenditure Range ($)", 0, 5000, (500, 3000))

    # Range slider for age group
    ui.input_slider("age_range", "Age Group", 18, 100, (25, 60))

# Metrics Section
with ui.layout_columns(fill=False):
    # Total expenditure for smokers
    with ui.value_box(
        showcase="fa-smoker",  # You can use any suitable icon
        theme="bg-gradient-pink-purple", height=200
    ):
        "Smokers' Total Expenditure"
        @render.text
        def display_smoker_exp():
            _, df, _ = reactive_health_data_combined()
            if df is not None:  # Ensure that df is valid before using it
                return f"${df[df['smoker'] == 'Yes']['expenditure'].sum():.2f}"
            return "$0.00"  # Fallback in case df is None

    # Total expenditure for non-smokers
    with ui.value_box(
        showcase="fa-non-smoker",  # You can use any suitable icon
        theme="bg-gradient-blue-green", height=200
    ):
        "Non-Smokers' Total Expenditure"
        @render.text
        def display_nonsmoker_exp():
            _, df, _ = reactive_health_data_combined()
            if df is not None:  # Ensure that df is valid before using it
                return f"${df[df['smoker'] == 'No']['expenditure'].sum():.2f}"
            return "$0.00"  # Fallback in case df is None

# Data Table and Visualizations
with ui.layout_columns(fill=False):
    # Data Table
    with ui.card():
        "Filtered Healthcare Expenditure Data"
        @render.data_frame
        def health_df():
            return render.DataTable(filtered_health_data(), selection_mode='row')

    # Scatterplot with regression line
    with ui.card(full_screen=True):
        ui.card_header("Scatterplot: Age vs Expenditure")
        @render_plotly
        def scatterplot_with_regression():
            filtered = filtered_health_data()
            fig = px.scatter(
                filtered,
                x="age",
                y="expenditure",
                color="gender",
                trendline="ols",
                labels={"age": "Age", "expenditure": "Expenditure ($)"},
                title="Scatterplot: Age vs Expenditure with Regression"
            )
            return fig

    # Heatmap for age vs expenditure
    with ui.card(full_screen=True):
        ui.card_header("Heatmap: Age vs Expenditure")
        @render_plotly
        def heatmap_age_vs_expenditure():
            filtered = filtered_health_data()
            fig = px.density_heatmap(
                filtered,
                x="age",
                y="expenditure",
                color_continuous_scale="Viridis",
                labels={"age": "Age", "expenditure": "Expenditure ($)"},
                title="Heatmap: Age vs Expenditure"
            )
            return fig

# Tabbed Trend Charts
with ui.navset_pill(id="tabbed_graphs"):
    # Smokers' Expenditure Trend Chart
    with ui.nav_panel("Smokers Trend"):
        @render_plotly
        def smokers_trend_chart():
            _, df, _ = reactive_health_data_combined()
            if not df.empty:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                return px.line(
                    df[df['smoker'] == 'Yes'],
                    x="timestamp",
                    y="expenditure",
                    line_shape="spline",
                    title="Smokers' Expenditure Over Time",
                    labels={"timestamp": "Time", "expenditure": "Expenditure ($)"},
                    color_discrete_sequence=["pink"]
                )

    # Non-Smokers' Expenditure Trend Chart
    with ui.nav_panel("Non-Smokers Trend"):
        @render_plotly
        def nonsmokers_trend_chart():
            _, df, _ = reactive_health_data_combined()
            if not df.empty:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                return px.line(
                    df[df['smoker'] == 'No'],
                    x="timestamp",
                    y="expenditure",
                    line_shape="spline",
                    title="Non-Smokers' Expenditure Over Time",
                    labels={"timestamp": "Time", "expenditure": "Expenditure ($)"},
                    color_discrete_sequence=["blue"]
                )

# Reactive Functions
@reactive.calc
def filtered_health_data():
    req(input.selected_gender(), input.selected_smoker())
    filtered_data = healthexp[
        (healthexp["gender"].isin(input.selected_gender())) & 
        (healthexp["smoker"].isin(input.selected_smoker())) & 
        (healthexp["expenditure"].between(*input.expenditure_range())) & 
        (healthexp["age"].between(*input.age_range()))
    ]
    return filtered_data

def reactive_health_data_combined():
    reactive.invalidate_later(UPDATE_INTERVAL_SECS)
    # Generate random new data points to simulate dynamic updates
    expenditure_value_smokers = round(random.uniform(100, 5000), 1)
    expenditure_value_nonsmokers = round(random.uniform(100, 5000), 1)
    timestamp_value = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_entry = {"expenditure": expenditure_value_smokers if random.choice(['Yes', 'No']) == 'Yes' else expenditure_value_nonsmokers, "timestamp": timestamp_value, "smoker": random.choice(['Yes', 'No'])}
    reactive_value_wrapper.get().append(new_entry)
    deque_snapshot = reactive_value_wrapper.get()
    df = pd.DataFrame(deque_snapshot)
    return deque_snapshot, df, new_entry
