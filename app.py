import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import numpy as np

# Load data
sheets = ['National Response Estimates', 'Sector Response Estimates', 'State Response Estimates', 'Employment Response Estimates']
df = pd.read_excel('assets/ai_supplement_us_census.xlsx', sheet_name=sheets)

# Question map

question_map = {'In the last six months, what types or applications of Artificial Intelligence (AI) did this business use in producing goods or services?':
                'What types of applications of AI did this business use?',
                'In the last six months, to use Artificial Intelligence (AI), what changes did this business make?':
                'What changes did this business make to use AI?',
                'In the last six months, did this business use Artificial Intelligence to perform operations previously performed by existing equipment or software in producing goods or services?':
                'Has AI use substituted existing software/equipment in operations?',
                'During the next six months, to use Artificial Intelligence, what changes do you think this business will make?':
                'What changes do you intend to make to use AI?',
                'During the next six months, what types or applications of Artificial Intelligence (AI) do you think this business will use in producing goods or services?':
                'What types of applications of AI do you intend to use?',
                'During the next six months, do you think this business will use Artificial Intelligence to perform operations currently performed by existing equipment and software in producing goods or services?':
                'Will AI substitute existing software/equipment in current operations in the future?'}

# National data cleanup
national = (
    df['National Response Estimates']
    .loc[lambda df_: df_['Question'].str.contains('applications|operations|changes')]
    .drop(['Scope (see data dictionary)', 'Question ID', 'Answer ID'], axis='columns')
    .rename(columns=lambda c: c.lower().replace(' ', '_'))
    .sort_values(by='estimate', ascending=False)
    .assign(
        question=lambda df_: df_['question'].map(question_map),
        answer=lambda df_: df_['answer'].astype('str'),
        estimate=lambda df_: df_['estimate'].str.replace('%', '').astype('float'),
        standard_error=lambda df_: df_['standard_error'].str.replace('%', '').astype('float'),
    )
)

# naics_codes

naics_codes = pd.read_excel('https://www.census.gov/naics/2022NAICS/2022_NAICS_Descriptions.xlsx')

# naics codes cleanup

naics_codes = (
    naics_codes
      .assign(
          sector = lambda df_: df_['Code'].astype('str'),
          title = lambda df_: df_['Title'].str.replace('T$','', regex=True).str.replace('and', '&')
      )
      .loc[lambda df_: df_['sector'].str.len() == 2]
      .drop(['Code', 'Title', 'Description'], axis='columns')
      .reset_index(drop=True)
)

# Sector data cleanup

sector = (df['Sector Response Estimates']
          .loc[lambda df_: df_['Question'].str.contains('applications|operations|changes')]
          .drop(['Scope (see data dictionary)', 'Question ID', 'Answer ID'], axis='columns')
          .replace('S', np.nan)
          .dropna()
          .rename(columns=lambda c: c.lower().replace(' ', '_'))
          .sort_values(by='estimate', ascending=False)
          .assign(
               question = lambda df_: df_['question'].map(question_map),
               sector = lambda df_: df_['sector'].astype('str'),
               answer = lambda df_: df_['answer'].astype('str'),
               estimate=lambda df_: df_['estimate'].str.replace('%', '').astype('float'),
               standard_error=lambda df_: df_['standard_error'].str.replace('%', '').astype('float')
               )
          .pipe((lambda df_: pd.merge(naics_codes, df_, on='sector')))
          .rename(columns = {'title': 'industry'})
          .drop('sector', axis='columns')
)

# State data cleanup

state = (df['State Response Estimates']
          .loc[lambda df_: df_['Question'].str.contains('applications|operations|changes')]
          .drop(['Scope (see data dictionary)', 'Question ID', 'Answer ID'], axis='columns')
          .replace('S', np.nan)
          .dropna()
          .rename(columns=lambda c: c.lower().replace(' ', '_'))
          .sort_values(by='estimate', ascending=False)
          .assign(
              question = lambda df_: df_['question'].map(question_map),
              answer = lambda df_: df_['answer'].astype('str'),
              estimate=lambda df_: df_['estimate'].str.replace('%', '').replace('S', np.nan).astype('float'),
              standard_error=lambda df_: df_['standard_error'].str.replace('%', '').replace('S', np.nan).astype('float')
          )
         )

