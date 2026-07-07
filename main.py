'''
    main python file containing all the user interface aspects of the program
    Displays injury data in an interactive table with searchable filters
'''
import pandas as pd
import dash
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, dash_table, Input, Output

from paths import data_path

_DISCIPLINE_BY_SPORT = {
    'motocross': 'Supercross / Motocross',
    'off_road': 'Trophy truck / Desert',
    'bmx': 'BMX',
    'skate': 'Skateboarding',
    'fmx': 'Freestyle motocross',
}


def _sport_label(code):
    return (code or '').replace('_', ' ').strip().title() or 'Unknown'


_MAX_PIE_SLICES = 12


def _empty_pie_figure(message):
    fig = go.Figure()
    fig.update_layout(
        title=message,
        annotations=[{
            'text': message,
            'showarrow': False,
            'x': 0.5,
            'y': 0.5,
            'xref': 'paper',
            'yref': 'paper',
            'font': {'size': 14},
        }],
    )
    return fig


def _cap_pie_series(counts):
    """Keep pie readable by showing top slices and grouping the rest as Other."""
    if len(counts) <= _MAX_PIE_SLICES:
        return counts
    top = counts.head(_MAX_PIE_SLICES - 1)
    other_total = counts.iloc[_MAX_PIE_SLICES - 1:].sum()
    return pd.concat([top, pd.Series({'Other': other_total})])


def _build_injury_pie_chart(filtered_df, group_by):
    """Aggregate injury counts with pandas and render as a pie chart."""
    if filtered_df.empty:
        return _empty_pie_figure('No injuries match the current filters')

    if group_by == 'venue':
        labels = (
            filtered_df['Venue']
            .fillna('')
            .astype(str)
            .str.strip()
            .replace('', 'Unknown venue')
        )
        title = 'Injury volume by track / venue'
        hover = 'Venue'
    else:
        labels = filtered_df['Year'].apply(
            lambda y: 'No date' if pd.isna(y) else str(int(y))
        )
        title = 'Injury volume by racing year'
        hover = 'Year'

    counts = labels.value_counts().sort_values(ascending=False)
    counts = _cap_pie_series(counts)
    if len(counts) > 1 and 'Other' in counts.index:
        title = f'{title} (top {_MAX_PIE_SLICES - 1} + Other)'

    chart_df = counts.reset_index()
    chart_df.columns = [hover, 'Injuries']

    fig = px.pie(
        chart_df,
        names=hover,
        values='Injuries',
        title=title,
        hole=0.35,
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        margin={'t': 50, 'b': 20, 'l': 20, 'r': 20},
        legend={'orientation': 'v', 'yanchor': 'middle', 'y': 0.5, 'x': 1.02},
        uniformtext={'mode': 'hide', 'minsize': 10},
    )
    return fig


def _apply_filters(sport_filter, discipline_filter, year_filter, month_filter, injury_filter, venue_filter):
    """Return a copy of the dataset constrained by the dashboard filters."""
    if df.empty:
        return df.copy()

    filtered_df = df.copy()

    if sport_filter != 'all':
        filtered_df = filtered_df[filtered_df['Sport'] == sport_filter]

    if discipline_filter != 'all':
        filtered_df = filtered_df[filtered_df['Discipline'] == discipline_filter]

    if year_filter == 'nodate':
        filtered_df = filtered_df[filtered_df['Date'].isna()]
    elif year_filter != 'all':
        filtered_df = filtered_df[filtered_df['Year'] == year_filter]

    if month_filter != 'all':
        filtered_df = filtered_df[filtered_df['Month'] == month_filter]

    if injury_filter != 'all':
        filtered_df = filtered_df[filtered_df['Injury'] == injury_filter]

    if venue_filter != 'all':
        filtered_df = filtered_df[filtered_df['Venue'] == venue_filter]

    return filtered_df


# Load the injury data
def load_data():
    """Load and preprocess the injury data from CSV"""
    try:
        df = pd.read_csv(data_path('updated_data.csv'))
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

        df['Discipline'] = df['Discipline'].fillna('').astype(str)
        empty_disc = df['Discipline'].str.strip() == ''
        df.loc[empty_disc, 'Discipline'] = (
            df.loc[empty_disc, 'Sport'].astype(str).str.lower().map(_DISCIPLINE_BY_SPORT).fillna('')
        )

        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Year'] = df['Date'].dt.year
        df['Month'] = df['Date'].dt.month
        df['MonthName'] = df['Date'].dt.strftime('%B')
        return df
    except FileNotFoundError:
        print(f"Error: {data_path('updated_data.csv')} not found. Please run the data processing function first.")
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
    disciplines = sorted({str(d).strip() for d in df['Discipline'].dropna().unique() if str(d).strip()})
    venues = sorted(df['Venue'].dropna().unique())
    has_undated = bool(df['Date'].isna().any())
