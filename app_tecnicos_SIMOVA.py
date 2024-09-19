import pandas as pd
import streamlit as st
from datetime import time
import plotly.express as px
import numpy as np

st.set_page_config(
    page_title='Reporte SIMOVA',
    page_icon=":clipboard:",  
    layout="wide")

st.title('Reporte de Registros de SIMOVA')
john_deere_colors = ['#A3C940', '#7A9A2A', '#FFD100', '#F6E8C3']  # Ejemplo de colores

@st.cache_data
def load_data(file):
    data=pd.read_excel(file,header=1)
    return data

with st.sidebar:
    st.header("Configuración")
    uploaded_file=st.file_uploader("Elija un archivo")

if uploaded_file is None:
    st.info("Cargue un archivo",icon="🚨")
    st.stop()
df=load_data(uploaded_file)
df = df.dropna(subset=['Nome Técnico'])


# Marcación Entrada
df['Hora Entrada']= pd.to_datetime(df['Hora Entrada'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
hora_referencia = time(8,45,0)
df['Cumple Ingreso a tiempo'] = (df['Hora Entrada'].dt.time <= hora_referencia).astype(int)

#Horas improductivas
df['Horas Paradas Improd.'] = pd.to_timedelta(df['Horas Paradas Improd.'])
df['Cumple Menos de una hora improd.'] = (df['Horas Paradas Improd.'] <= pd.Timedelta(hours=1)).astype(int)

# Marcacion de salida
df['Hora Saída'] = pd.to_datetime(df['Hora Saída'], format='%d/%m/%Y %H:%M:%S')
inicio = pd.to_datetime('16:30:00').time()
fin = pd.to_datetime('19:00:00').time()
df['Cumple Salida Correcta'] = ((df['Hora Saída'].dt.time >= inicio) & (df['Hora Saída'].dt.time <= fin)).astype(int)

# Traslado
df['Total Horas Deslocamento']=pd.to_timedelta(df['Total Horas Deslocamento'])

# General
df['Calificacion General'] = ((df['Cumple Ingreso a tiempo'] + df['Cumple Menos de una hora improd.'] + df['Cumple Salida Correcta'])==3).astype(int)
df['Fecha'] = df['Hora Entrada'].dt.date

with st.expander("Previsualización de datos"):
    st.dataframe(df)

primer_dia=df['Hora Entrada'].dt.date.min()
ultimo_dia=df['Hora Entrada'].dt.date.max()
cantidad_tecnicos = df['Nome Técnico'].nunique()
diferencia_dias = ultimo_dia - primer_dia
# Crear un rango de fechas entre el primer y el último día
rango_fechas = pd.date_range(start=primer_dia, end=ultimo_dia)
# Filtrar los días que no sean domingo (el día 6 en pandas corresponde al domingo)
dias_no_domingo = len(rango_fechas[rango_fechas.weekday != 6])

st.text(f'Fecha del Reporte: Entre {primer_dia} y {ultimo_dia}')
st.text(f'días laborales: {dias_no_domingo}')
st.text(f'Cantidad de técnicos: {cantidad_tecnicos}')


# Agrupar los datos por fecha y técnico
grupoxtecnico_df = df.groupby(['Nome Técnico']).agg({
    'Cumple Ingreso a tiempo': 'sum',
    'Cumple Menos de una hora improd.': 'sum',
    'Cumple Salida Correcta': 'sum',
    'Calificacion General': 'sum',
}).reset_index()

grupoxtecnico_df.iloc[:, 1:] = grupoxtecnico_df.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')
grupoxtecnico_df.iloc[:, 1:] = grupoxtecnico_df.iloc[:, 1:] / dias_no_domingo


# Agrupar los datos por fecha y técnico
grouped_df = df.groupby(['Fecha', 'Nome Técnico']).agg({
    'Cumple Ingreso a tiempo': 'sum',
    'Cumple Menos de una hora improd.': 'sum',
    'Cumple Salida Correcta': 'sum',
    'Calificacion General': 'sum'
}).reset_index()


# Selector para el indicador, con 'Calificacion General' como opción por defecto
indicator = st.selectbox(
    "Selecciona el indicador a visualizar:",
    ['Cumple Ingreso a tiempo', 'Cumple Menos de una hora improd.', 'Cumple Salida Correcta', 'Calificacion General'],
    index=3  
)

# Ordenar el DataFrame por el indicador seleccionado, de mayor a menor
grupoxtecnico_df_sorted = grupoxtecnico_df.sort_values(by=indicator, ascending=False)

# Crear gráfico de barras utilizando Plotly
fig = px.bar(
    grupoxtecnico_df_sorted,  # Usar el DataFrame ordenado
    x='Nome Técnico',         # Eje x es el nombre del técnico
    y=indicator,              # Eje y es el indicador seleccionado
    title=f'{indicator} por Técnico',  # Título del gráfico
    labels={'Nome Técnico': 'Nombre del Técnico', indicator: indicator},  # Etiquetas
    color=indicator,          # Colorear las barras según el indicador
    color_continuous_scale=px.colors.sequential.Aggrnyl  # Paleta de colores (puedes cambiarla)
)

# Personalizar el gráfico
fig.update_layout(
    xaxis_title='Nombre del Técnico',
    yaxis_title=indicator,
    title={'x': 0.5},  # Centrar el título
    template='plotly_white'  # Usar un tema más limpio
)

# Mostrar gráfico en Streamlit
st.plotly_chart(fig)

# Colores de John Deere
john_deere_colors = ['#FD3500', '#367C2B']  # Naranja y verde oscuro

# Crear una tabla de contingencia
heatmap_data = df.pivot_table(index='Nome Técnico', columns='Fecha', values=indicator, fill_value=0)

# Calcular el valor total del indicador por técnico
tech_order = heatmap_data.sum(axis=1).sort_values(ascending=False).index

# Reordenar el DataFrame según el valor total del indicador
heatmap_data = heatmap_data.reindex(index=tech_order)

# Asegúrate de que las columnas de fechas son del tipo datetime
heatmap_data.columns = pd.to_datetime(heatmap_data.columns)

# Crear un mapa de calor
fig = px.imshow(
    heatmap_data,
    labels=dict(x="Fecha", y="Nome Técnico", color=indicator),
    color_continuous_scale=[(0, john_deere_colors[0]), (1, john_deere_colors[1])],  # Colores de John Deere
    aspect="auto"
)

# Personalizar el gráfico
fig.update_layout(
    title=f'Mapa de {indicator} por Técnico y Fecha',
    xaxis_title='Fecha',
    yaxis_title='Nombre Técnico',
    xaxis=dict(
        tickmode='array',
        tickvals=list(range(len(heatmap_data.columns))),
        ticktext=heatmap_data.columns.strftime('%d-%m-%Y'),  # Formato más claro
        tickangle=45,  # Ángulo de las etiquetas
        title_font=dict(size=14),  # Tamaño de fuente del título del eje x
        tickfont=dict(size=10, color='red')  # Tamaño de fuente de las etiquetas
    ),
    yaxis=dict(
        tickmode='array',
        tickvals=list(range(len(heatmap_data.index))),
        ticktext=heatmap_data.index,  # Técnicos ordenados
        title_font=dict(size=14),  # Tamaño de fuente del título del eje y
        tickfont=dict(size=10)  # Tamaño de fuente de las etiquetas
    ),
    coloraxis_colorbar=dict(
        title=indicator,
        tickvals=[0, 1],
        ticktext=["No Cumple", "Cumple"]
    )
)

# Mostrar el mapa de calor en Streamlit
st.plotly_chart(fig)