# Firm size dictionary

label_to_size = {'A': 'Small', 'B': 'Small', 'C': 'Small', 'D': "Small", 'E': 'Medium', 'F': 'Medium', 'G': "Large"}

# Employment data cleanup

employment = (df['Employment Response Estimates']
          .loc[lambda df_: df_['Question'].str.contains('applications|operations|changes')]
          .drop(['Scope (see data dictionary)', 'Question ID', 'Answer ID'], axis='columns')
          .replace('S', np.nan)
          .dropna()
          .rename(columns=lambda c: c.lower().replace(' ', '_'))
          .sort_values(by='estimate', ascending=False)
          .assign(
              question = lambda df_: df_['question'].map(question_map),
              emp_size = lambda df_: df_["empsize"].map(label_to_size),
              answer = lambda df_: df_['answer'].astype('str'),
              estimate=lambda df_: df_['estimate'].str.replace('%', '').astype('float'),
              standard_error=lambda df_: df_['standard_error'].str.replace('%', '').astype('float')
          )
          .drop('empsize', axis='columns')
         )

# Instantiate app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LITERA], meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}])

server = app.server #required for deployment on render

# Define app layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("How are US Businesses Adopting AI?", className='text-center text-primary mb-4'), width=12),
        dbc.Col(
            html.P("AI is one of the transformative technologies of our times. How US businesses adopt this technology "
                   "is of utmost importance. The US Census Bureau added supplemental content on AI to its Business Trends and "
                   "Outlook Survey during December 2023 through February 2024. This app allows you to explore this data.",
                   className='text-primary'),
            width=12
        )
    ]),
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
            ], style={'marginBottom': '30px'}, xs=12, sm=12, md=12, lg=6, xl=6),
            dbc.Row([
                dbc.Card(id='graph-card', style={'height': '500px'})
            ], xs=12, sm=12, md=12, lg=6, xl=6)
        ]),

        dbc.Tab(label="Sector Trends", children=[
            dbc.Row([
                dbc.Card([
                    dbc.CardHeader('Pick a Question and Sector'),
                    dbc.CardBody([
                        dcc.Dropdown(
                            id='sector-question-dropdown',
                            options=[{'label': question, 'value': question}
                                     for question in sector['question'].unique()],
                            placeholder="Select Question",
                            style={'width': '600px', 'display': 'inline-block'}
                        ),
                        dcc.Dropdown(
                            id='sector-dropdown',
                            options=[{'label': industry, 'value': industry}
                                     for industry in sector['industry'].unique()],
                            placeholder="Select Sector",
                            style={'width': '600px', 'display': 'inline-block', 'marginLeft': '50px'}
                        )
                    ])
                ], style={'height': '200px'}),
            ], style={'marginBottom': '30px'}, xs=12, sm=12, md=12, lg=6, xl=6),
            dbc.Row([
                dbc.Card(id='sector-graph-card', style={'height': '500px'})
            ], xs=12, sm=12, md=12, lg=6, xl=6)
        ]),
        dbc.Tab(label="State Trends", children=[
           dbc.Row([
               dbc.Card([
                   dbc.CardHeader('Pick a Question and one State'),
                   dbc.CardBody([
                       dcc.Dropdown(
                           id='state-question-dropdown',
                           options=[{'label': question, 'value': question}
                                    for question in state['question'].unique()],
                           placeholder="Select Question",
                           style={'width': '600px', 'display': 'inline-block'}
                       ),
                       dcc.Dropdown(
                           id='state-dropdown',
                           options=[{'label': state, 'value': state}
                                    for state in state['state'].unique()],
                           placeholder="Select State",
                           style={'width': '600px', 'display': 'inline-block', 'marginLeft': '50px'}
                       )
                   ])
               ], style={'height': '200px'}),
           ], style={'marginBottom': '30px'}, xs=12, sm=12, md=12, lg=6, xl=6),
           dbc.Row([
               dbc.Card(id='state-graph-card', style={'height': '500px'})
           ], xs=12, sm=12, md=12, lg=6, xl=6)
       ]),
       dbc.Tab(label="Firm Size Trends", children=[
           dbc.Row([
               dbc.Card([
                   dbc.CardHeader('Pick a Question and Firm Size category'),
                   dbc.CardBody([
                       dcc.Dropdown(
                           id='firm-question-dropdown',
                           options=[{'label': question, 'value': question}
                                    for question in employment['question'].unique()],
                           placeholder="Select Question",
                           style={'width': '600px', 'display': 'inline-block'}
                       ),
                       dcc.Dropdown(
                           id='firm-size-dropdown',
                           options=[{'label': size, 'value': size}
                                    for size in employment['emp_size'].unique()],
                           placeholder="Select Firm Size category",
                           style={'width': '600px', 'display': 'inline-block', 'marginLeft': '50px'}
                       )
                   ])
               ], style={'height': '200px'}),
           ], style={'marginBottom': '30px'}, xs=12, sm=12, md=12, lg=6, xl=6),
           dbc.Row([
               dbc.Card(id='firm-size-graph-card', style={'height': '500px'})
           ], xs=12, sm=12, md=12, lg=6, xl=6),
    ]),
]),
    dbc.Row([
        dbc.Col(html.Img(src="/assets/aatiny.jpg", style={'marginRight': '50px'}, height="50px"), width=6, style={'textAlign': 'right'}),
        ], style={"position": "fixed", "bottom": '10px', "right": '10px', "zIndex": 999})
       ], xs=12, sm=12, md=12, lg=6, xl=6)

