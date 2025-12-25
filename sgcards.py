import streamlit as st
from sqlalchemy import text
from db import engine
import datetime
import pandas as pd
from datetime import datetime
from calendar import monthrange



st.set_page_config(page_title="Gestor de Tarjetas", layout="wide")

# ---------------------------------------------------
# Función: Obtener todas las tarjetas
# ---------------------------------------------------
def get_tarjetas():
    query = text("SELECT * FROM TarjetasCredito ORDER BY nombre ASC")
    with engine.connect() as conn:
        result = conn.execute(query)
        return result.fetchall()

# ---------------------------------------------------
# Función: Crear tarjeta
# ---------------------------------------------------
def crear_tarjeta(nombre, limite, corte, pago):
    query = text("""
        INSERT INTO TarjetasCredito (nombre, limiteCredito, fechaCorte, fechaPago)
        VALUES (:nombre, :limite, :corte, :pago)
    """)
    with engine.connect() as conn:
        conn.execute(query, {"nombre": nombre, "limite": limite, "corte": corte, "pago": pago})
        conn.commit()

# ---------------------------------------------------
# Función: Actualizar tarjeta
# ---------------------------------------------------
def actualizar_tarjeta(id_t, nombre, limite, corte, pago):
    query = text("""
        UPDATE TarjetasCredito
        SET nombre=:nombre, limiteCredito=:limite, fechaCorte=:corte, fechaPago=:pago
        WHERE id=:id
    """)
    with engine.connect() as conn:
        conn.execute(query, {
            "nombre": nombre, "limite": limite,
            "corte": corte, "pago": pago, "id": id_t
        })
        conn.commit()

# ---------------------------------------------------
# Función: Eliminar tarjeta
# ---------------------------------------------------
def eliminar_tarjeta(id_t):
    query = text("DELETE FROM TarjetasCredito WHERE id=:id")
    with engine.connect() as conn:
        conn.execute(query, {"id": id_t})
        conn.commit()

# ---------------------------------------------------
# Función: Próximos pagos
# ---------------------------------------------------
def calcular_proximos_pagos(tarjetas):
    hoy = datetime.date.today().day
    proximos = []

    for t in tarjetas:
        dias_restantes = t.fechaPago - hoy
        if dias_restantes < 0:
            dias_restantes += 30  # se pasa al siguiente mes

        proximos.append({
            "nombre": t.nombre,
            "fechaPago": t.fechaPago,
            "diasRestantes": dias_restantes
        })

    return sorted(proximos, key=lambda x: x["diasRestantes"])


# ---------------------------------------------------
# Función: Tarjetas disponibles (según fecha de corte)
# ---------------------------------------------------
def tarjetas_disponibles(tarjetas):
    hoy = datetime.date.today().day
    disponibles = []

    for t in tarjetas:
        # Disponible si el día actual es MENOR al día de corte
        disponible = hoy < t.fechaCorte

        disponibles.append({
            "nombre": t.nombre,
            "corte": t.fechaCorte,
            "disponible": disponible
        })

    return disponibles


# ========================== UI =============================

st.sidebar.title("SGCards")

# Nuevo menú superior
seccion = st.sidebar.radio(
    "Selecciona una sección",
    ("Panel principal", "Opciones administrativas"), label_visibility="collapsed"
)

# Si elige opciones administrativas, mostramos el CRUD
if seccion == "Opciones administrativas":
    opcion = st.sidebar.selectbox(
        "Selecciona una acción:",
        (
            "Crear tarjeta",
            "Ver tarjetas",
            #"Próximos pagos",
            #"Tarjetas disponibles"
        ), label_visibility="collapsed"
    )
else:
    opcion = None  # Para que no intente ejecutar nadas
st.sidebar.write("---")