else:
    years = months = injuries = sports = disciplines = venues = []
    has_undated = False

# Define the layout
app.layout = html.Div([
    html.Div([
        html.H1("Action Sports Injury Data Viewer", style={'textAlign': 'center', 'marginBottom': '30px'}),

        html.Div([
            html.Div([
                html.Label("Sport:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                dcc.Dropdown(
                    id='sport-filter',
                    options=[{'label': 'All Sports', 'value': 'all'}] + [{'label': _sport_label(sport), 'value': sport} for sport in sports],
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
                    options=(
                        [{'label': 'All Years', 'value': 'all'}]
                        + ([{'label': 'No date', 'value': 'nodate'}] if has_undated else [])
                        + [{'label': str(year), 'value': year} for year in years]
                    ),
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
            html.Div([
                html.Label("Chart breakdown:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                dcc.RadioItems(
                    id='chart-group-by',
                    options=[
                        {'label': ' By track / venue', 'value': 'venue'},
                        {'label': ' By racing year', 'value': 'year'},
                    ],
                    value='venue',
                    inline=True,
                    style={'marginBottom': '10px'},
                ),
            ]),
            dcc.Graph(id='injury-pie-chart', config={'displayModeBar': False}),
        ], style={
            'marginBottom': '24px',
            'padding': '20px',
            'backgroundColor': '#fafafa',
            'borderRadius': '5px',
            'border': '1px solid #e0e0e0',
        }),

        html.Div([
            dash_table.DataTable(
                id='injury-table',
                columns=[
                    {'name': 'Sport', 'id': 'Sport', 'type': 'text'},
                    {'name': 'Discipline', 'id': 'Discipline', 'type': 'text'},
                    {'name': 'Athlete', 'id': 'Athlete', 'type': 'text'},
                    {'name': 'Injury', 'id': 'Injury', 'type': 'text'},
                    {'name': 'Venue', 'id': 'Venue', 'type': 'text'},
                    {'name': 'Date', 'id': 'Date', 'type': 'text'},
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


@app.callback(
    [Output('discipline-filter', 'options'),
     Output('discipline-filter', 'value')],
    [Input('sport-filter', 'value')],
    prevent_initial_call=True,
)
def cascade_discipline_options(sport_filter):
    """When sport changes, refresh discipline choices and reset selection."""
    base = [{'label': 'All Disciplines', 'value': 'all'}]
    if df.empty:
        return base, 'all'
    sub = df if sport_filter == 'all' else df[df['Sport'] == sport_filter]
    discs = sorted({str(d).strip() for d in sub['Discipline'].dropna().unique() if str(d).strip()})
    return base + [{'label': d, 'value': d} for d in discs], 'all'


# Define the callback to update the table and pie chart
@app.callback(
    [Output('injury-table', 'data'),
     Output('results-count', 'children'),
     Output('injury-pie-chart', 'figure')],
    [Input('sport-filter', 'value'),
     Input('discipline-filter', 'value'),
     Input('year-filter', 'value'),
     Input('month-filter', 'value'),
     Input('injury-filter', 'value'),
     Input('venue-filter', 'value'),
     Input('chart-group-by', 'value')]
)
def update_dashboard(sport_filter, discipline_filter, year_filter, month_filter, injury_filter, venue_filter, chart_group_by):
    """Filter the data and refresh the table and injury volume pie chart."""
    if df.empty:
        return [], f"No data available. Please ensure {data_path('updated_data.csv')} exists.", _empty_pie_figure('No data available')

    filtered_df = _apply_filters(
        sport_filter, discipline_filter, year_filter, month_filter, injury_filter, venue_filter,
    )

    pie_figure = _build_injury_pie_chart(filtered_df, chart_group_by or 'venue')

    display_df = filtered_df.copy()
    display_df['Date'] = display_df['Date'].apply(
        lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else ''
    )
    display_df = display_df[['Sport', 'Discipline', 'Athlete', 'Injury', 'Venue', 'Date']]
    data = display_df.to_dict('records')
    results_text = f"Showing {len(data)} result(s)"

    return data, results_text, pie_figure

if __name__ == '__main__':
    if df.empty:
        print(f"Warning: No data loaded. Please ensure {data_path('updated_data.csv')} exists.")
    else:
        print(f"Loaded {len(df)} injury records")
        print("Starting Dash server...")
    app.run(debug=True, host='127.0.0.1', port=8050)
