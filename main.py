# -*- coding: utf-8 -*-
import pandas as pd
import plotly.graph_objects as go
from fasthtml.common import *
from starlette.testclient import TestClient

# --- Configuração do FastHTML ---

# Adiciona o script do Plotly e um estilo de fundo
plotly_js = Script(src="https://cdn.plot.ly/plotly-2.32.0.min.js")
body_style = Style("body { background-color: #FDFBF5; font-family: sans-serif; }")

# Pico CSS é incluído por padrão no FastHTML
app, rt = fast_app(hdrs=[plotly_js, body_style])

# --- Carregamento de Dados ---
data_file = 'Coffe_sales.xlsx'
try:
    df = pd.read_excel(data_file)
    print(f"Sucesso: Arquivo '{data_file}' carregado.")
except FileNotFoundError:
    print(f"AVISO: Arquivo '{data_file}' não encontrado.")
    print("Usando dados fictícios para demonstração.")
    dummy_dates = pd.to_datetime(pd.date_range(start='2025-01-01', periods=100))
    df = pd.DataFrame({
        'money': [x * 10 + 50 for x in range(100)],
        'cash_type': ['card', 'cash'] * 50,
        'coffee_name': ['Espresso', 'Latte', 'Capuccino'] * 33 + ['Espresso'],
        'date': dummy_dates
    })

# --- Definições de Cores ---
background_color = 'white'
text_color = '#2A140D'
coffee_colors = ['#D2B48C', '#2A140D']

# --- Funções Auxiliares para Gráficos ---

def create_metric_card(value, title, is_currency=False, height=250):
    """Cria um gráfico de Indicador do Plotly."""
    fig = go.Figure(go.Indicator(
        mode="number",
        value=round(value, 2) if is_currency else int(value),
        title={"text": title, 'font': {'color': text_color, 'size': 16}},
        number={'font': {'color': text_color, 'size': 36}, 'prefix': '$' if is_currency else ''}
    ))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=height)
    return Safe(fig.to_html(full_html=False, include_plotlyjs=False))

def create_donut_chart(df, height=250):
    if df.empty: 
        return Safe("<p>Sem dados para gráfico de rosca.</p>")
    sales_by_payment_type = df.groupby('cash_type')['money'].sum()
    fig = go.Figure(data=[go.Pie(
        labels=sales_by_payment_type.index,
        values=sales_by_payment_type,
        hole=.6,
        textfont_size=12,
        direction='clockwise',
        sort=False
    )])
    fig.update_layout(
        title_text='Sales By Payment Type',
        title_font_color=text_color,
        title_x=0.5,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend_font_color=text_color,
        height=height,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5)
    )
    fig.update_traces(
        hoverinfo='label+percent', textinfo='percent', textfont_color='white',
        marker=dict(colors=coffee_colors, line=dict(color='#000000', width=1))
    )
    return Safe(fig.to_html(full_html=False, include_plotlyjs=False))

def create_bar_chart(df, height=450):
    if df.empty: 
        return Safe("<p>Sem dados para gráfico de barras.</p>")
    revenue_by_coffee_type = df.groupby('coffee_name')['money'].sum().sort_values(ascending=True)
    labels = [f'${v/1000:.0f}K' for v in revenue_by_coffee_type.values]
    fig = go.Figure(go.Bar(
        x=revenue_by_coffee_type.values,
        y=revenue_by_coffee_type.index,
        text=labels,
        textposition='auto',
        orientation='h',
        marker=dict(color=text_color)
    ))
    fig.update_layout(
        title='Revenue By Coffee Type',
        title_font_color=text_color,
        title_x=0.5,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=height,
        xaxis=dict(showgrid=False, visible=False),
        yaxis=dict(showgrid=False, title_font_color=text_color, tickfont_color=text_color)
    )
    return Safe(fig.to_html(full_html=False, include_plotlyjs=False))

def create_line_chart(df, height=450):
    if df.empty: 
        return Safe("<p>Sem dados para gráfico de linha.</p>")
    df_copy = df.copy()
    df_copy['date'] = pd.to_datetime(df_copy['date'])
    df_copy['Weekday'] = df_copy['date'].dt.day_name()
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df_copy['Weekday'] = pd.Categorical(df_copy['Weekday'], categories=weekday_order, ordered=True)
    weekly_sales_trend = df_copy.groupby('Weekday', observed=False)['money'].mean().reindex(weekday_order)
    fig = go.Figure(go.Scatter(
        x=weekly_sales_trend.index,
        y=weekly_sales_trend.values,
        mode='lines+markers',
        line=dict(color=text_color, width=3),
        marker=dict(color=text_color, size=6)
    ))
    fig.update_layout(
        title='Sales Trend By Day',
        title_font_color=text_color,
        title_x=0.5,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=height,
        xaxis=dict(showgrid=False, title_font_color=text_color, tickfont_color=text_color),
        yaxis=dict(showgrid=True, gridcolor='#eee', title_font_color=text_color, tickfont_color=text_color)
    )
    return Safe(fig.to_html(full_html=False, include_plotlyjs=False))

# --- Rota Principal ---

@rt
def index():
    """Página principal que renderiza o dashboard."""
    total_sales = df['money'].sum()
    num_transactions = len(df)
    avg_transaction_value = df['money'].mean()
    
    card_height = 350
    main_chart_height = 450
    donut_height = 350
    
    card1 = create_metric_card(total_sales, "Total Sales", is_currency=True, height=card_height)
    card2 = create_metric_card(num_transactions, "Number Of Transactions", height=card_height)
    card3 = create_metric_card(avg_transaction_value, "Avg Transaction Value", is_currency=True, height=card_height)
    
    chart_donut = create_donut_chart(df, height=donut_height)
    chart_bar = create_bar_chart(df, height=main_chart_height)
    chart_line = create_line_chart(df, height=main_chart_height)
    
    card_style = (
        "border: 1px solid #EAEAEA; border-radius: 8px; padding: 1rem; "
        "background-color: #FFFFFF; box-shadow: 0 2px 4px rgba(0,0,0,0.05);"
    )

    return (
        Title("Dashboard de Vendas de Café"),
        Container(
            H1("COFFEE SHOP SALES", style=f"text-align: center; margin-bottom: 1.5rem; color: {text_color};"),
            Grid(
                Div(card1, style=card_style),
                Div(card2, style=card_style),
                Div(card3, style=card_style),
                Div(chart_donut, style=card_style)
            ),
            Grid(
                Div(chart_bar, style=f"{card_style} margin-top: 1.5rem;"),
                Div(chart_line, style=f"{card_style} margin-top: 1.5rem;")
            ),
            Script("""
                window.addEventListener('load', () => {
                if (window.Plotly) {
                    document.querySelectorAll('.js-plotly-plot').forEach(el => {
                    window.Plotly.Plots.resize(el);
                    });
                }
                });
            """)

        )
    )

# --- Geração Estática ---
print("Gerando HTML estático...")

client = TestClient(app)
response = client.get('/')
html_content = response.text

output_file = "dashboard_estatico.html"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Sucesso! Página estática salva como '{output_file}'")
print("Você pode abrir este arquivo diretamente no seu navegador.")