# ======================= PANEL PRINCIPAL ===========================
if seccion == "Panel principal":

    # Radio horizontal para las secciones del panel
    panel = st.radio(
        "",
        ["Próximos pagos", "Disponibles"],
        horizontal=True
    )

    # ================== OPCIÓN: PRÓXIMOS PAGOS ==================
    if panel == "Próximos pagos":

        tarjetas = get_tarjetas()

        if not tarjetas:
            st.info("No hay tarjetas registradas.")
        else:

            # ====== FILTRO POR FECHA (NUEVO) ======
            fecha_seleccionada = st.sidebar.date_input(
                "Próximos pagos:",
                datetime.now()
            )

            hoy = fecha_seleccionada.day
            anio = fecha_seleccionada.year
            mes = fecha_seleccionada.month

            dias_mes = monthrange(anio, mes)[1]

            # ====== Totales ======
            total_tarjetas = len(tarjetas)
            total_credito = sum(float(t._mapping["limiteCredito"]) for t in tarjetas)

            st.sidebar.write(f"**Total de tarjetas registradas:** {total_tarjetas}")
            st.sidebar.write(f"**Línea total de crédito:** ${total_credito:,.2f}")

            proximas = []

            for t in tarjetas:

                t = dict(t._mapping)
                fecha_pago = int(t["fechaPago"])

                # ==== CÁLCULO DE DÍAS RESTANTES BASADO EN FECHA SELECCIONADA ====
                if fecha_pago >= hoy:
                    dias_restantes = fecha_pago - hoy
                else:
                    dias_restantes = (dias_mes - hoy) + fecha_pago

                # Mostrar solo si faltan 5 días o menos
                if dias_restantes <= 5:
                    proximas.append({
                        "tarjeta": t["nombre"],
                        "fecha_pago": fecha_pago,
                        "días_restantes": dias_restantes
                    })

            if proximas:

                df = pd.DataFrame(proximas)
                df = df.sort_values("días_restantes")
                df = df.set_index("tarjeta")

                def resaltar_hoy(row):
                    color = "background-color: #F54927" if row["días_restantes"] == 0 else ""
                    return [color] * len(row)

                st.dataframe(
                    df.style.apply(resaltar_hoy, axis=1),
                    use_container_width=True
                )

            else:
                st.info("No hay tarjetas próximas a pagar.")


    # ================== OPCIÓN: DISPONIBLES ==================
    elif panel == "Disponibles":
        #st.subheader("Tarjetas disponibles para usar hoy")

        tarjetas = get_tarjetas()
        if not tarjetas:
            st.info("No hay tarjetas registradas.")
        else:

            # === Fecha actual desde el calendario ===
            fecha_actual = st.sidebar.date_input(
                "Disponibilidad basada en fecha:",
                datetime.now()
            )

            hoy = fecha_actual.day
            anio = fecha_actual.year
            mes = fecha_actual.month

            dias_mes = monthrange(anio, mes)[1]

            disponibles = []

            for t in tarjetas:
                t = dict(t._mapping)

                corte = int(t["fechaCorte"])
                inicio = corte
                fin = corte + 10

                # ---- Ajuste para cambio de mes ----
                if fin > dias_mes:
                    # Caso de disponibilidad que pasa al siguiente mes
                    fin_real = fin - dias_mes

                    if hoy >= inicio:
                        dias_restantes = fin - hoy
                        esta_disponible = dias_restantes >= 0
                    else:
                        dias_restantes = fin_real - hoy
                        esta_disponible = dias_restantes >= 0
                else:
                    # Todo dentro del mismo mes
                    fin_real = fin
                    esta_disponible = inicio <= hoy <= fin_real
                    dias_restantes = fin_real - hoy if esta_disponible else -1

                # Guardar solo si está disponible hoy
                if esta_disponible:
                    disponibles.append({
                        "tarjeta": t["nombre"],
                        "fecha_corte": corte,
                        "disponible_hasta": fin_real,
                        "días_restantes": dias_restantes
                    })

            # === Mostrar DataFrame ===
            if disponibles:
                df = pd.DataFrame(disponibles)
                df = df.set_index("tarjeta")

                # Ordenar por días restantes (menor a mayor)
                df = df.sort_values("días_restantes")

                st.dataframe(df, use_container_width=True)

            else:
                st.info("No hay tarjetas disponibles para usar en esta fecha.")


# ---------------------------------------------------
# CREAR TARJETA
# ---------------------------------------------------
if opcion == "Crear tarjeta":

    nombre = st.sidebar.text_input("Nombre de la tarjeta")
    limite = st.sidebar.number_input("Límite de crédito", min_value=0, step=1000)
    corte = st.sidebar.number_input("Fecha de corte (1–31)", min_value=1, max_value=31)
    pago = st.sidebar.number_input("Fecha de pago (1–31)", min_value=1, max_value=31)

    if st.sidebar.button("Guardar tarjeta"):
        if nombre and limite > 0:
            crear_tarjeta(nombre, limite, corte, pago)
            st.sidebar.success("Tarjeta creada correctamente.")
        else:
            st.sidebar.error("Completa todos los campos.")



# ---------------------------------------------------
# VER TARJETAS
# ---------------------------------------------------
elif opcion == "Ver tarjetas":

    tarjetas = get_tarjetas()

    if tarjetas:
        # Convertir lista a DataFrame
        df = pd.DataFrame(tarjetas)

        # Asegurar índice
        if "id" in df.columns:
            df = df.set_index("id")

        # Añadir columna de selección para editar
        df["opciones"] = False

        # Mostrar tabla editable
        edited_df = st.data_editor(
            df,
            use_container_width=True,
            column_config={
                "limiteCredito": st.column_config.NumberColumn(
                    "Límite de Crédito",
                    format="$ %d",
                ),
                "opciones": st.column_config.CheckboxColumn(
                    "Opciones",
                    help="Seleccione para editar esta tarjeta",
                    default=False,
                )
            }
        )

        # --- Detectar qué tarjeta fue seleccionada ---
        seleccionados = edited_df[edited_df["opciones"] == True]

        # Solo se toma el PRIMERO si hubiera más (solo 1 activo permitido)
        if not seleccionados.empty:

            fila = seleccionados.iloc[0]
            id_tarjeta = fila.name

            st.sidebar.subheader("Editar tarjeta seleccionada")

            # Formulario con valores actuales
            nombre = st.sidebar.text_input("Nombre", fila["nombre"])
            limite = st.sidebar.number_input("Límite de crédito", value=int(fila["limiteCredito"]), step=1000)
            corte = st.sidebar.number_input("Fecha de corte", value=int(fila["fechaCorte"]), min_value=1, max_value=31)
            pago = st.sidebar.number_input("Fecha de pago", value=int(fila["fechaPago"]), min_value=1, max_value=31)

            if st.sidebar.button("Actualizar tarjeta"):
                actualizar_tarjeta(id_tarjeta, nombre, limite, corte, pago)
                st.sidebar.success("Tarjeta actualizada correctamente.")
                st.rerun()


            # -------------- OPCIÓN DE ELIMINAR ----------------
            #st.sidebar.subheader("Eliminar tarjeta")

            eliminar_checkbox = st.sidebar.checkbox(
                "Activar eliminación",
                help="Marque para confirmar que desea eliminar esta tarjeta"
            )

            if eliminar_checkbox:
                if st.sidebar.button("Confirmar eliminación", type="primary"):
                    eliminar_tarjeta(id_tarjeta)
                    st.sidebar.success("Tarjeta eliminada correctamente.")
                    st.rerun()

    else:
        st.info("No hay tarjetas registradas.")

