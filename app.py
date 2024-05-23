import streamlit as st
import pandas as pd
import os
from datetime import datetime
import pytz
import time
import numpy as np

# Configurar la página
st.set_page_config(page_title='Gestión de Gastos e Ingresos',
                   page_icon='💼',
                   layout='centered',
                   initial_sidebar_state='auto')

def load_template():
    template_path = "Control Gastos Ingresos.xlsx"
    if os.path.exists(template_path):
        return pd.read_excel(template_path, sheet_name=None, engine='openpyxl')
    else:
        st.error("La plantilla de Excel no se encuentra.")
        return {}

def main():
    st.title('Gestión de Gastos e Ingresos')
    st.write('Sube tu archivo de Excel para comenzar a gestionar tus gastos e ingresos o comienza con la plantilla predeterminada.')

    # Estado de la aplicación para controlar el archivo actual
    if 'file_source' not in st.session_state:
        st.session_state.file_source = 'default'

    # Botón para cambiar entre usar plantilla y cargar archivo propio
    if st.session_state.file_source == 'default':
        if st.button('Usar plantilla predeterminada'):
            st.session_state.sheets = load_template()
            if st.session_state.sheets:
                st.session_state.df = st.session_state.sheets["Registro"]
                st.session_state.categories = st.session_state.sheets["Categorías"]
                st.session_state.file_source = 'uploaded'
            st.rerun()
    else:
        if st.button('Cambiar a cargar archivo propio'):
            st.session_state.file_source = 'default'
            st.rerun()

    # Cargar archivo Excel o usar plantilla
    if st.session_state.file_source == 'default':
        uploaded_file = st.file_uploader("Elige un archivo Excel", type="xlsx")
        if uploaded_file:
            st.session_state.sheets = pd.read_excel(uploaded_file, sheet_name=None, engine='openpyxl')
            if st.session_state.sheets:
                st.session_state.df = st.session_state.sheets["Registro"]
                st.session_state.categories = st.session_state.sheets["Categorías"]
                st.session_state.file_source = 'uploaded'
            st.rerun()

    if 'df' in st.session_state and not st.session_state.df.empty:
        df = st.session_state.df
        categories = st.session_state.categories

        # Extraer los meses únicos del dataframe
        unique_months = df.iloc[12:, 1].dropna().unique().tolist()

        # Agregar una opción "Todos" a la lista de meses
        unique_months.insert(0, 'Todos')

        # Crear un selectbox con los meses
        mes = st.selectbox('Mes 📅', unique_months)

        # Filtrar el dataframe basado en la selección del usuario
        if mes != 'Todos':
            registros = df[df.iloc[:, 1] == mes].dropna(how='all')
            registros = registros.reset_index(drop=True)
        else:
            registros = df.iloc[11:, :].dropna(how='all')
            registros = registros.reset_index(drop=True)

        registros.columns = df.iloc[10, :].dropna().tolist()
        registros['Fecha'] = pd.to_datetime(registros['Fecha'],
                                            format='%d-%m-%Y')
        registros['Fecha'] = registros['Fecha'].dt.strftime('%d-%m-%Y')

        # Calcular los totales para el mes seleccionado
        ingresos = registros[registros['Ingreso / Gasto / Inversión'] == 'Ingreso']['Valor'].sum()
        gastos = registros[registros['Ingreso / Gasto / Inversión'] == 'Gasto']['Valor'].sum()
        inversiones = registros[registros['Ingreso / Gasto / Inversión'] == 'Inversión']['Valor'].sum()
        balance = ingresos - gastos - inversiones

        # Mostrar los totales en la interfaz de usuario
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                f'<div style="text-align: center">'
                f'<b>Total Ingresos del Mes 💰:</b><br>${ingresos:,.0f}'
                f'</div>', 
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(
                f'<div style="text-align: center">'
                f'<b>Total Gastos del Mes 💸:</b><br>${gastos:,.0f}'
                f'</div>', 
                unsafe_allow_html=True
            )

        with col3:
            st.markdown(
                f'<div style="text-align: center">'
                f'<b>Total Inversiones del Mes 📈:</b>'
                f'<br>${inversiones:,.0f}'
                f'</div>',
                unsafe_allow_html=True
            )

        st.markdown(
            f'<div style="text-align: center">'
            f'<b>Balance del Mes 🔍:</b><br>${balance:,.0f}'
            f'</div>', 
            unsafe_allow_html=True
        )

        # Inicializar st.session_state.registros si no existe
        if "registros" not in st.session_state:
            st.session_state.registros = registros

        # Mostrar registros del mes seleccionado
        st.dataframe(st.session_state.registros, use_container_width=True)

        # Formatear la fecha
        meses = [
            'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
            'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
            ]


        timezone = pytz.timezone('America/Bogota')
        fecha_actual = datetime.now(timezone).date()
        # Opciones para añadir, eliminar o modificar registros
        st.sidebar.title("Opciones")

        # Añadir nuevo registro
        with st.sidebar.expander("Añadir nuevo registro"):
            new_data = {}

            # Almacenar el tipo de registro seleccionado en el estado de sesión
            new_data['Fecha'] = st.date_input('Ingrese Fecha 📅', value=fecha_actual, format="DD/MM/YYYY")
            if 'tipo_registro' not in st.session_state:
                st.session_state.tipo_registro = categories.iloc[0, 0]
            new_data['Ingreso / Gasto / Inversión'] = st.selectbox('Tipo de Registro', categories.iloc[:, 0].dropna().tolist(), key='tipo_registro')

            # Actualizar el concepto basado en el tipo de registro seleccionado
            tipo_registro = st.session_state.tipo_registro

            conceptos = categories[tipo_registro].dropna().tolist()
            new_data['Concepto'] = st.selectbox('Concepto', conceptos, key='concepto')
            new_data['Detalle'] = st.text_input('Detalle')
            new_data['Valor'] = st.number_input('Valor 💵', min_value=0.0, format='%f')
            if st.button('Añadir'):
                new_data['Mes'] = meses[new_data['Fecha'].month - 1]  # Autocompletar el mes
                # Asegurarse de que new_data['Fecha'] es de tipo datetime
                if not isinstance(new_data['Fecha'], pd.Timestamp):
                    new_data['Fecha'] = pd.to_datetime(new_data['Fecha'])

                # Darle el formato 'DD/MM/YYYY' a new_data['Fecha']
                new_data['Fecha'] = new_data['Fecha'].strftime('%d-%m-%Y')
                new_record = pd.DataFrame([new_data])
                new_record = new_record.reindex(columns=registros.columns)
                # Añadir new_record a registros
                registros = pd.concat([registros, new_record], ignore_index=True)
                # Añadir new_record a st.session_state.registros
                st.session_state.registros = pd.concat([st.session_state.registros, new_record], ignore_index=True)
                st.write("Registro añadido:")
                st.dataframe(new_record, use_container_width=True)
                time.sleep(2)
                st.rerun()

        # Modificar registro
        with st.sidebar.expander("Modificar registro"):
            row_index = st.number_input('Ingrese el índice del registro a modificar', min_value=0, max_value=len(st.session_state.registros)-1, key='row_index_modificar')
            registros = st.session_state.registros
            new_data = {}
            new_data['Fecha'] = st.date_input('Ingrese Fecha 📅', value=datetime.strptime(registros.at[row_index, 'Fecha'], '%d-%m-%Y'), format="DD/MM/YYYY", key='fecha')
            if 'tipo_registro_modificar' not in st.session_state:
                st.session_state.tipo_registro_modificar = categories.iloc[0, 0]
            new_data['Ingreso / Gasto / Inversión'] = st.selectbox('Tipo de Registro', categories.iloc[:, 0].dropna().tolist(), index=categories.iloc[:, 0].dropna().tolist().index(registros.at[row_index, 'Ingreso / Gasto / Inversión']), key='tipo_registro_modificar')
            
            # Actualizar el concepto basado en el tipo de registro seleccionado
            tipo_registro_modificar = st.session_state.tipo_registro_modificar
            conceptos_modificar = categories[tipo_registro_modificar].dropna().tolist()
            new_data['Concepto'] = st.selectbox('Concepto', conceptos_modificar, index=None, key='concepto_modificar', placeholder=registros.at[row_index, 'Concepto'])
            if new_data['Concepto'] is None:
                new_data['Concepto'] = registros.at[row_index, 'Concepto']
            
            new_data['Detalle'] = st.text_input('Detalle', value=registros.at[row_index, 'Detalle'], key='detalle_modificar')
            new_data['Valor'] = st.number_input('Valor 💵', min_value=0, value=int(registros.at[row_index, 'Valor']), key="valor_modificar")
            if st.button('Modificar'):
                new_data['Mes'] = meses[new_data['Fecha'].month - 1]  # Autocompletar el mes
                # Darle el formato 'DD/MM/YYYY' a new_data['Fecha']
                new_data['Fecha'] = new_data['Fecha'].strftime('%d-%m-%Y')
                for col in registros.columns:
                    registros.at[row_index, col] = new_data[col]
                st.session_state.registros = registros
                st.write("Registro modificado:")
                st.dataframe(registros, use_container_width=True)
                time.sleep(2)
                st.rerun()

        # Eliminar registro
        with st.sidebar.expander("Eliminar registro"):
            row_index = st.number_input('Ingrese el índice del registro a eliminar', min_value=0, max_value=len(registros)-1)
            if st.button('Eliminar'):
                registros = registros.drop(registros.index[row_index]).reset_index(drop=True)
                st.session_state.registros = registros
                st.write("Registro eliminado:")
                st.dataframe(registros, use_container_width=True)
                time.sleep(2)
                st.rerun()

        # Descargar archivo modificado
        if st.button("Descargar Excel modificado"):
            timestamp = datetime.now(timezone).strftime("%Y%m%d%H%M%S")
            output_path = f"Control Gastos Ingresos {timestamp}.xlsx"

            # Número de filas vacías
            num_empty_rows = 2

            # Crear un DataFrame vacío con el número de filas que quieres añadir
            empty_rows = pd.DataFrame(np.nan, index=range(num_empty_rows), columns=st.session_state.df.columns)

            # Insertar las filas vacías en la posición que quieras
            st.session_state.df = pd.concat([st.session_state.df.iloc[:6], empty_rows, st.session_state.df.iloc[6:]]).reset_index(drop=True)

            
            # Mantén solo las filas hasta la 11 en df
            st.session_state.df = st.session_state.df.iloc[:13]

            # Asegurarse de que st.session_state.df tenga al menos 13 filas
            if len(st.session_state.df) < len(st.session_state.registros) + 1:
                num_empty_rows = len(st.session_state.registros)
                empty_rows = pd.DataFrame(np.nan, index=range(num_empty_rows), columns=st.session_state.df.columns)
                st.session_state.df = pd.concat([st.session_state.df, empty_rows]).reset_index(drop=True)

            # Hacer una copia de st.session_state.registros
            registros_guardar = st.session_state.registros.copy()


            # Resetear los nombres de las columnas de st.session_state.registros para que coincidan con los de st.session_state.df
            registros_guardar.columns = st.session_state.df.columns

            # Concatenar st.session_state.registros debajo de la fila 12 de st.session_state.df
            st.session_state.df = pd.concat([st.session_state.df.iloc[:13], registros_guardar], axis=0, ignore_index=True)

            # Guardar el archivo Excel modificado
            st.session_state.df.to_excel(output_path, index=False)

            st.write("Archivo modificado guardado. Haz click en el botón para descargar:") # Leer el archivo Excel como bytes
            with open(output_path, 'rb') as f:
                bytes_data = f.read()

            # Crear un botón de descarga para el archivo Excel
            st.download_button(
                label="Descargar Excel actualizado",
                data=bytes_data,
                file_name=output_path,
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )

if __name__ == "__main__":
    main()
