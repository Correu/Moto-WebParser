'''
    main python file containing all the user interface aspects of the program
    Displays injury data in an interactive table with searchable filters
'''
import pandas as pd
import dash
from dash import dcc, html, dash_table, Input, Output

# Load the injury data
def load_data():
    """Load and preprocess the injury data from CSV"""
    try:
        df = pd.read_csv('updated_data.csv')
        # Backward-compatible defaults for older motocross-only files
        if 'Sport' not in df.columns:
            df['Sport'] = 'motocross'
        if 'Discipline' not in df.columns:
            df['Discipline'] = ''
        if 'Venue' not in df.columns:
            if 'Track' in df.columns:
                df['Venue'] = df['Track']
            else:
                df['Venue'] = ''
        if 'Athlete' not in df.columns:
            if 'Rider' in df.columns:
                df['Athlete'] = df['Rider']
            else:
                df['Athlete'] = ''

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
app.title = "Action Sports Injury Data Viewer"

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
    sports = sorted(df['Sport'].dropna().unique())
    disciplines = sorted([d for d in df['Discipline'].dropna().unique() if str(d).strip()])
    venues = sorted(df['Venue'].dropna().unique())
else:
    years = months = injuries = sports = disciplines = venues = []

# Define the layout
app.layout = html.Div([
    html.Div([
        html.H1("Action Sports Injury Data Viewer", style={'textAlign': 'center', 'marginBottom': '30px'}),
        
        html.Div([
            html.Div([
                html.Label("Sport:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                dcc.Dropdown(
                    id='sport-filter',
                    options=[{'label': 'All Sports', 'value': 'all'}] + [{'label': sport.title(), 'value': sport} for sport in sports],
                    value='all',
                    clearable=False,
                    style={'width': '100%'}
                ),
            ], style={'width': '16%', 'display': 'inline-block', 'marginRight': '0.8%', 'verticalAlign': 'top'}),

            html.Div([
                html.Label("Discipline:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                dcc.Dropdown(
                    id='discipline-filter',
                    options=[{'label': 'All Disciplines', 'value': 'all'}] + [{'label': discipline, 'value': discipline} for discipline in disciplines],
                    value='all',
                    clearable=False,
                    searchable=True,
                    style={'width': '100%'}
                ),
            ], style={'width': '16%', 'display': 'inline-block', 'marginRight': '0.8%', 'verticalAlign': 'top'}),

            html.Div([
                html.Label("Year:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                dcc.Dropdown(
                    id='year-filter',
                    options=[{'label': 'All Years', 'value': 'all'}] + [{'label': str(year), 'value': year} for year in years],
                    value='all',
                    clearable=False,
                    style={'width': '100%'}
                ),
            ], style={'width': '16%', 'display': 'inline-block', 'marginRight': '0.8%', 'verticalAlign': 'top'}),
            
            html.Div([
                html.Label("Month:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                dcc.Dropdown(
                    id='month-filter',
                    options=[{'label': 'All Months', 'value': 'all'}] + [{'label': month_names.get(m, f'Month {m}'), 'value': m} for m in months],
                    value='all',
                    clearable=False,
                    style={'width': '100%'}
                ),
            ], style={'width': '16%', 'display': 'inline-block', 'marginRight': '0.8%', 'verticalAlign': 'top'}),
            
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
            ], style={'width': '16%', 'display': 'inline-block', 'marginRight': '0.8%', 'verticalAlign': 'top'}),
            
            html.Div([
                html.Label("Location (Venue):", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                dcc.Dropdown(
                    id='venue-filter',
                    options=[{'label': 'All Venues', 'value': 'all'}] + [{'label': venue, 'value': venue} for venue in venues],
                    value='all',
                    clearable=False,
                    searchable=True,
                    style={'width': '100%'}
                ),
            ], style={'width': '16%', 'display': 'inline-block', 'verticalAlign': 'top'}),
        ], style={'marginBottom': '20px', 'padding': '20px', 'backgroundColor': '#f0f0f0', 'borderRadius': '5px'}),
        
        html.Div(id='results-count', style={'marginBottom': '10px', 'fontSize': '16px', 'fontWeight': 'bold'}),
        
        html.Div([
            dash_table.DataTable(
                id='injury-table',
                columns=[
                    {'name': 'Sport', 'id': 'Sport', 'type': 'text'},
                    {'name': 'Discipline', 'id': 'Discipline', 'type': 'text'},
                    {'name': 'Athlete', 'id': 'Athlete', 'type': 'text'},
                    {'name': 'Injury', 'id': 'Injury', 'type': 'text'},
                    {'name': 'Venue', 'id': 'Venue', 'type': 'text'},
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
    [Input('sport-filter', 'value'),
     Input('discipline-filter', 'value'),
     Input('year-filter', 'value'),
     Input('month-filter', 'value'),
     Input('injury-filter', 'value'),
     Input('venue-filter', 'value')]
)
def update_table(sport_filter, discipline_filter, year_filter, month_filter, injury_filter, venue_filter):
    """Filter the data based on selected filters"""
    if df.empty:
        return [], "No data available. Please ensure updated_data.csv exists."
    
    filtered_df = df.copy()
    
    # Apply filters
    if sport_filter != 'all':
        filtered_df = filtered_df[filtered_df['Sport'] == sport_filter]

    if discipline_filter != 'all':
        filtered_df = filtered_df[filtered_df['Discipline'] == discipline_filter]

    if year_filter != 'all':
        filtered_df = filtered_df[filtered_df['Year'] == year_filter]
    
    if month_filter != 'all':
        filtered_df = filtered_df[filtered_df['Month'] == month_filter]
    
    if injury_filter != 'all':
        filtered_df = filtered_df[filtered_df['Injury'] == injury_filter]
    
    if venue_filter != 'all':
        filtered_df = filtered_df[filtered_df['Venue'] == venue_filter]
    
    # Format date for display
    filtered_df['Date'] = filtered_df['Date'].dt.strftime('%Y-%m-%d')
    
    # Select only the columns to display
    display_df = filtered_df[['Sport', 'Discipline', 'Athlete', 'Injury', 'Venue', 'Date']]
    
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