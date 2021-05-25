import time
import numpy as np
import csv
from time import sleep
from datetime import datetime
from random import random
from selenium.common import exceptions
from msedge.selenium_tools import Edge, EdgeOptions
from jupyter_dash import JupyterDash
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import plotly.express as px
from os import path
max_price = 1000
import re


app = JupyterDash(__name__,external_stylesheets=[dbc.themes.LUX])
app.config.suppress_callback_exceptions = True
df = pd.DataFrame()
df_temp_range = pd.DataFrame()


def generate_filename(search_term):
    timestamp = datetime.now().strftime("%Y%m")
    stem = path = '_'.join(search_term.split(' '))
    filename = stem + '_' + timestamp + '.csv'
    return filename


def save_data_to_csv(record, filename, new_file=False):
    header = ['description', 'price', 'rating', 'review_count', 'url']
    if new_file:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)
    else:
        with open(filename, 'a+', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(record)


def create_webdriver() -> Edge:
    options = EdgeOptions()
    options.use_chromium = True
    options.headless = True
    driver = Edge(options=options)
    return driver


def generate_url(search_term, page):
    base_template = 'https://www.amazon.in/s?k={}&ref=nb_sb_noss'
    search_term = search_term.replace(' ', '+')
    stem = base_template.format(search_term)
    url_template = stem + '&page={}'
    if page == 1:
        return stem
    else:
        return url_template.format(page)


def extract_card_data(card):
    description = card.find_element_by_xpath('.//h2/a').text.strip()
    url = card.find_element_by_xpath('.//h2/a').get_attribute('href')
    try:
        price = card.find_element_by_xpath('.//span[@class="a-price-whole"]').text
    except exceptions.NoSuchElementException:
        return
    try:
        temp = card.find_element_by_xpath('.//span[contains(@aria-label, "out of")]')
        rating = temp.get_attribute('aria-label')
    except exceptions.NoSuchElementException:
        rating = ""
    try:
        temp = card.find_element_by_xpath('.//span[contains(@aria-label, "out of")]/following-sibling::span')
        review_count = temp.get_attribute('aria-label')
    except exceptions.NoSuchElementException:
        review_count = ""
    return description, price, rating, review_count, url


def collect_product_cards_from_page(driver):
    cards = driver.find_elements_by_xpath('//div[@data-component-type="s-search-result"]')
    return cards


def sleep_for_random_interval():
    time_in_seconds = random() * 2
    sleep(time_in_seconds)


def run_1(search_term):
    """Run the Amazon webscraper"""
    filename = generate_filename(search_term)
    save_data_to_csv(None, filename, new_file=True)  # initialize a new file
    driver = create_webdriver()
    num_records_scraped = 0

    for page in range(1, 11):  # max of 20 pages
        # load the next page
        search_url = generate_url(search_term, page)
        print(search_url)
        driver.get(search_url)
        print('TIMEOUT while waiting for page to load')

        # extract product data
        cards = collect_product_cards_from_page(driver)
        for card in cards:
            record = extract_card_data(card)
            if record:
                save_data_to_csv(record, filename)
                num_records_scraped += 1
        sleep_for_random_interval()

    # shut down and report results
    driver.quit()
    print(f"Scraped {num_records_scraped:,d} for the search term: {search_term}")
    return filename


app.layout = html.Div([
    html.Br(),

    dbc.Row([
        dbc.Col([
            html.Div([
                dbc.Input(id='search1',type='text',placeholder='What are you looking for? Eg. Phones,Tv,Laptops,.etc. ',className='border border-success form-control'),
            ],className="input-group")
        ],width={'size':5,'offset':3}),
        dbc.Col([
            html.Div([
                    dbc.Button("search",id="btnSearch",type="button",className="btn btn-success")
                ],className="input-group-append")
        ],width={'size':1,'offset':0})
    ]),
    html.Br(),
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Div([
                    html.H4([
                        html.B(["Total Products Count "])
                    ],className="card-title"),
                    html.P(id="row_count_id",children=[
                        "No DataFrame"
                    ],className="card-text")
                ],className="card-body")
            ],className="card border border-success")
        ],width={'size':5,'offset':1}),
        dbc.Col([
            html.Div([
                html.Div([
                    html.H4([
                        html.B(["Total Brands Count "])
                    ],className="card-title"),
                    html.P(id="product_count_id",children=[
                        "No DataFrame"
                    ],className="card-text")
                ],className="card-body")
            ],className="card border border-success")
        ],width={'size':5,'offset':0})
    ]),
    html.Br(),
    dbc.Row([
        dbc.Col([
            dcc.Loading(id="loading1",
                        type="cube",
                        color="green",
                        children=html.Div([dcc.Graph(id='graph1')],className="border border-success"))
        ],width={'size':10, 'offset':1})
    ]),
    html.Br(),
    dbc.Row([
        dbc.Col([
            html.Hr(style={'background-color':'grey'} )
        ],width={'size':10,'offset':1})
    ]),
    dbc.Row([
       dbc.Col([
           html.Div([
               html.H4([
                   html.B("Brand Wise Details")
               ])
           ],style={'padding':10,'text-align':'center'})
       ],width={'size':10,'offset':1})
    ]),
    html.Br(),
    dbc.Row([
        dbc.Col([
            html.Div([
            dcc.Dropdown(id='brand_dropdown',
                         placeholder="Select Brand Name",
                        clearable=False)])
        ],width={'size':10,'offset':1})
    ]),
    html.Br(),
    dbc.Row([

        dbc.Col([
            dcc.Loading(id="loading2",
                        type="cube",
                        color="green",
                        children=html.Div([dcc.Graph(id='graph2')], className="border border-success"))
        ], width={'size': 6, 'offset': 1}),


        dbc.Col([
            dcc.Loading(id="loading3",
                        type="cube",
                        color="green",
                        children=html.Div([dcc.Graph(id='graph3')], className="border border-success"))
        ], width={'size': 4, 'offset': 0})

    ]),
    html.Br(),
    dbc.Row([
        dbc.Col([
            html.Hr(style={'background-color':'grey'} )
        ],width={'size':10,'offset':1})
    ]),
    dbc.Row([
       dbc.Col([
           html.Div([
               html.H4(id="range-id",
                       children=[
                   html.B("Price Range Between _______")
               ])
           ],style={'padding':10,'text-align':'center'})
       ],width={'size':10,'offset':1})
    ]),
    
    dbc.Row([
        dbc.Col([
            dcc.RangeSlider(
                id='non-linear-range-slider',
                marks={i: '{}'.format(100 ** i) for i in range(4)},
                   allowCross=False,
                dots=False,
                value=[0,1000],
                step=1.0,
                updatemode='drag'
            )
        ],width={'size':9,'offset':1}),
        
        dbc.Col([
            dbc.Button("SHOW",id="btnRange",type="button",className="btn btn-success")
        ],width={'size':1,'offset':0})
    ]),
    
    html.Br(),
    dbc.Row([
        dbc.Col([
            dbc.CardDeck(id="card-deck-header",children=[
                dbc.Card([
                    dbc.CardHeader(html.H5("Total Products in Range")),
                    dbc.CardBody([
                        html.H5(id="product_count",
                               children=[
                                "No DataFrame"
                        ],className="card-title")
                    ]),
                ]),
                dbc.Card([
                    dbc.CardHeader(html.H5("We suggest you,")),
                    dbc.CardBody([
                        html.H5(id="suggest_id",
                                children=[
                            "nothing"
                        ], className="card-title"),
                    ]),
                ])
            ])
        ],width={'size':10,'offset':1})
    ]),
    
      
    html.Br(),
    dbc.Row([
        dbc.Col([
            dcc.Loading(id="loading-range-graph",
                        type="cube",
                        color="green",
                        children=html.Div([dcc.Graph(id='graph-by-range')], className="border border-success"))
        ],width={'size':10,'offset':1})
    ]),
    html.Br(),
 
    dbc.Row([
        dbc.Col([
            dbc.CardDeck(id="card-deck-header2",children=[
                dbc.Card([
                    dbc.CardHeader(html.H5("Low Budget Product")),
                    dbc.CardBody([
                        html.H5(id="budget_low",
                               children=[
                                "No DataFrame"
                        ],className="card-title")
                    ]),
                ]),
                dbc.Card([
                    dbc.CardHeader(html.H5("High Budget Product")),
                    dbc.CardBody([
                        html.H5(id="budget_high",
                               children=[
                                "No DataFrame"
                        ],className="card-title")
                    ]),
                ])
            ])
        ],width={'size':10,'offset':1})
    ]),    
    html.Br(),
    html.Br()
    
],style={'background-color':"#F6FFEF"})




