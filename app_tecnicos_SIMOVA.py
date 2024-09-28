import pandas as pd
import streamlit as st
from datetime import time
import plotly.express as px
import plotly.graph_objs as go
import numpy as np
import matplotlib.pyplot as plt  # Importar matplotlib
import seaborn as sns
import locale

# Configurar el idioma a español
#locale.setlocale(locale.LC_TIME, 'es_ES.utf8')

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

# Lista con los nuevos nombres de columna
columnas_portugues = [
    'Código Técnico', 'Nome Técnico', 'Função', 'Filial', 'Hora Entrada', 
    'Hora Saída', 'Total Horas Turno', 'Horas Paradas Prod.', 'Horas Paradas Improd.',
    'Total Horas Perdas', 'Total Horas Trabalhadas', 'Total Horas Deslocamento']

# Cambiar los nombres de las columnas del DataFrame
df.columns = columnas_portugues

df = df.dropna(subset=['Nome Técnico'])


# Marcación Entrada
df['Hora Entrada']= pd.to_datetime(df['Hora Entrada'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
hora_1= time(4,0,0)
hora_2 = time(8,45,0)
df['Cumple Ingreso a tiempo'] = ((df['Hora Entrada'].dt.time <= hora_2) & (df['Hora Entrada'].dt.time >= hora_1)).astype(int)

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
dias_no_domingo = len(rango_fechas)

st.text(f'Fecha del Reporte: Entre {primer_dia} y {ultimo_dia}')
st.text(f'días de registro: {dias_no_domingo }')
st.text(f'Cantidad de técnicos: {cantidad_tecnicos}')


# Agrupar los datos por fecha y técnico
grupoxtecnico_df = df.groupby(['Nome Técnico']).agg({
    'Cumple Ingreso a tiempo': 'sum',
    'Cumple Menos de una hora improd.': 'sum',
    'Cumple Salida Correcta': 'sum',
    'Calificacion General': 'sum',
}).reset_index()

grupoxtecnico_df.iloc[:, 1:] = grupoxtecnico_df.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')
grupoxtecnico_df.iloc[:, 1:] = grupoxtecnico_df.iloc[:, 1:]


# Agrupar los datos por fecha y técnico
grouped_df = df.groupby(['Fecha', 'Nome Técnico']).agg({
    'Cumple Ingreso a tiempo': 'sum',
    'Cumple Menos de una hora improd.': 'sum',
    'Cumple Salida Correcta': 'sum',
    'Calificacion General': 'sum'
}).reset_index()


# Selector para el indicador, con 'Calificacion General' como opción por defecto
#indicator = st.selectbox(
#    "Selecciona el indicador a visualizar:",
#    ['Cumple Ingreso a tiempo', 'Cumple Menos de una hora improd.', 'Cumple Salida Correcta', 'Calificacion General'],
#    index=3  
#)


indicator1 ='Cumple Ingreso a tiempo'
indicator2='Cumple Menos de una hora improd.'
indicator3='Cumple Salida Correcta'
indicator4='Calificacion General'

def graficos(indicator):
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
        color_continuous_scale=px.colors.sequential.Aggrnyl  # Paleta de colores
    )

    # Personalizar el gráfico de barras
    fig.update_layout(
        xaxis_title='Nombre del Técnico',
        yaxis_title=indicator,
        template='plotly_white'  # Usar un tema más limpio
    )

    # Colores de John Deere
    john_deere_colors = ['#FD3500', '#367C2B']  # Naranja y verde oscuro

    # Crear una tabla de contingencia (heatmap_data)
    heatmap_data = df.pivot_table(index='Nome Técnico', columns='Fecha', values=indicator, fill_value=0)

    # Calcular el valor total del indicador por técnico
    tech_order = heatmap_data.sum(axis=1).sort_values(ascending=True).index

    # Reordenar el DataFrame según el valor total del indicador
    heatmap_data = heatmap_data.reindex(index=tech_order)

    # Asegúrate de que las columnas de fechas son del tipo datetime
    heatmap_data.columns = pd.to_datetime(heatmap_data.columns)

    # Convertir las fechas a formato de cadena con día de la semana en español
    heatmap_data.columns = heatmap_data.columns.strftime('%A %d-%m-%Y')  # Ej: lunes 01-01-2024

    # Crear el heatmap con Plotly
    heatmap_fig = go.Figure(
        data=go.Heatmap(
            z=heatmap_data.values,  # Los valores del heatmap
            x=heatmap_data.columns,  # Etiquetas del eje X (fechas)
            y=heatmap_data.index,    # Etiquetas del eje Y (nombres de técnicos)
            colorscale=john_deere_colors,  # Aplicar los colores personalizados
            text=heatmap_data.values,  # Mostrar los valores dentro de las celdas
            hoverinfo='text',         # Información de hover al pasar sobre la celda
            showscale=True,           # Mostrar la barra de colores
            zmin=heatmap_data.min().min(),  # Definir el valor mínimo del color
            zmax=heatmap_data.max().max(),  # Definir el valor máximo del color
        )
    )
    # Ajustes en las etiquetas del eje Y
    heatmap_fig.update_layout(
        yaxis=dict(
            tickfont=dict(size=10)  # Ajustar el tamaño de las etiquetas del eje Y
        ),
        margin=dict(l=150)  # Ajustar el margen izquierdo para dar más espacio a las etiquetas
    )

    # Simular espaciado entre celdas (agregar bordes blancos finos)
    heatmap_fig.update_traces(
        hoverongaps=False,  # Evitar mostrar información en celdas sin valor
        xgap=0.5,  # Espaciado horizontal entre celdas
        ygap=0.5   # Espaciado vertical entre celdas
    )

    # Personalizar el layout del heatmap
    heatmap_fig.update_layout(
        title=dict(text=f'Cumplimiento de {indicator} por Fecha'),
        xaxis_title='Fecha',
        yaxis_title='Nombre Técnico',
    )

    return fig, heatmap_fig

# Llamar a la función y mostrar los gráficos en Streamlit
fig, heatmap_fig = graficos(indicator1)
#st.plotly_chart(fig)
st.plotly_chart(heatmap_fig)

fig2, heatmap_fig2 = graficos(indicator2)
#st.plotly_chart(fig2)
st.plotly_chart(heatmap_fig2)

fig3, heatmap_fig3 = graficos(indicator3)
#st.plotly_chart(fig3)
st.plotly_chart(heatmap_fig3)

fig4, heatmap_fig4 = graficos(indicator4)
#st.plotly_chart(fig4)
st.plotly_chart(heatmap_fig4)
