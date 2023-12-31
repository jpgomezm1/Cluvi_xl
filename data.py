import pandas as pd
import plotly.graph_objs as go
import dash_table
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
from dash_table.Format import Format, Scheme, Sign, Symbol, Group
from dash_table import DataTable, FormatTemplate

# Carga el archivo excel en un dataframe omitiendo la primera fila
df = pd.read_excel('informe_xlgourmet.xlsx', skiprows=1)

# Remueve los simbolos de moneda y convierte los montos a float
df['Monto'] = df['Monto'].replace({'\$': '', ',': ''}, regex=True).astype(float)

# Calcula las comisiones para cada pasarela de pago
df['Comision Cluvipay'] = df['Monto'] * 0.0399 + 500
df['Comision Otras pasarelas de pago'] = df['Monto'] * 0.0315 + df['Monto'] * 0.0020 + df['Monto'] * 0.0050 + df['Monto'] * 0.0150 + 700

# Calcula las diferencias entre las comisiones de las dos pasarelas de pago
df['Diferencia'] = df['Comision Otras pasarelas de pago'] - df['Comision Cluvipay']

# Calcula el porcentaje de las comisiones
df['Porcentaje Cluvipay'] = df['Comision Cluvipay'] / df['Monto'] * 100
df['Porcentaje Otras pasarelas de pago'] = df['Comision Otras pasarelas de pago'] / df['Monto'] * 100

# Remueve las columnas que sobran
df = df.drop(columns=['Tasa Variable', 'Tasa Fija', 'Total Comision'])

# Función de formato para las columnas de moneda
def format_currency(value):
    return f"${value:,.3f}"

# Función de formato para las columnas de porcentaje
def format_percentage(value):
    return f"{value:.2f}%"

# Aplica las funciones de formato a las columnas correspondientes
for col in ['Monto', 'Comision Cluvipay', 'Comision Otras pasarelas de pago', 'Diferencia']:
    df[col] = df[col].apply(format_currency)

for col in ['Porcentaje Cluvipay', 'Porcentaje Otras pasarelas de pago']:
    df[col] = df[col].apply(format_percentage)

# Crea una tabla interactiva con Dash
table = dash_table.DataTable(
    id='table',
    columns=[{"name": i, "id": i} for i in df.columns],
    data=df.to_dict('records'),
    sort_action="native",
    filter_action="native",
    style_cell={'textAlign': 'left'},
    page_size=10,
    filter_options={"default": 'native'},
)

# Crea gráficos interactivos con Plotly
fig1 = go.Figure(data=[
    go.Bar(name='Cluvipay', x=df.index, y=df['Porcentaje Cluvipay']),
    go.Bar(name='Otras pasarelas de pago', x=df.index, y=df['Porcentaje Otras pasarelas de pago'])
])
fig1.update_layout(barmode='group', xaxis_tickangle=-45, title_text='Comisiones por transacción (%)', yaxis_title='Porcentaje')

fig2 = go.Figure(data=[
    go.Scatter(name='Cluvipay', x=df.index, y=df['Comision Cluvipay'], mode='lines+markers'),
    go.Scatter(name='Otras pasarelas de pago', x=df.index, y=df['Comision Otras pasarelas de pago'], mode='lines+markers')
])
fig2.update_layout(xaxis_tickangle=-45, title_text='Comisiones por transacción (COP)', yaxis_title='COP')

# Crea una aplicación web con Dash
external_stylesheets = ['https://stackpath.bootstrapcdn.com/bootswatch/4.5.2/yeti/bootstrap.min.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

dropdown = dcc.Dropdown(
    id='dropdown',
    options=[{'label': i, 'value': i} for i in df['Sucursal'].unique()],
    multi=True,
    placeholder="Selecciona una Sucursal"
)



app.layout = html.Div(children=[
    html.Div(
        html.Img(src=app.get_asset_url('thelogo.png'), height="200px")
    ),
    html.H1(children='Informe Cluvipay XL Gourmet', style={'textAlign': 'center', 'padding': '20px'}),

    html.Div(children='''
        Aquí se presenta una comparación detallada de las comisiones por transacción de Cluvipay y otras pasarelas de pago, y el ahorro generado entre el 12 de mayo y el 27 de julio.
    ''', style={'textAlign': 'justify', 'margin': '20px', 'textAlign': 'center', 'fontSize': '20px'}),

    html.H2(children='Detalle de las transacciones', style={'textAlign': 'center', 'padding': '10px'}),

    html.Div(children='''
        A continuacion en esta tabla se presentan todas las transacciones generadas en el periodo, el ahorro generado a traves de Cluvipay. La informacion se puede filtrar por cualquier columna de su preferencia
    ''', style={'textAlign': 'justify', 'margin': '20px', 'textAlign': 'center', 'fontSize': '20px'}),

    dropdown,
    table,

    html.H2(children='Gráficos', style={'textAlign': 'center', 'padding': '10px'}),

    dcc.Graph(
        id='graph1',
        figure=fig1
    ),

    dcc.Graph(
        id='graph2',
        figure=fig2
    ),

    html.H2(children='Simulador de comisiones', style={'textAlign': 'center', 'padding': '10px'}),

    html.Div(children=[
        dcc.Input(
            id='input-monto',
            type='number',
            value=""
        ),
        html.Button('Calcular', id='calcular-button', n_clicks=0, style={'background-color': '#6B30BA', 'border': 'none', 'color': 'white', 'padding': '15px 32px', 'text-align': 'center', 'text-decoration': 'none', 'display': 'inline-block', 'font-size': '16px', 'margin': '4px 2px', 'cursor': 'pointer'}),
    ], style={'textAlign': 'center'}),

    html.Div(id='simulador-output', style={'textAlign': 'center', 'padding': '20px', 'fontSize': '20px'}),
])

@app.callback(
    Output('table', 'data'),
    [Input('dropdown', 'value')]
)
def update_table(selected_dropdown_value):
    if selected_dropdown_value:
        filtered_df = df[df['Sucursal'].isin(selected_dropdown_value)].copy()
        return filtered_df.to_dict('records')
    else:
        return df.to_dict('records')



@app.callback(
    Output('simulador-output', 'children'),
    [Input('calcular-button', 'n_clicks')],
    [State('input-monto', 'value')]
)
def calculate_commission(n_clicks, monto):
    if monto:
        monto = float(monto)
        comision_cluvipay = monto * 0.0399 + 500
        comision_otras_pasarelas = monto * 0.0315 + monto * 0.0020 + monto * 0.0050 + monto * 0.0150 + 700
        ahorro = comision_otras_pasarelas - comision_cluvipay
        return f'Comisión Cluvipay: {comision_cluvipay:,.2f} COP, Comisión otras pasarelas de pago: {comision_otras_pasarelas:,.2f} COP, Ahorro: {ahorro:,.2f} COP'

if __name__ == '__main__':
    app.run_server(debug=True)