@app.callback(Output("range-id","children"),
              Output("non-linear-range-slider","max"),
            [Input("non-linear-range-slider","value")])
def update_range_div(value):
    return "Price Range Between "+str(value[0])+" to "+str(value[1]),max_price


@app.callback(Output("graph-by-range","figure"),
              Output("product_count","children"),
              Output("suggest_id","children"),
             [Input("btnRange","n_clicks")],
             [State("non-linear-range-slider","value")])
def update_graph_by_range(btn_clicks,value):
    print(value[0])
    print("-")
    print(value[1])
    global df
    
    if btn_clicks:
        df_for=df
        df_for = df_for[(df_for['price'] < value[1]) & (df_for['price'] > value[0])]
        df_for['rating_num'] = df_for['rating']
        df_for[['rating_num']] = df_for[['rating_num']].astype(str)
        df_for.dropna(inplace=True)
        df_for.sort_values("price", ascending=True, inplace=True)
        df_for.reset_index(inplace=True)
        
        
        j=0
        for row in df_for['rating']:
            df_for['rating_num'].iloc[j] = str(row).split(' ')[0]
            j+=1

        df_for["name"] = df_for["brand"]
        j=0
        for row in df_for['description']:
            df_for['name'].iloc[j] = re.split('; |, |\( |: |-',str(row))[0]
            j+=1
            
        df_for[['rating_num']] = df_for[['rating_num']].apply(pd.to_numeric)
        

        del df_for["index"]
        #print(df_for.head())
        #li_by_price = []
        
        
        
        fig_range = px.scatter(df_for, x=df_for.index, 
                                y='price',
                                hover_data=['name'], 
                                color='rating_num',
                                color_continuous_scale="matter",
                                height=400)
        fig_range.update_xaxes(showticklabels=False)
        fig_range.update_traces(mode='markers', marker_line_width=1, marker_size=8)
        fig_range.update_layout(
            xaxis={
              'title':{
                  'text':'Product Between Range' 
              } 
            },
            legend={
                'title':{
                    'text':'RATING OUT OF 5'
                }
            }
        )
        
        if (len(df_for)==1):
            
            prod_pr = str(df_for["description"].iloc[-1]) + ", Price: " + str(df_for["price"].iloc[-1])
            return fig_range, str(len(df_for.index)), str(prod_pr)
        else:
            
            price = (int)((df_for["price"].mean()+df_for["price"].max())/2)
            
            df_mean_price = df_for[(df_for['rating_num'] >= 4.2) & (df_for['price'] > price)]

            #df_mean_price = df_rating_4_2[df_rating_4_2['price'] < (df_rating_4_2["price"].mean())]

            print(df_mean_price)
            if len(df_mean_price)>0:
                high_budget_desc = df_mean_price[df_mean_price["price"]==df_mean_price["price"].max()]["description"].iloc[0]
                high_budget_price = df_mean_price[df_mean_price["price"]==df_mean_price["price"].max()]["price"].iloc[0]
                prod_pred = str(high_budget_desc)+" Price: Rs."+str(high_budget_price)+"/-"
                return fig_range, str(len(df_for.index)), str(prod_pred)
            else:
                return fig_range, str(len(df_for.index)), str("Empty Dataframe")
    return {
        'layout':{
            'title':'Empty Graph'
        }
    }, "No Data Frame", "Nothing"



