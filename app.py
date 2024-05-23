"""
Este script de Python es una aplicación web que permite a los usuarios cargar
un archivo de Excel con datos de gastos e ingresos y gestionarlos. Los usuarios
pueden cargar su propio archivo de Excel o usar una plantilla predeterminada
para comenzar a gestionar sus gastos e ingresos.

La aplicación permite a los usuarios ver los totales de ingresos, gastos e
inversiones para un mes seleccionado, así como añadir, modificar y eliminar
registros de gastos e ingresos.
"""

import os
import time
import pytz
from datetime import datetime
import numpy as np
import pandas as pd
import streamlit as st


# Configurar la página
st.set_page_config(page_title='Gestión de Gastos e Ingresos',
                   page_icon='💼',
                   layout='centered',
                   initial_sidebar_state='auto')


def load_template():
    """
    Cargar la plantilla de Excel con los datos de gastos e ingresos.

    Args:
        None

    Returns:
        dict: Un diccionario con las hojas del archivo de Excel cargado.
    """
    # Ruta de la plantilla de Excel
    template_path = "Control Gastos Ingresos.xlsx"

    # Verificar si la plantilla de Excel existe
    if os.path.exists(template_path):
        # Leer el archivo de Excel y devolver un diccionario con las hojas
        return pd.read_excel(template_path, sheet_name=None, engine='openpyxl')
    else:
        # Mostrar un mensaje de error si la plantilla de Excel no se encuentra
        st.error("La plantilla de Excel no se encuentra.")
        return {}