# National bar chart callback

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

# Sector bar chart callback

@app.callback(
    Output('sector-graph-card', 'children'),
    [Input('sector-question-dropdown', 'value'), Input('sector-dropdown', 'value')]
)
def update_sector_bar_chart(question, sector_name):
    if question and sector_name:
        filtered_data = sector.loc[(sector['question'] == question) & (sector['industry'] == sector_name)]
        sorted_data = filtered_data.sort_values(by='estimate', ascending=False)
        sorted_data = sorted_data[sorted_data['answer'] != 'nan']
        fig = dcc.Graph(
            figure=px.bar(sorted_data, x='estimate', y='answer', orientation='h', labels={'estimate': 'Percentage', 'answer': ''},
                          template='plotly_white', color='answer', color_continuous_scale='Viridis').update_layout(margin=dict(l=0, r=0, t=0, b=0))
        )
        return dbc.CardBody(fig)
    else:
        return dbc.CardBody('Please select a question and sector to view the bar chart.')

# State bar chart callback

@app.callback(
   Output('state-graph-card', 'children'),
   [Input('state-question-dropdown', 'value'), Input('state-dropdown', 'value')]
)
def update_state_bar_chart(question, state_name):
   if question and state_name:
       filtered_data = state.loc[(state['question'] == question) & (state['state'] == state_name)]
       sorted_data = filtered_data.sort_values(by='estimate', ascending=False)
       sorted_data = sorted_data[sorted_data['answer'] != 'nan']
       fig = dcc.Graph(
           figure=px.bar(sorted_data, x='estimate', y='answer', orientation='h', labels={'estimate': 'Percentage', 'answer': ''},
                         template='plotly_white', color='answer', color_continuous_scale='Viridis').update_layout(margin=dict(l=0, r=0, t=0, b=0))
       )
       return dbc.CardBody(fig)
   else:
       return dbc.CardBody('Please select a question and state to view the bar chart.')

# Firm size bar chart callback

@app.callback(
   Output('firm-size-graph-card', 'children'),
   [Input('firm-question-dropdown', 'value'), Input('firm-size-dropdown', 'value')]
)
def update_firm_size_bar_chart(question, firm_size):
   if question and firm_size:
       filtered_data = employment.loc[(employment['question'] == question) & (employment['emp_size'] == firm_size)]
       sorted_data = filtered_data.sort_values(by='estimate', ascending=False)
       sorted_data = sorted_data[sorted_data['answer'] != 'nan']
       fig = dcc.Graph(
           figure=px.bar(sorted_data, x='estimate', y='answer', orientation='h', labels={'estimate': 'Percentage', 'answer': ''},
                         template='plotly_white', color='answer', color_continuous_scale='Viridis').update_layout(margin=dict(l=0, r=0, t=0, b=0))
       )
       return dbc.CardBody(fig)
   else:
       return dbc.CardBody('Please select a question and firm size category to view the bar chart.')

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)