@app.callback(
            Output("graph1","figure"),
            Output("brand_dropdown", "options"),
            Output("row_count_id", "children"),
            Output("product_count_id", "children"),
            Output("budget_low", "children"),
            Output("budget_high", "children"),
            [Input("btnSearch","n_clicks")],
            [State('search1', 'value')])
def update_graph1(btnValue, search_term):
    df1 = pd.DataFrame()
    brand_name_list = []
    global df
    global max_price
    if search_term:
        df_brand = pd.DataFrame()
        file_name = search_term+"_"+datetime.now().strftime("%Y%m")+".csv"
        nan_value = float("NaN")
        if path.exists(file_name):
            df = pd.read_csv(file_name)
        else:
            fn = run_1(search_term)
            df = pd.read_csv(fn)

        df.columns = ['description', 'price', 'rating', 'reviewCount', 'url']
       
        j = 0
        df.insert(5, "brand", df['description'], True)
        
        for i in df['description']:
            df['brand'].iloc[j] = str(i.split(' ')[0]).lower()
            j = j + 1

        # defining to global variable
        df = data_frame(df)
        df_brand = pd.DataFrame()
        
        df_range = df.groupby(by='brand')[['reviewCount', 'price']].max().reset_index()
        max_price = df_range['price'].max()
       
        df_brand = df.groupby(by='brand')[['reviewCount', 'price']].min().reset_index()
        ser_brand = df['brand'].value_counts().reset_index()
        ser_brand.columns = ['brand', 'freq']


        df_brand.insert(3, "freq_brand", df_brand['price'])
        c = 0
        for i in df_brand['brand']:
            c1 = 0
            for j in ser_brand['brand']:
                if str(i) == str(j):
                    df_brand['freq_brand'].iloc[c] = ser_brand['freq'].iloc[c1]
                    c = c + 1
                c1 = c1 + 1

        df_brand_new = df_brand
        df_brand_new.dropna(inplace=True)
        for i in df_brand_new['brand']:
            brand_name_list.append({'label': i, 'value': str(i)})
            
        
        fig = px.bar(df_brand, x='brand', y='price', color='freq_brand', color_continuous_scale='sunsetdark')
        fig.update_layout(
            legend=dict(
                title={
                    'text': 'frequency of products'
                }
            ),
            yaxis={
            'title': 'Brand offering Minimum price product'
        })
        
        
        len_row = len(df)
        divide_30 = (int)(len_row / 3)
        mean_price = df["price"].mean()
        
        df_temp1 = df
        
        df_temp1['rating_num'] = df_temp1['rating']
        df_temp1[['rating_num']] = df_temp1[['rating_num']].astype(str)
        df_temp1.dropna(subset=["rating_num","rating"],inplace=True)
        j=0
        for row in df_temp1['rating']:
            df_temp1['rating_num'].iloc[j] = str(row).split(' ')[0]
            j+=1

        df_temp1[['rating_num']] = df_temp1[['rating_num']].apply(pd.to_numeric)
        
