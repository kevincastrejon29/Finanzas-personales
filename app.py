import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from streamlit_gsheets import GSheetsConnection

# Configuración limpia sin icono de página
st.set_page_config(page_title="Finanzas personales", layout="wide")

# --- SISTEMA DE AUTENTICACIÓN ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("Acceso de Seguridad")
        st.write("Por favor, ingrese sus credenciales para acceder al portal financiero.")
        with st.form("login_form"):
            usuario = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password") 
            ingresar = st.form_submit_button("Ingresar", use_container_width=True)
            if ingresar:
                if usuario == st.secrets["credenciales"]["usuario"] and password == st.secrets["credenciales"]["password"]:
                    st.session_state["autenticado"] = True
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas. Verifique e intente nuevamente.")
    st.stop() 

# --- ÁRBOL DE JERARQUÍAS ACTUALIZADO ---
SUBCATEGORIAS_GASTO = {
    "Alimentación": ["Supermercado", "Restaurantes y delivery", "Cafés y snacks", "Agua, bebidas, suplementos alimenticios"],
    "Vivienda": ["Arriendo / hipoteca", "Servicios básicos (agua, luz, gas)", "Internet y TV", "Mantenimiento y reparaciones", "Muebles y equipamiento", "Suministros y aseo del hogar"],
    "Transporte": ["Transporte público", "Combustible", "Mantenimiento vehicular", "Estacionamientos y peajes", "Taxi (Uber, InDrive, Didi)"],
    "Salud y bienestar": ["Seguro médico", "Consultas y medicamentos", "Terapias", "Gimnasio", "Exámenes médicos"],
    "Aseo y cuidado personal": ["Productos de aseo", "Barbería / peluquería", "Cosmética", "Ropa interior y cuidado personal"],
    "Ropa y accesorios": ["Ropa diaria", "Calzado", "Accesorios", "Reparaciones de ropa"],
    "Educación y desarrollo": ["Cursos y certificaciones", "Libros", "Plataformas educativas", "Idiomas", "Eventos académicos"],
    "Deportes y hobbies": ["Equipamiento deportivo", "Inscripciones", "Clases", "Mantenimiento"],
    "Suscripciones y entretenimiento": ["Streaming (Netflix, Spotify, etc.)", "Videojuegos", "Cine y espectáculos", "Suscripciones digitales"],
    "Finanzas y obligaciones": ["Créditos y préstamos", "Tarjetas de crédito", "Intereses", "Comisiones bancarias", "Impuestos"],
    "Ahorro e inversión": ["Ahorro programado", "Inversiones", "Fondo de emergencia", "Jubilación"],
    "Regalos y donaciones": ["Regalos", "Donaciones", "Eventos sociales"],
    "Tecnología y comunicación": ["Teléfono móvil", "Equipos electrónicos", "Software no recurrente", "Accesorios tecnológicos"]
}

SUBCATEGORIAS_INGRESO = {
    "Sueldo": ["Pago regular", "Bono / Gratificación", "Adelanto"],
    "Devoluciones": ["Reembolso de tienda", "Devolución de terceros"],
    "Otros ingresos": ["Cachuelo / Freelance", "Venta de cosas", "Rendimientos / Intereses"]
}

# Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_transacciones():
    try:
        df = conn.read(worksheet="Transacciones", usecols=list(range(7)), ttl=0)
        df = df.dropna(how="all")
        if 'Subcategoría' not in df.columns: df['Subcategoría'] = "General"
        df['Subcategoría'] = df['Subcategoría'].fillna("General")
        df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
        return df
    except:
        return pd.DataFrame(columns=["Fecha", "Cuenta", "Tipo", "Categoría", "Subcategoría", "Monto", "Descripción"])

def cargar_prestamos():
    try:
        df = conn.read(worksheet="Prestamos", usecols=list(range(7)), ttl=0)
        df = df.dropna(how="all")
        df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
        df['Fecha_Devolucion'] = pd.to_datetime(df['Fecha_Devolucion']).dt.date
        return df
    except:
        return pd.DataFrame(columns=["Fecha", "Persona", "Monto", "Interes", "Fecha_Devolucion", "Cuenta", "Estado"])

