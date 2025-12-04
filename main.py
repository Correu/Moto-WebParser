'''
    main python file containing all the user interface aspects of the program
    Displays injury data in an interactive table with searchable filters
'''
import pandas as pd
import dash
from dash import dcc, html, dash_table, Input, Output
from datetime import datetime

# Load the injury data
def load_data():
    """Load and preprocess the injury data from CSV"""
    try:
        df = pd.read_csv('updated_data.csv')
        # Parse date column and extract year and month
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Year'] = df['Date'].dt.year
        df['Month'] = df['Date'].dt.month
        df['MonthName'] = df['Date'].dt.strftime('%B')
        # Clean up the data - remove rows with invalid dates
        df = df.dropna(subset=['Date'])
        return df
    except FileNotFoundError:
        print("Error: updated_data.csv not found. Please run the data processing function first.")
        return pd.DataFrame()

# Initialize the Dash app
app = dash.Dash(__name__)
app.title = "Moto Injury Data Viewer"

# Load data
df = load_data()

# Get unique values for filters
if not df.empty:
    years = sorted(df['Year'].dropna().unique(), reverse=True)
    months = sorted(df['Month'].dropna().unique())
    month_names = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 
                   5: 'May', 6: 'June', 7: 'July', 8: 'August', 
                   9: 'September', 10: 'October', 11: 'November', 12: 'December'}
    injuries = sorted(df['Injury'].dropna().unique())
    tracks = sorted(df['Track'].dropna().unique())
else:
    years = months = injuries = tracks = []

# Define the layout
app.layout = html.Div([
    html.Div([
        html.H1("Moto Injury Data Viewer", style={'textAlign': 'center', 'marginBottom': '30px'}),
        
        html.Div([
            html.Div([
                html.Label("Year:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                dcc.Dropdown(
                    id='year-filter',
                    options=[{'label': 'All Years', 'value': 'all'}] + [{'label': str(year), 'value': year} for year in years],
                    value='all',
                    clearable=False,
                    style={'width': '100%'}
                ),
            ], style={'width': '24%', 'display': 'inline-block', 'marginRight': '1%', 'verticalAlign': 'top'}),
            
            html.Div([
                html.Label("Month:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                dcc.Dropdown(
                    id='month-filter',
                    options=[{'label': 'All Months', 'value': 'all'}] + [{'label': month_names.get(m, f'Month {m}'), 'value': m} for m in months],
                    value='all',
                    clearable=False,
                    style={'width': '100%'}
                ),
            ], style={'width': '24%', 'display': 'inline-block', 'marginRight': '1%', 'verticalAlign': 'top'}),
            
            html.Div([
                html.Label("Injury Type:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                dcc.Dropdown(
                    id='injury-filter',
                    options=[{'label': 'All Injuries', 'value': 'all'}] + [{'label': injury, 'value': injury} for injury in injuries],
                    value='all',
                    clearable=False,
                    searchable=True,
                    style={'width': '100%'}
                ),
            ], style={'width': '24%', 'display': 'inline-block', 'marginRight': '1%', 'verticalAlign': 'top'}),
            
            html.Div([
                html.Label("Location (Track):", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                dcc.Dropdown(
                    id='track-filter',
                    options=[{'label': 'All Tracks', 'value': 'all'}] + [{'label': track, 'value': track} for track in tracks],
                    value='all',
                    clearable=False,
                    searchable=True,
                    style={'width': '100%'}
                ),
            ], style={'width': '24%', 'display': 'inline-block', 'verticalAlign': 'top'}),
        ], style={'marginBottom': '20px', 'padding': '20px', 'backgroundColor': '#f0f0f0', 'borderRadius': '5px'}),
        
        html.Div(id='results-count', style={'marginBottom': '10px', 'fontSize': '16px', 'fontWeight': 'bold'}),
        
        html.Div([
            dash_table.DataTable(
                id='injury-table',
                columns=[
                    {'name': 'Rider', 'id': 'Rider', 'type': 'text'},
                    {'name': 'Injury', 'id': 'Injury', 'type': 'text'},
                    {'name': 'Track', 'id': 'Track', 'type': 'text'},
                    {'name': 'Date', 'id': 'Date', 'type': 'datetime', 'format': {'specifier': '%Y-%m-%d'}},
                ],
                data=[],
                page_size=50,
                sort_action='native',
                filter_action='native',
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px',
                    'fontFamily': 'Arial, sans-serif',
                    'fontSize': '14px',
                    'minWidth': '100px',
                },
                style_header={
                    'backgroundColor': '#2c3e50',
                    'color': 'white',
                    'fontWeight': 'bold',
                    'textAlign': 'center',
                },
                style_data={
                    'backgroundColor': 'white',
                    'color': 'black',
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#f8f9fa',
                    }
                ],
            )
        ], style={'marginTop': '20px'}),
    ], style={'maxWidth': '1400px', 'margin': '0 auto', 'padding': '20px'})
])

# Define the callback to update the table
@app.callback(
    [Output('injury-table', 'data'),
     Output('results-count', 'children')],
    [Input('year-filter', 'value'),
     Input('month-filter', 'value'),
     Input('injury-filter', 'value'),
     Input('track-filter', 'value')]
)
def update_table(year_filter, month_filter, injury_filter, track_filter):
    """Filter the data based on selected filters"""
    if df.empty:
        return [], "No data available. Please ensure updated_data.csv exists."
    
    filtered_df = df.copy()
    
    # Apply filters
    if year_filter != 'all':
        filtered_df = filtered_df[filtered_df['Year'] == year_filter]
    
    if month_filter != 'all':
        filtered_df = filtered_df[filtered_df['Month'] == month_filter]
    
    if injury_filter != 'all':
        filtered_df = filtered_df[filtered_df['Injury'] == injury_filter]
    
    if track_filter != 'all':
        filtered_df = filtered_df[filtered_df['Track'] == track_filter]
    
    # Format date for display
    filtered_df['Date'] = filtered_df['Date'].dt.strftime('%Y-%m-%d')
    
    # Select only the columns to display
    display_df = filtered_df[['Rider', 'Injury', 'Track', 'Date']]
    
    # Convert to records for DataTable
    data = display_df.to_dict('records')
    
    # Update results count
    count = len(data)
    results_text = f"Showing {count} result(s)"
    
    return data, results_text

if __name__ == '__main__':
    if df.empty:
        print("Warning: No data loaded. Please ensure updated_data.csv exists.")
    else:
        print(f"Loaded {len(df)} injury records")
        print("Starting Dash server...")
    app.run(debug=True, host='127.0.0.1', port=8050)