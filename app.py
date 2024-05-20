import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import numpy as np


# Load data

sheets=['National Response Estimates', 'Sector Response Estimates', 'State Response Estimates', 'Employment Response Estimates']

df = pd.read_excel('C:/Users/ormal/Documents/ai_data_census/ai_supplement_us_census.xlsx',
                    sheet_name=sheets)

# National data cleanup

national = (
    df['National Response Estimates']
      .loc[lambda df_: df_['Question'].str.contains('applications|operations|changes')]
      .drop(['Scope (see data dictionary)', 'Question ID', 'Answer ID'], axis='columns')
      .rename(columns = lambda c: c.lower().replace(' ', '_'))
      .sort_values(by='estimate', ascending=False)
      .assign(
          answer = lambda df_: df_['answer'].astype('str'),
          estimate = lambda df_: df_['estimate'].str.replace('%', '').astype('float'),
          standard_error = lambda df_: df_['standard_error'].str.replace('%', '').astype('float'),
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
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader('Pick a Question'),
                        dbc.CardBody(
                            dcc.Dropdown(
                                id='question-dropdown',
                                options=[{'label': question, 'value': question} for question in national['question'].unique()],
                                placeholder="Select Question"
                            )
                        )
                    ])
                ], width=4),
                dbc.Col(
                    dcc.Graph(id='national-bar')
                , width=8)
            ])
        ])
    ])
])

# Define callback to update bar chart based on selected question
@app.callback(
    Output('national-bar', 'figure'),
    [Input('question-dropdown', 'value')]
)
def update_bar_chart(question):
    if question:
        filtered_data = national.loc[national['question'] == question]
        fig = px.bar(filtered_data, x='estimate', y='answer', orientation='h', labels={'estimate': 'Percentage', 'question': 'Types or Applications of AI'})
        return fig
    else:
        return {}

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)