def main():
    """
    Función principal que ejecuta la aplicación web de gestión de gastos e
    ingresos.

    Args:
        None

    Returns:
        None
    """
    # Título de la aplicación
    st.title('Gestión de Gastos e Ingresos')

    # Descripción de la aplicación
    st.write('Sube tu archivo de Excel para comenzar a gestionar tus gastos e \
             ingresos o comienza con la plantilla predeterminada.')

    # Estado de la aplicación para controlar el archivo actual
    if 'file_source' not in st.session_state:
        st.session_state.file_source = 'default'

    # Botón para cambiar entre usar plantilla y cargar archivo propio
    if st.session_state.file_source == 'default':
        # Botón para cargar la plantilla predeterminada
        if st.button('Usar plantilla predeterminada'):
            # Cargar la plantilla de Excel
            st.session_state.sheets = load_template()
            # Verificar si se cargaron las hojas del archivo de Excel
            if st.session_state.sheets:
                st.session_state.df = st.session_state.sheets["Registro"]
                st.session_state.categories = st.session_state.sheets[
                                                                "Categorías"
                                                                    ]
                # Cambiar el estado del archivo a 'uploaded'
                st.session_state.file_source = 'uploaded'
            st.rerun()
    else:
        # Botón para cambiar a cargar archivo propio
        if st.button('Cambiar a cargar archivo propio'):
            st.session_state.file_source = 'default'
            st.rerun()

    # Cargar archivo Excel o usar plantilla
    if st.session_state.file_source == 'default':
        uploaded_file = st.file_uploader("Elige un archivo Excel", type="xlsx")
        if uploaded_file:
            st.session_state.sheets = pd.read_excel(uploaded_file,
                                                    sheet_name=None,
                                                    engine='openpyxl')
            if st.session_state.sheets:
                st.session_state.df = st.session_state.sheets["Registro"]
                st.session_state.categories = st.session_state.sheets[
                                                                "Categorías"
                                                                    ]
                st.session_state.file_source = 'uploaded'
            st.rerun()

    if 'df' in st.session_state and not st.session_state.df.empty:
        df = st.session_state.df
        categories = st.session_state.categories

        # Extraer los meses únicos del dataframe y excluir "-"
        unique_months = df.iloc[12:, 1][df.iloc[12:, 1] != "-"]
        unique_months = unique_months.dropna().unique().tolist()

        # Agregar una opción "Todos" a la lista de meses
        unique_months.insert(0, 'Todos')

        # Crear un selectbox con los meses
        mes = st.selectbox('Mes 📅', unique_months)

        if 'registros' in st.session_state:
            registros = st.session_state.registros

            # Reemplazar "-" por NaN en el dataframe
            registros = registros.replace('-', np.nan)

            # Filtrar el dataframe basado en la selección del usuario
            if mes != 'Todos':
                registros = registros[registros.iloc[:, 1] == mes]
                registros = registros.dropna(how='all')
                registros = registros.reset_index(drop=True)
            else:
                registros = registros.iloc[:, :].dropna(how='all')
                registros = registros.reset_index(drop=True)

        else:

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

        def sumar_valor(registros, tipo):
            """
            Sumar los valores de ingresos, gastos o inversiones en los
            registros.

            Args:
                registros (pd.DataFrame): Un DataFrame con los registros de
                                          gastos e ingresos.
                tipo (str): El tipo de registro ('Ingreso', 'Gasto' o
                            'Inversión').

            Returns:
                float: La suma de los valores de ingresos, gastos o
                       inversiones.
            """
            return registros[
                        registros['Ingreso / Gasto / Inversión'] == tipo
                            ]['Valor'].sum()

        ingresos = sumar_valor(registros, 'Ingreso')
        gastos = sumar_valor(registros, 'Gasto')
        inversiones = sumar_valor(registros, 'Inversión')
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
        st.dataframe(registros, use_container_width=True)

        # Formatear la fecha
        meses = [
            'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
            'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
            ]

        timezone = pytz.timezone('America/Bogota')
        fecha_actual = datetime.now(timezone).date()
        # Opciones para añadir, eliminar o modificar registros
        st.sidebar.title("Opciones")

        # Añadir nuevo registro
        with st.sidebar.expander("Añadir nuevo registro"):
            new_data = {}

            # Almacenar el tipo de registro seleccionado en el estado de sesión
            new_data['Fecha'] = st.date_input('Ingrese Fecha 📅',
                                              value=fecha_actual,
                                              format="DD/MM/YYYY")
            if 'tipo_registro' not in st.session_state:
                st.session_state.tipo_registro = categories.iloc[0, 0]
            categorias = categories.iloc[:, 0].dropna().tolist()
            new_data['Ingreso / Gasto / Inversión'] = st.selectbox(
                                                            'Tipo de Registro',
                                                            categorias,
                                                            key='tipo_registro'
                                                            )
            # Actualizar el concepto basado en el tipo de registro seleccionado
            tipo_registro = st.session_state.tipo_registro

            conceptos = categories[tipo_registro].dropna().tolist()
            new_data['Concepto'] = st.selectbox('Concepto',
                                                conceptos,
                                                key='concepto')
            new_data['Detalle'] = st.text_input('Detalle')
            new_data['Valor'] = st.number_input('Valor 💵',
                                                min_value=0.0,
                                                format='%f')
            if st.button('Añadir'):
                new_data['Mes'] = meses[new_data['Fecha'].month - 1]
                # Asegurarse de que new_data['Fecha'] es de tipo datetime
                if not isinstance(new_data['Fecha'], pd.Timestamp):
                    new_data['Fecha'] = pd.to_datetime(new_data['Fecha'])

                # Darle el formato 'DD/MM/YYYY' a new_data['Fecha']
                new_data['Fecha'] = new_data['Fecha'].strftime('%d-%m-%Y')
                new_record = pd.DataFrame([new_data])
                new_record = new_record.reindex(columns=registros.columns)
                # Añadir new_record a registros
                registros = pd.concat([registros, new_record],
                                      ignore_index=True)
                # Añadir new_record a st.session_state.registros
                st.session_state.registros = pd.concat(
                                                [st.session_state.registros,
                                                 new_record],
                                                ignore_index=True
                                                )
                st.write("Registro añadido:")
                st.dataframe(new_record, use_container_width=True)
                time.sleep(2)
                st.rerun()

        # Modificar registro
        with st.sidebar.expander("Modificar registro"):
            if len(st.session_state.registros) == 0:
                st.warning("No hay registros para modificar.")
                st.stop()

            else:
                row_index = st.number_input(
                                'Ingrese el índice del registro a modificar',
                                min_value=0,
                                max_value=len(st.session_state.registros)-1,
                                key='row_index_modificar'
                                )
            registros = st.session_state.registros
            new_data = {}
            new_data['Fecha'] = st.date_input('Ingrese Fecha 📅',
                                              value=datetime.strptime(
                                                        registros.at[row_index,
                                                                     'Fecha'],
                                                        '%d-%m-%Y'
                                                        ),
                                              format="DD/MM/YYYY",
                                              key='fecha'
                                              )
            if 'tipo_registro_modificar' not in st.session_state:
                st.session_state.tipo_registro_modificar = \
                    categories.iloc[0, 0]
            new_data['Ingreso / Gasto / Inversión'] = \
                st.selectbox('Tipo de Registro',
                             categories.iloc[:, 0].dropna().tolist(),
                             index=categories.iloc[:, 0].dropna().tolist().
                             index(registros.at[
                                    row_index, 'Ingreso / Gasto / Inversión'
                                    ]),
                             key='tipo_registro_modificar')

            # Actualizar el concepto basado en el tipo de registro seleccionado
            tipo_registro_modificar = st.session_state.tipo_registro_modificar
            conceptos_modificar = categories[tipo_registro_modificar]
            conceptos_modificar = conceptos_modificar.dropna().tolist()
            new_data['Concepto'] = st.selectbox('Concepto',
                                                conceptos_modificar,
                                                index=None,
                                                key='concepto_modificar',
                                                placeholder=registros.at[
                                                                    row_index,
                                                                    'Concepto'
                                                                    ]
                                                )
            if new_data['Concepto'] is None:
                new_data['Concepto'] = registros.at[row_index, 'Concepto']

            new_data['Detalle'] = st.text_input('Detalle',
                                                value=registros.at[
                                                        row_index, 'Detalle'
                                                        ],
                                                key='detalle_modificar')
            new_data['Valor'] = st.number_input('Valor 💵', min_value=0,
                                                value=int(registros.at[
                                                            row_index, 'Valor'
                                                            ]
                                                          ),
                                                key="valor_modificar")
            if st.button('Modificar'):
                new_data['Mes'] = meses[new_data['Fecha'].month - 1]
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
            row_index = st.number_input(
                                'Ingrese el índice del registro a eliminar',
                                min_value=0,
                                max_value=len(registros)-1
                                )
            if st.button('Eliminar'):
                registros = registros.drop(registros.index[row_index])
                registros = registros.reset_index(drop=True)
                st.session_state.registros = registros
                st.write("Registro eliminado:")
                st.dataframe(registros, use_container_width=True)
                time.sleep(2)
                st.rerun()

        import openpyxl

        # Descargar archivo modificado
        if st.button("Descargar Excel modificado"):
            template_path = "Control Gastos Ingresos.xlsx"
            wb = openpyxl.load_workbook(template_path)
            ws = wb["Registro"]

            # Actualizar solo las filas a partir de la fila 13 con los
            # valores de registros
            for i, row in enumerate(
                            st.session_state.registros.itertuples(index=False),
                            start=13
                            ):
                column_index = 1
                for j, value in enumerate(row):
                    # Incrementar column_index para omitir la columna
                    # B del Excel
                    if j == 1:
                        column_index += 1
                    else:
                        ws.cell(row=i, column=column_index, value=value)
                        column_index += 1

            # Guardar el archivo Excel modificado
            timestamp = datetime.now(pytz.timezone('America/Bogota'))
            timestamp = timestamp.strftime("%Y%m%d%H%M%S")
            output_path = f"Control Gastos Ingresos {timestamp}.xlsx"
            wb.save(output_path)

            st.write("Archivo modificado guardado. \
                     Haz click en el botón para descargar:")
            with open(output_path, 'rb') as f:
                bytes_data = f.read()

            # Crear un botón de descarga para el archivo Excel
            st.download_button(
                label="Descargar Excel actualizado",
                data=bytes_data,
                file_name=output_path,
                mime='application/vnd.openxmlformats-officedocument.\
                      spreadsheetml.sheet',
            )


if __name__ == "__main__":
    main()
