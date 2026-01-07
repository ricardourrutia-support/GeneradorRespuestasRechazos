# GeneradorRespuestasRechazos# 🚕 Generador de Respuestas de Rechazo (Zendesk Helper)

Esta aplicación web, construida en Python y Streamlit, automatiza la creación de mensajes de respuesta para tickets de Zendesk relacionados con **pagos rechazados** a colaboradores (drivers).

La herramienta procesa una nómina (Excel o CSV), aplica reglas de negocio para personalizar el saludo y detecta posibles errores en los datos bancarios.

## 📋 Características Principales

1.  **Detección de Entidad (Empresa vs. Persona):**
    * Analiza el **RUT**. Si el cuerpo del RUT es mayor a `70.000.000`, se trata como Empresa (usa Razón Social).
    * En caso contrario, se trata como Persona Natural (usa el primer nombre).
2.  **Validación de Cuenta Bancaria:**
    * Detecta si el número ingresado tiene **15 o más dígitos**.
    * En esos casos, añade automáticamente una advertencia cordial sugiriendo que el usuario ingresó el número de tarjeta (plástico) en lugar del número de cuenta.
3.  **Corrección de Formato Numérico:**
    * Convierte números en notación científica (ej: `5.33E+15`) a texto plano completo para su correcta visualización.
4.  **Formato para Zendesk:**
    * Genera bloques de texto listos para copiar y pegar en los tickets, incluyendo enlaces formateados en Markdown.

## 🚀 Instalación y Ejecución

### Prerrequisitos
* Tener instalado [Python](https://www.python.org/) (versión 3.8 o superior).

### Pasos

1.  **Clonar el repositorio** (o descargar los archivos en una carpeta).
2.  **Instalar dependencias:**
    Abre tu terminal en la carpeta del proyecto y ejecuta:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Ejecutar la aplicación:**
    ```bash
    streamlit run app.py
    ```
4.  La aplicación se abrirá automáticamente en tu navegador (usualmente en `http://localhost:8501`).

## 📂 Formato del Archivo de Entrada

La aplicación acepta archivos `.xlsx` o `.csv`. Para que funcione correctamente, el archivo debe contener **exactamente** las siguientes columnas (respetando mayúsculas y acentos):

| Columna | Descripción |
| :--- | :--- |
| **Rut** | El RUT del colaborador (ej: `12.345.678-9`). Usado para la lógica de saludo. |
| **Nombre / Razón social** | Nombre completo o razón social. |
| **Institución** | Nombre del banco (ej: `Banco Estado`, `Mercado Pago`). |
| **Cuenta** | Número de cuenta rechazado. |
| **Motivo del rechazo** | La razón técnica del fallo. |
| **email** | Correo electrónico del colaborador (para identificar el usuario en Zendesk). |

## 🛠️ Personalización

En la barra lateral de la aplicación puedes configurar:
* **Nombre del Agente:** Quien firma el correo (ej: Ricardo).
* **Pie de Firma:** Cargo o área (ej: Cabify Support).

---
*Desarrollado para optimizar el flujo de Soporte y Operaciones.*