#         print(df_temp1)
        
        df_for_low = df_temp1[(df_temp1["price"] < mean_price) & (df_temp1["rating_num"] >= 4.2)]
     
        low_budget_desc = df_for_low[df_for_low["price"]==df_for_low["price"].max()]["description"].iloc[0]
        low_budget_price = df_for_low[df_for_low["price"]==df_for_low["price"].max()]["price"].iloc[0]
        
        low_budget_product = str(low_budget_desc) + ", Price: Rs." + str(low_budget_price) + "/-"
        
        
        df_for_high = df_temp1[(df_temp1["price"] > mean_price) & (df_temp1["rating_num"] >= 4.2)]
     
        high_budget_desc = df_for_high[df_for_high["price"]==df_for_high["price"].max()]["description"].iloc[0]
        high_budget_price = df_for_high[df_for_high["price"]==df_for_high["price"].max()]["price"].iloc[0]
        
        high_budget_product = str(high_budget_desc) + ", Price: Rs." + str(high_budget_price) + "/-"
        return fig, brand_name_list, str(len(df.index)), str(len(df_brand['brand'])), str(low_budget_product),str(high_budget_product)
    else:
        return {
                   'layout': {
                       'title': 'Empty graph'
                   }
               }, brand_name_list, str("No DataFrame"), str("No DataFrame"), str("No DataFrame"), str("No DataFrame")

