import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import numpy as np

# Load data
sheets = ['National Response Estimates', 'Sector Response Estimates', 'State Response Estimates', 'Employment Response Estimates']
df = pd.read_excel('C:/Users/ormal/Documents/ai_data_census/ai_supplement_us_census.xlsx', sheet_name=sheets)

# National data cleanup
national = (
    df['National Response Estimates']
    .loc[lambda df_: df_['Question'].str.contains('applications|operations|changes')]
    .drop(['Scope (see data dictionary)', 'Question ID', 'Answer ID'], axis='columns')
    .rename(columns=lambda c: c.lower().replace(' ', '_'))
    .sort_values(by='estimate', ascending=False)
    .assign(
        answer=lambda df_: df_['answer'].astype('str'),
        estimate=lambda df_: df_['estimate'].str.replace('%', '').astype('float'),
        standard_error=lambda df_: df_['standard_error'].str.replace('%', '').astype('float'),
    )
)


# Instantiate app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY], meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}])

# Define app layout
app.layout = dbc.Container([
    dbc.Row(
        dbc.Col(html.H1("How are US Businesses Adopting AI?", className='text-center text-success mb-4'), width=12)
    ),
    dbc.Tabs([
        dbc.Tab(label="National Trends", children=[
            dbc.Row([
                dbc.Card([
                    dbc.CardHeader('Pick a Question'),
                    dbc.CardBody(
                        dcc.Dropdown(
                            id='question-dropdown',
                            options= [{'label': question, 'value': question}
                                      for question in national[national['answer'] != 'nan']['question'].unique()],
                            placeholder="Select Question", style={'width': '1250px'}
                        )
                    )
                ], style={'height': '200px'}),
            ], style={'marginBottom': '30px'}),
            dbc.Row([
                dbc.Card(id='graph-card', style={'height': '500px'})
            ])
        ])
    ])
])

# Define callback to update bar chart based on selected question
@app.callback(
    Output('graph-card', 'children'),
    [Input('question-dropdown', 'value')]
)
def update_bar_chart(question):
    if question:
        filtered_data = national.loc[national['question'] == question]
        sorted_data = filtered_data.sort_values(by='estimate', ascending=False)
        sorted_data = sorted_data[sorted_data['answer'] != 'nan']
        fig = dcc.Graph(
            figure=px.bar(sorted_data, x='estimate', y='answer', orientation='h', labels={'estimate': 'Percentage', 'answer': ''},
                          template='plotly_white', color='answer', color_continuous_scale='Viridis').update_layout(margin=dict(l=0, r=0, t=0, b=0))
        )
        return dbc.CardBody(fig)
    else:
        return dbc.CardBody('Please select a question to view the bar chart.')

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)