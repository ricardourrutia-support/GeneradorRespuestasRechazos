import streamlit as st
import pandas as pd
import re

# Configuración de la página
st.set_page_config(page_title="Generador de Respuestas Zendesk", page_icon="🚕", layout="wide")

st.title("🚕 Generador de Respuestas para Zendesk")
st.markdown("""
Sube la nómina de rechazos. El sistema detectará automáticamente:
* **Empresa vs Persona:** Basado en si el RUT base es > 70.000.000.
* **Error de Tarjeta:** Si el número de cuenta tiene 15 o más dígitos.
* **Casos Especiales:** Detecta errores técnicos (ej: 'Host IFR no disponible') y ajusta el mensaje de forma amigable.
""")

# --- BARRA LATERAL (INPUTS DEL AGENTE) ---
st.sidebar.header("Datos del Agente")
nombre_agente = st.sidebar.text_input("Tu Nombre", value="Ricardo")
pie_firma = st.sidebar.text_input("Tu Firma / Cargo", value="Cabify Support")

# --- FUNCIONES DE LÓGICA ---

def limpiar_rut(rut_raw):
    try:
        rut_str = str(rut_raw).upper()
        rut_limpio = rut_str.replace(".", "").replace("-", "")
        cuerpo_rut = rut_limpio[:-1]
        return int(cuerpo_rut)
    except:
        return 0

def procesar_saludo(row):
    rut_val = limpiar_rut(row.get('Rut', 0))
    nombre_completo = str(row.get('Nombre / Razón social', 'Colaborador')).strip()
    
    if rut_val > 70000000:
        return nombre_completo.title()
    else:
        partes = nombre_completo.split()
        if len(partes) > 0:
            return partes[0].capitalize()
        return "Colaborador"

def formatear_cuenta(cuenta_raw):
    try:
        if isinstance(cuenta_raw, (float, int)):
            return "{:.0f}".format(cuenta_raw)
        return str(cuenta_raw)
    except:
        return str(cuenta_raw)

def generar_aviso_tarjeta(cuenta_str):
    cuenta_clean = cuenta_str.replace(" ", "")
    if len(cuenta_clean) >= 15:
        return "\n⚠️ **Nota Importante:** Hemos notado que el número registrado tiene 15 o más dígitos. Te recordamos cordialmente verificar que estés ingresando tu **número de cuenta bancaria** y no el número que aparece impreso en tu tarjeta (plástico), ya que suelen ser diferentes.\n"
    return ""

def crear_texto_correo(row, agente, firma):
    # 1. Datos básicos
    nombre_saludo = procesar_saludo(row)
    motivo_original = str(row.get('Motivo del rechazo', 'Motivo no especificado'))
    institucion = row.get('Institución', 'Banco no especificado')
    cuenta_str = formatear_cuenta(row.get('Cuenta', 'N/A'))
    aviso_tarjeta = generar_aviso_tarjeta(cuenta_str)

    # 2. Lógica de Casos Especiales
    es_caso_operativo = "Medio de pago habilitado en banco destino" in motivo_original
    es_caso_ifr = "Host IFR no disponible" in motivo_original

    if es_caso_operativo:
        # Reemplazo del motivo técnico por el amigable
        motivo_mostrar = "La transferencia no pudo realizarse debido a una incidencia operativa del banco receptor."
        
        # Mensaje condicional: Da la opción de mantener o cambiar
        bloque_accion = """Dada esta situación, queda a tu elección cómo proceder para el próximo pago:

1. **Mantener tu cuenta actual:** Si confirmas que tu cuenta está operativa, podemos reintentar el abono en el siguiente ciclo, aunque depende de tu banco si lo acepta.
2. **Cambiar de cuenta:** Para asegurar el pago más rápido, puedes indicarnos una cuenta diferente (de otro banco o tipo).

**Si decides cambiarla**, por favor respóndenos con los siguientes datos:"""

    elif es_caso_ifr:
        # Reemplazo del motivo IFR por intermitencia
        motivo_mostrar = f"Intermitencias en el Banco {institucion} al momento de procesar el pago."
        
        # Mensaje estándar
        bloque_accion = """Para poder continuar con los abonos pendientes, te pedimos por favor verificar si esta información es correcta o bien ingresar una nueva cuenta bancaria con los siguientes datos:"""

    else:
        # Caso Normal
        motivo_mostrar = motivo_original
        
        # Mensaje estándar: Pide verificar o cambiar
        bloque_accion = """Para poder continuar con los abonos pendientes, te pedimos por favor verificar si esta información es correcta o bien ingresar una nueva cuenta bancaria con los siguientes datos:"""

    # 3. Construcción del Mensaje Final
    mensaje = f"""Hola {nombre_saludo},

Mi nombre es {agente} y seré el encargado de ayudarte con tu caso.

Junto con saludarte, te comento que tus pagos han sido rechazados por tu banco debido al siguiente motivo:
Motivo de rechazo: {motivo_mostrar}

Cuenta registrada al momento del rechazo:
Institución: {institucion}
N° de cuenta: {cuenta_str}
{aviso_tarjeta}
{bloque_accion}

Nombre:
RUT:
Banco:
Tipo de cuenta (vista o corriente):
Número de cuenta:

👉 En caso de que ya hayas actualizado correctamente tu información bancaria, puedes ignorar este mensaje.

Te recordamos que los datos bancarios deben estar registrados a tu nombre. No es posible generar pagos a cuentas de terceros, salvo que se adjunte un certificado notarial que autorice el uso de dicha cuenta.

Quedamos atentos a tu respuesta para poder ayudarte a la brevedad.

Ante cualquier duda adicional, no dudes en volver a contactarnos o visitar nuestro Centro de Ayuda: https://help.cabify.com/hc/es

Un saludo cordial,

{agente}
{firma}"""
    return mensaje

# --- INTERFAZ PRINCIPAL ---

uploaded_file = st.file_uploader("Sube tu archivo (Excel o CSV)", type=["xlsx", "csv"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        df.columns = df.columns.str.strip()
        
        cols_requeridas = ['Rut', 'Nombre / Razón social', 'Institución', 'Cuenta', 'email']
        missing = [c for c in cols_requeridas if c not in df.columns]
        
        if missing:
            st.error(f"Faltan las siguientes columnas: {', '.join(missing)}")
        else:
            st.success(f"Archivo cargado. Generando respuestas...")
            
            for index, row in df.iterrows():
                email_usuario = row['email']
                if pd.isna(email_usuario):
                    email_usuario = "Correo no disponible"
                
                texto_final = crear_texto_correo(row, nombre_agente, pie_firma)
                
                with st.container():
                    st.markdown("---")
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        st.subheader(f"Caso #{index + 1}")
                        st.info(f"📧 **Enviar a:**\n\n{email_usuario}")
                        st.text(f"RUT: {row['Rut']}")
                        
                        # Alertas visuales para el agente
                        motivo_check = str(row.get('Motivo del rechazo', ''))
                        if "Medio de pago habilitado en banco destino" in motivo_check:
                            st.error("⚡ Caso Especial: Incidencia Banco")
                        elif "Host IFR no disponible" in motivo_check:
                            st.warning("🔄 Caso Especial: Intermitencia (IFR)")
                        
                        cuenta_display = formatear_cuenta(row['Cuenta'])
                        if len(cuenta_display) >= 15:
                            st.warning("⚠️ Posible N° Tarjeta")
                    
                    with col2:
                        st.write("**Copiar mensaje:**")
                        st.code(texto_final, language="markdown")

    except Exception as e:
        st.error(f"Error procesando el archivo: {e}")