@app.callback(Output("graph2","figure"),
              Output("graph3","figure"),
              [Input("brand_dropdown","value")]
              )
def update_graph2(value):
    global df

    df_brand_wise1 = {}
    if value:

        df_brand_wise = df[df['brand'] == str(value)]

        df_brand_wise['rating_num'] = df_brand_wise['rating']
        df_brand_wise[['rating_num']] = df_brand_wise[['rating_num']].astype(str)
        df_brand_wise.dropna(subset=["rating_num","rating"],inplace=True)
        j=0
        for row in df_brand_wise['rating']:
            df_brand_wise['rating_num'].iloc[j] = str(row).split(' ')[0]
            j+=1

        df_brand_wise[['rating_num']] = df_brand_wise[['rating_num']].apply(pd.to_numeric)
        j = 0
        df_brand_wise['description_1'] = df_brand_wise['description']
        for row in df_brand_wise['description']:
            df_brand_wise['description_1'].iloc[j] = str(row).split(' ')[:6]
            j += 1

        df_brand_wise.reset_index()
        li_prod_spec = []
        
        df_brand_wise["text"] = df_brand_wise["description"]
        j=0
        for item in df_brand_wise["description"]:
            if len(item.split(' ')) > 5:
                df_brand_wise["text"].iloc[j] = item.split(' ')[:5]
            else:
                df_brand_wise["text"].iloc[j] = item.split(' ')[:2]
            j=j+1

        fig1 = px.bar(df_brand_wise, x='rating_num',
                    y='description', color='price', color_continuous_scale='matter',
                    orientation='h', text='description', hover_data={
                                                                'text':True,
                                                                'description':False,
                                                                'price':True,
                                                                'rating_num':True
                                                                    }
            )
        fig1.update_layout(barmode='stack',

                          title={
                              'text': "<b>"+str(value).upper()+"</b> PRODUCTS"
                          },
                          xaxis={
                                'title':'Rating out of 5'
                            },
                          yaxis={
                              'title': 'Product description',
                              'showticklabels':False
                          }
                          )
        fig1.update_traces(texttemplate='%{text}', textposition='inside')
        fig1.update_xaxes(range=[0,5],nticks=20)

        fig2 = px.pie(df_brand_wise, values='reviewCount', names='text', color_discrete_sequence=px.colors.sequential.matter_r,
                      color='rating_num')
        fig2.update_traces( pull=[0.1 if (df_brand_wise['reviewCount'].max() == i)  else 0.0 for i in df_brand_wise['reviewCount']],
                            showlegend=False)
        fig2.update_layout(title_text="<b>"+str(value).upper()+"</b> products review count".upper())
        return fig1, fig2

    else:
        return {
            'layout':{
                'title':'Empty Graph',
                'xaxis':{
                    'title': 'Rating out of 5'
                },
                'yaxis' : {
                    'title': 'Product description'
                }
            }
        },{
            'layout':{
                'title':'Empty Graph'
            }
        }


def data_frame(dataFrame):

    j=0
    for i in dataFrame['price']:
        dataFrame['price'].iloc[j] = i.replace(',', '')
        dataFrame['reviewCount'].iloc[j] = str(dataFrame['reviewCount'].iloc[j]).replace(',', '')
        j=j+1

    dataFrame['reviewCount'] = pd.to_numeric(df['reviewCount'], errors='coerce')
    dataFrame['reviewCount'].dropna(inplace=True)
    dataFrame[['reviewCount', 'price']] = dataFrame[['reviewCount', 'price']].apply(pd.to_numeric)
    return dataFrame

# if __name__ == '__main__':
#     app.run_server(debug=True)

app.run_server(mode='external',port=1234)