df = cargar_transacciones()
df_p = cargar_prestamos()

st.title("Finanzas personales")
st.markdown("---")

tab_registro, tab_dashboard = st.tabs(["Registrar Transacción", "Panel de Control Ejecutivo"])

# --- PESTAÑA 1: FORMULARIO REACTIVO CON RE-INSTANCIACIÓN DINÁMICA ---
with tab_registro:
    st.subheader("Ingreso de Movimientos")
    cuentas_todas = ["Tarjeta Sueldo", "Tarjeta Gastos", "Efectivo", "Cuenta CTS"]
    cuentas_operativas = ["Tarjeta Sueldo", "Tarjeta Gastos", "Efectivo"]
    
    # Variables de control de ciclo de vida del formulario
    if "form_id" not in st.session_state: st.session_state["form_id"] = 0
    if "mensaje_exito" not in st.session_state: st.session_state["mensaje_exito"] = None

    # Desplegar notificación persistente de éxito si existe
    if st.session_state["mensaje_exito"]:
        st.success(st.session_state["mensaje_exito"])
        st.session_state["mensaje_exito"] = None # Limpiar para el siguiente ciclo

    # Estructura de captura
    col1, col2 = st.columns(2)
    with col1:
        fecha = st.date_input("Fecha de Transacción", date.today())
        tipo = st.selectbox("Tipo de Operación", ["Gasto", "Ingreso", "Transferencia", "Préstamo Otorgado", "Cobro de Préstamo"])
        # Atamos el form_id a la clave de los inputs a limpiar
        monto = st.number_input("Monto (S/)", min_value=0.0, format="%.2f", step=5.0, key=f"monto_{st.session_state['form_id']}")

    with col2:
        if tipo == "Ingreso":
            cuenta = st.selectbox("Cuenta Destino", cuentas_todas)
            categoria = st.selectbox("Categoría", list(SUBCATEGORIAS_INGRESO.keys()))
            subcategoria = st.selectbox("Subcategoría", SUBCATEGORIAS_INGRESO[categoria])
            persona = ""
            
        elif tipo == "Gasto":
            cuenta = st.selectbox("Cuenta de Origen", cuentas_operativas)
            categoria = st.selectbox("Categoría", list(SUBCATEGORIAS_GASTO.keys()))
            subcategoria = st.selectbox("Subcategoría", SUBCATEGORIAS_GASTO[categoria])
            persona = ""
            
        elif tipo == "Transferencia":
            cuenta_origen = st.selectbox("Cuenta de Origen (Salida)", cuentas_todas)
            cuenta = st.selectbox("Cuenta de Destino (Entrada)", cuentas_todas)
            categoria = "Transferencia"
            subcategoria = "Traspaso interno"
            persona = ""
            
        elif tipo == "Préstamo Otorgado":
            cuenta = st.selectbox("Cuenta de Origen", cuentas_operativas)
            persona = st.text_input("Deudor (Nombre completo)")
            interes = st.number_input("Tasa de Interés Pactada (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
            fecha_dev = st.date_input("Fecha de Vencimiento", date.today())
            categoria = "Préstamo Otorgado"
            subcategoria = f"A: {persona}"
            
        elif tipo == "Cobro de Préstamo":
            df_p_pendientes = df_p[df_p["Estado"] == "Pendiente"]
            if df_p_pendientes.empty:
                st.warning("No se registran cuentas por cobrar pendientes en el sistema.")
                st.stop()
            opciones_p = df_p_pendientes.apply(lambda x: f"{x['Persona']} | S/ {x['Monto']} (Vence: {x['Fecha_Devolucion']})", axis=1).tolist()
            prestamo_sel = st.selectbox("Seleccionar Cuenta por Cobrar", opciones_p)
            idx_sel = opciones_p.index(prestamo_sel)
            p_registro = df_p_pendientes.iloc[idx_sel]
            cuenta = st.selectbox("Cuenta de Destino (Ingreso)", cuentas_operativas)
            categoria = "Préstamo Cobrado"
            subcategoria = f"De: {p_registro['Persona']}"
            monto_final = float(p_registro['Monto']) * (1 + (float(p_registro['Interes']) / 100))
            st.success(f"Ingreso total calculado (Capital + Intereses): S/ {monto_final:,.2f}")

        # Atamos el form_id a la clave de la descripción
        descripcion = st.text_input("Descripción / Referencia (Opcional)", key=f"desc_{st.session_state['form_id']}")

    if st.button("Procesar y Guardar Transacción", type="primary", use_container_width=True):
        if descripcion.strip() == "":
            if tipo == "Transferencia": desc_guardar = f"Traspaso: {cuenta_origen} -> {cuenta}"
            elif tipo == "Préstamo Otorgado": desc_guardar = f"Préstamo otorgado a {persona}"
            elif tipo == "Cobro de Préstamo": desc_guardar = f"Liquidación de préstamo por {p_registro['Persona']}"
            else: desc_guardar = f"{categoria} — {subcategoria}"
        else:
            desc_guardar = descripcion

        # Re-lectura obligatoria de seguridad para evitar sobreescritura de datos
        df_nube = cargar_transacciones()
        df_p_nube = cargar_prestamos()

        if tipo == "Transferencia":
            nuevo_trans = pd.DataFrame([
                {"Fecha": fecha, "Cuenta": cuenta_origen, "Tipo": "Gasto", "Categoría": "Transferencia", "Subcategoría": subcategoria, "Monto": monto, "Descripción": desc_guardar},
                {"Fecha": fecha, "Cuenta": cuenta, "Tipo": "Ingreso", "Categoría": "Transferencia", "Subcategoría": subcategoria, "Monto": monto, "Descripción": desc_guardar}
            ])
            df_final = pd.concat([df_nube, nuevo_trans], ignore_index=True)
            conn.update(worksheet="Transacciones", data=df_final)
            
        elif tipo == "Préstamo Otorgado":
            nuevo_trans = pd.DataFrame([{"Fecha": fecha, "Cuenta": cuenta, "Tipo": "Gasto", "Categoría": "Préstamo Otorgado", "Subcategoría": subcategoria, "Monto": monto, "Descripción": desc_guardar}])
            df_final = pd.concat([df_nube, nuevo_trans], ignore_index=True)
            conn.update(worksheet="Transacciones", data=df_final)
            
            nuevo_p = pd.DataFrame([{"Fecha": fecha, "Persona": persona, "Monto": monto, "Interes": interes, "Fecha_Devolucion": fecha_dev, "Cuenta": cuenta, "Estado": "Pendiente"}])
            df_p_final = pd.concat([df_p_nube, nuevo_p], ignore_index=True)
            conn.update(worksheet="Prestamos", data=df_p_final)
            
        elif tipo == "Cobro de Préstamo":
            nuevo_trans = pd.DataFrame([{"Fecha": fecha, "Cuenta": cuenta, "Tipo": "Ingreso", "Categoría": "Préstamo Cobrado", "Subcategoría": subcategoria, "Monto": monto_final, "Descripción": desc_guardar}])
            df_final = pd.concat([df_nube, nuevo_trans], ignore_index=True)
            conn.update(worksheet="Transacciones", data=df_final)
            
            condicion = (df_p_nube['Persona'] == p_registro['Persona']) & (df_p_nube['Monto'] == p_registro['Monto']) & (df_p_nube['Estado'] == 'Pendiente')
            df_p_nube.loc[condicion, 'Estado'] = 'Cobrado'
            conn.update(worksheet="Prestamos", data=df_p_nube)
        else:
            nuevo_trans = pd.DataFrame([{"Fecha": fecha, "Cuenta": cuenta, "Tipo": tipo, "Categoría": categoria, "Subcategoría": subcategoria, "Monto": monto, "Descripción": desc_guardar}])
            df_final = pd.concat([df_nube, nuevo_trans], ignore_index=True)
            conn.update(worksheet="Transacciones", data=df_final)
            
        # Incrementar el ID del formulario para generar nuevos inputs limpios y guardar notificación
        st.session_state["form_id"] += 1
        st.session_state["mensaje_exito"] = "Transacción registrada e integrada exitosamente en Google Sheets."
        st.rerun()

# --- PESTAÑA 2: PANEL DE CONTROL EJECUTIVO ---
with tab_dashboard:
    if df.empty:
        st.info("No existen registros operativos para analizar.")
    else:
        df['Fecha_DT'] = pd.to_datetime(df['Fecha'])
        df['Año'] = df['Fecha_DT'].dt.year
        df['Mes_Num'] = df['Fecha_DT'].dt.month
        
        meses_es = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 
                    7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
        df['Mes'] = df['Mes_Num'].map(meses_es)

        hoy = date.today()
        año_actual = hoy.year
        mes_actual_nombre = meses_es[hoy.month]

        # Barra Lateral
        st.sidebar.header("Parámetros de Análisis")
        filtro_año = st.sidebar.selectbox("Ejercicio Fiscal (Año)", sorted(list(df['Año'].unique())), index=sorted(list(df['Año'].unique())).index(año_actual) if año_actual in df['Año'].unique() else 0)
        filtro_mes = st.sidebar.selectbox("Periodo (Mes)", list(meses_es.values()), index=list(meses_es.values()).index(mes_actual_nombre))
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("Filtros de Estructura Condicional")
        filtro_tipo_flujo = st.sidebar.selectbox("Tipo de Flujo", ["Todos los Movimientos", "Ingreso", "Gasto"])

        df_filtrado_mes = df[(df['Año'] == filtro_año) & (df['Mes'] == filtro_mes)]
        exclusiones_filtro = ['Saldo Inicial', 'Transferencia', 'Préstamo Otorgado', 'Préstamo Cobrado']
        df_base_cascade = df_filtrado_mes[~df_filtrado_mes['Categoría'].isin(exclusiones_filtro)]

        opciones_categorias = ["Todas las Categorías"]
        opciones_subcategorias = ["Todas las Subcategorías"]
        
        if filtro_tipo_flujo == "Ingreso":
            cats_reales = sorted(list(df_base_cascade[df_base_cascade['Tipo'] == 'Ingreso']['Categoría'].unique()))
            opciones_categorias += cats_reales
        elif filtro_tipo_flujo == "Gasto":
            cats_reales = sorted(list(df_base_cascade[df_base_cascade['Tipo'] == 'Gasto']['Categoría'].unique()))
            opciones_categorias += cats_reales
        else:
            cats_reales = sorted(list(df_base_cascade['Categoría'].unique()))
            opciones_categorias += cats_reales

        filtro_categoria = st.sidebar.selectbox("Segmento de Categoría", opciones_categorias)

        if filtro_categoria != "Todas las Categorías":
            subcats_reales = sorted(list(df_base_cascade[df_base_cascade['Categoría'] == filtro_categoria]['Subcategoría'].unique()))
            opciones_subcategorias += subcats_reales
        else:
            if filtro_tipo_flujo != "Todos los Movimientos":
                subcats_reales = sorted(list(df_base_cascade[df_base_cascade['Tipo'] == filtro_tipo_flujo]['Subcategoría'].unique()))
            else:
                subcats_reales = sorted(list(df_base_cascade['Subcategoría'].unique()))
            opciones_subcategorias += subcats_reales

        filtro_subcategoria = st.sidebar.selectbox("Segmento de Subcategoría", opciones_subcategorias)

        # Saldos Globales
        df['Valor_Real'] = df.apply(lambda x: x['Monto'] if x['Tipo'] == 'Ingreso' else -x['Monto'], axis=1)
        saldo_sueldo = df[df["Cuenta"] == "Tarjeta Sueldo"]['Valor_Real'].sum()
        saldo_gastos = df[df["Cuenta"] == "Tarjeta Gastos"]['Valor_Real'].sum()
        saldo_efectivo = df[df["Cuenta"] == "Efectivo"]['Valor_Real'].sum()
        saldo_cts = df[df["Cuenta"] == "Cuenta CTS"]['Valor_Real'].sum()
        liquidez_disponible = saldo_sueldo + saldo_gastos + saldo_efectivo

        st.subheader("Posición de Liquidez y Cuentas Patrimoniales")
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        kpi1.metric("Tarjeta Sueldo", f"S/ {saldo_sueldo:,.2f}")
        kpi2.metric("Tarjeta Gastos", f"S/ {saldo_gastos:,.2f}")
        kpi3.metric("Efectivo Físico", f"S/ {saldo_efectivo:,.2f}")
        kpi4.metric("Fondo CTS", f"S/ {saldo_cts:,.2f}")
        kpi5.metric("Liquidez Disponible", f"S/ {liquidez_disponible:,.2f}")
        st.divider()

        # Fórmulas de Flujo Operativo
        exclusiones_consumo = exclusiones_filtro + ['Ahorro e inversión']
        ingresos_mes = df_filtrado_mes[(df_filtrado_mes['Tipo'] == 'Ingreso') & (~df_filtrado_mes['Categoría'].isin(exclusiones_filtro))]['Monto'].sum()
        gastos_consumo = df_filtrado_mes[(df_filtrado_mes['Tipo'] == 'Gasto') & (~df_filtrado_mes['Categoría'].isin(exclusiones_consumo))]['Monto'].sum()
        ahorro_inversion_mes = df_filtrado_mes[(df_filtrado_mes['Tipo'] == 'Gasto') & (df_filtrado_mes['Categoría'] == 'Ahorro e inversión')]['Monto'].sum()
        flujo_libre = ingresos_mes - gastos_consumo - ahorro_inversion_mes

        st.subheader(f"Desempeño Operativo General — {filtro_mes} {filtro_año}")
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Ingresos Operativos", f"S/ {ingresos_mes:,.2f}")
        col_m2.metric("Gastos de Consumo", f"S/ {gastos_consumo:,.2f}", help="Capital consumido en operaciones del mes. Excluye transferencias a cuentas de ahorro e inversión.")
        col_m3.metric("Ahorro e Inversión", f"S/ {ahorro_inversion_mes:,.2f}", help="Capital reservado y transferido hacia el incremento patrimonial.")
        col_m4.metric("Flujo Libre Neto", f"S/ {flujo_libre:,.2f}", help="Excedente de liquidez tras cubrir obligaciones operativas y de inversión.")
        st.divider()

        # Control de Préstamos
        st.subheader("Cuentas por Cobrar (Préstamos Activos)")
        df_p_pendientes = df_p[df_p["Estado"] == "Pendiente"]
        if not df_p_pendientes.empty:
            total_prestado = df_p_pendientes["Monto"].sum()
            st.info(f"Capital total colocado en deudores de plazo pendiente: S/ {total_prestado:,.2f}")
            df_p_visual = df_p_pendientes[["Fecha", "Persona", "Monto", "Interes", "Fecha_Devolucion", "Cuenta"]].copy()
            df_p_visual["Días para Vencimiento"] = df_p_visual["Fecha_Devolucion"].apply(lambda x: (x - date.today()).days)
            retrasados = df_p_visual[df_p_visual["Días para Vencimiento"] < 0]
            if not retrasados.empty: st.error(f"Advertencia: {len(retrasados)} deudor(es) presentan retraso en la fecha pactada de liquidación.")
            st.dataframe(df_p_visual, use_container_width=True)
        else:
            st.write("No se reportan deudas de capital activas a favor.")
        st.divider()

        # --- APLICACIÓN CASCADA DE FILTROS PARA GRÁFICOS Y TABLA ---
        df_graficos = df_base_cascade.copy()
        df_tabla_final = df_filtrado_mes.copy()

        if filtro_tipo_flujo != "Todos los Movimientos":
            df_graficos = df_graficos[df_graficos['Tipo'] == filtro_tipo_flujo]
            df_tabla_final = df_tabla_final[df_tabla_final['Tipo'] == filtro_tipo_flujo]

        if filtro_categoria != "Todas las Categorías":
            df_graficos = df_graficos[df_graficos['Categoría'] == filtro_categoria]
            df_tabla_final = df_tabla_final[df_tabla_final['Categoría'] == filtro_categoria]

        if filtro_subcategoria != "Todas las Subcategorías":
            df_graficos = df_graficos[df_graficos['Subcategoría'] == filtro_subcategoria]
            df_tabla_final = df_tabla_final[df_tabla_final['Subcategoría'] == filtro_subcategoria]

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("#### Composición de Canales de Distribución")
            
            if filtro_subcategoria != "Todas las Subcategorías":
                monto_especifico = df_graficos["Monto"].sum()
                st.info(f"El impacto financiero neto acumulado en la subcategoría {filtro_subcategoria} es de S/ {monto_especifico:,.2f} para el periodo fiscal seleccionado.")
            
            elif filtro_categoria != "Todas las Categorías":
                if not df_graficos.empty:
                    pie_data = df_graficos.groupby("Subcategoría")["Monto"].sum().reset_index()
                    fig_pie = px.pie(pie_data, values="Monto", names="Subcategoría", hole=0.4, title=f"Subcategorías de {filtro_categoria}")
                    fig_pie.update_traces(textinfo='percent+label')
                    st.plotly_chart(fig_pie, use_container_width=True)
                else: st.write("Sin registros operativos.")
            
            elif filtro_tipo_flujo != "Todos los Movimientos":
                if not df_graficos.empty:
                    if filtro_tipo_flujo == "Gasto":
                        df_graficos = df_graficos[~df_graficos['Categoría'].isin(exclusiones_consumo)]
                    pie_data = df_graficos.groupby("Categoría")["Monto"].sum().reset_index()
                    fig_pie = px.pie(pie_data, values="Monto", names="Categoría", hole=0.4, title=f"Estructura del {filtro_tipo_flujo}")
                    fig_pie.update_traces(textinfo='percent+label')
                    st.plotly_chart(fig_pie, use_container_width=True)
                else: st.write("Sin movimientos detectados.")
            
            else:
                df_pie_general = df_graficos[(df_graficos['Tipo'] == 'Gasto') & (~df_graficos['Categoría'].isin(exclusiones_consumo))]
                if not df_pie_general.empty:
                    pie_data = df_pie_general.groupby("Categoría")["Monto"].sum().reset_index()
                    fig_pie = px.pie(pie_data, values="Monto", names="Categoría", hole=0.4, title="Estructura de Gastos Generales")
                    fig_pie.update_traces(textinfo='percent+label')
                    st.plotly_chart(fig_pie, use_container_width=True)
                else: st.write("No se reportan gastos de consumo en este periodo.")

        with col_g2:
            st.markdown("#### Evolución Operativa Histórica (Ejercicio Actual)")
            df_año = df[(df['Año'] == filtro_año) & (~df['Categoría'].isin(exclusiones_filtro))]
            if not df_año.empty:
                tendencia = df_año.groupby(["Mes_Num", "Mes", "Tipo"])["Monto"].sum().reset_index().sort_values("Mes_Num")
                fig_line = px.line(tendencia, x="Mes", y="Monto", color="Tipo", markers=True,
                                   color_discrete_map={"Ingreso": "#00CC96", "Gasto": "#EF553B"})
                st.plotly_chart(fig_line, use_container_width=True)

        with st.expander("Libro Diario de Operaciones Auditadas"):
            if df_tabla_final.empty: 
                st.write("No se encontraron registros bajo el árbol de jerarquías seleccionado.")
            else: 
                st.dataframe(df_tabla_final.sort_values(by="Fecha", ascending=False)[["Fecha", "Cuenta", "Tipo", "Categoría", "Subcategoría", "Monto", "Descripción"]], use_container_width=True)