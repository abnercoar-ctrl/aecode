# NEXA CONTROL

Sistema de Seguimiento de Trabajos y Valorizaciones.

Gestiona trabajos, frentes, metrados, precios unitarios, programación incremental, ejecución y valorizaciones brutas. **Todos los archivos de ejemplo son ficticios**: no representan contratos, tarifas, políticas ni datos internos de NEXA. La etiqueta monetaria inicial `UM` significa unidades monetarias demostrativas.

## Ejecución en este equipo (PowerShell)

Desde la carpeta abierta en VS Code:

```powershell
Set-Location -LiteralPath 'C:\Users\est.abnerb\OneDrive - Votorantim\Documentos\5. PYTHON_PRUEBAS RELAVES'
& '.\.venv\Scripts\python.exe' -m pip install -r '.\NEXA_CONTROL\requirements.txt'
Set-Location -LiteralPath '.\NEXA_CONTROL'
& '..\.venv\Scripts\python.exe' -m streamlit run app.py
```

Abra `http://localhost:8501`. No es necesario activar el entorno ni cambiar la política de ejecución de PowerShell. El entorno detectado es `.venv` en la carpeta superior; Python 3.14.7. No se encontró una carpeta `venv` en el espacio de trabajo y la terminal no tenía `VIRTUAL_ENV` definido. El comando global `python` apuntaba al alias de WindowsApps, por lo que se usa el ejecutable explícito del entorno.

En otro equipo, dentro de la carpeta del proyecto:

```powershell
py -3.14 -m venv .venv
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.txt
& '.\.venv\Scripts\python.exe' -m streamlit run app.py
```

`requirements.txt` fija las versiones directas utilizadas. `requirements-lock.txt` registra también las dependencias transitivas del entorno local. El lock local puede contener paquetes específicos de Windows; para Community Cloud use `requirements.txt`.

## Estructura

```text
NEXA_CONTROL/
  app.py                         # Composición y estado de la sesión
  modulos/
    gestion_datos.py             # Esquemas, archivos, validación, filtros
    calculos_avance.py           # Cantidades y avances ponderados
    valorizaciones.py           # Montos por fecha y mes
    indicadores.py              # Indicadores del alcance
    graficos.py                  # Cuatro gráficos Plotly
    exportacion.py               # Excel formateado
    interfaz.py                  # Formularios y vistas
  datos/                        # Plantillas Excel y CSV demostrativas
  recursos/                     # Referencia visual y notas de diseño
  scripts/generar_ejemplos.py    # Generación determinista de ejemplos
  tests/                        # Cálculos, validaciones, archivos, interfaz
  .streamlit/config.toml         # Tema y configuración
  requirements.txt
  requirements-lock.txt
  README.md
  INFOGRAFIA_CONTENIDO.md
```

Librerías: Streamlit (interfaz y sesión), Pandas y NumPy (tablas y cálculos), Plotly (gráficos interactivos), openpyxl (lectura de Excel), XlsxWriter (exportación), pytest (pruebas). No se requiere una API de IA para ejecutar el sistema.

Para la comprobación visual local se instaló además Playwright 1.64.0, usando el Edge existente sin descargar otro navegador. Es opcional y se fija en `requirements-qa.txt`; no se utiliza al ejecutar la aplicación ni al desplegarla.

## Uso

1. **Dashboard general:** seleccione proyecto, frente, Desde y Hasta. Se muestran presupuesto, ejecutado acumulado, saldo, avances programado y real, desviación, cantidad de trabajos, atrasados y pendientes.
2. **Registro de trabajos:** complete proyecto, código, descripción, frente, unidad, metrado, precio e inicio/fin; pulse Registrar trabajo. El código es único dentro de cada proyecto. Puede editar o eliminar filas con el editor y Guardar edición. No se permite eliminar una partida que tenga avances asociados; modifique primero esos avances.
3. **Seguimiento de avances:** seleccione proyecto/código y registre fecha, metrado programado y ejecutado **incrementales**, no acumulados. Si registró 20 ayer y 30 hoy, hoy ingrese 30. Cada fecha representa el cierre de un período; el sistema no prorratea registros que abarquen varios días. Solo se admite una fila por trabajo y fecha; para corregirla, edite la existente. Los formularios y editores administran toda la sesión y lo indican; la tabla de avance al corte usa los filtros.
4. **Valorizaciones:** consulte montos del período, acumulado, saldo, resumen mensual y detalle.
5. **Reportes y exportación:** descargue un reporte Excel filtrado, un respaldo completo, tablas CSV o ejemplos. El respaldo completo incluye registros fuera del alcance y posteriores al corte; puede restaurarse con vista previa desde esta misma sección.

La sesión comienza con datos ficticios. En Datos de la sesión puede iniciar una sesión vacía o recargar la demostración; estos botones reemplazan los datos de la sesión actual. Los datos viven en `st.session_state`, sin base de datos: se conservan durante las interacciones y navegación, pero pueden perderse al cerrar la sesión, reiniciar el servidor o dormir la instancia de nube. Descargue respaldos antes de salir. Los archivos importados no se escriben sobre los ejemplos.

## Importación

En Registro de trabajos y Seguimiento de avances, despliegue Importar. Se admite `.xlsx` o `.csv` UTF-8 (con o sin BOM), coma o punto y coma como separador, decimales con punto y fechas `AAAA-MM-DD`. Los Excel individuales leen la primera hoja. Guarde los códigos como texto para conservar ceros iniciales. Límite: 20 MB por archivo.

Columnas exactas de partidas:

```text
proyecto,codigo,descripcion,frente,unidad,metrado_contratado,precio_unitario,fecha_inicio,fecha_fin
```

Columnas exactas de avances:

```text
proyecto,fecha,codigo,metrado_programado,metrado_ejecutado
```

Las columnas extra o ausentes se rechazan; su orden puede variar. Revise la vista previa, elija Agregar registros o Reemplazar esta tabla y pulse Incorporar archivo revisado. Los datos se validan antes de incorporarse. Para cargar otro proyecto completo, inicie una sesión vacía, importe primero partidas y luego avances. Para reemplazar ambas tablas a la vez, use Restaurar respaldo revisado con las hojas `Partidas` y `Avances` del respaldo completo.

Se rechazan campos obligatorios vacíos, números no finitos o negativos, fechas inválidas, inicio posterior a fin, claves duplicadas, avances huérfanos, duplicados diarios y metrados programados o ejecutados acumulados superiores a lo contratado. El exceso se contrasta con una tolerancia numérica relativa de `1e-9`. No se aprueban adicionales contractuales automáticamente. Metrado o precio cero se permiten con advertencia. Los avances fuera del intervalo programado se admiten con advertencia para reflejar trabajo anticipado o tardío.

## Cálculos y filtros

- Presupuesto = Σ(metrado contratado × precio unitario).
- Valorización del período = Σ(metrado ejecutado incremental × precio unitario), entre Desde y Hasta inclusive.
- Acumulado = Σ(valorizaciones de toda la historia hasta Hasta inclusive).
- Saldo = presupuesto − ejecutado acumulado.
- Avance físico ponderado por presupuesto = ejecutado acumulado / presupuesto × 100.
- Avance programado = monto programado acumulado / presupuesto × 100.
- Desviación = avance real − programado, en puntos porcentuales (pp).

**El presupuesto es el de todas las partidas del alcance proyecto/frente; no se recorta por fecha.** Desde solo limita montos del período y resumen mensual. Los KPI acumulados, el avance por trabajo/frente y la curva S mantienen la historia anterior a Desde. No se suman metrados de unidades distintas para calcular avances generales. Si el presupuesto es cero, el porcentaje se muestra como cero con advertencia; no debe interpretarse como avance medible.

Las fechas programadas no generan una distribución automática: ingrese los metrados programados por fecha. Una partida está pendiente si no completó su metrado, y atrasada si además ejecutó menos de lo programado al corte o venció su fecha fin. Una partida completada deja de estar pendiente, aunque su cierre real haya ocurrido tarde; no se modela historial de cierre en esta versión.

No se implementan IGV, adelantos, amortizaciones, retenciones, reajustes ni penalidades. Todos los montos son brutos. La etiqueta de unidad monetaria es configurable y no transforma valores ni permite mezclar monedas con conversión automática. Para varios proyectos, use precios expresados en la misma unidad monetaria.

## Gráficos

- **Curva S:** programado azul y real verde, acumulados al corte. Parte de un punto cero anterior al inicio y no omite historia anterior a Desde.
- **Avance por frente:** barras de porcentajes ponderados por presupuesto dentro de cada proyecto/frente.
- **Valorizaciones mensuales:** ejecución dentro del período; incluye meses sin movimientos con cero. Los meses extremos pueden ser parciales.
- **Desviación por trabajo:** verde para adelanto o igualdad, rojo para retraso; el eje se expresa en pp.

Todos los gráficos se generan desde las tablas cargadas. Puede explorar valores con el cursor, alternar series desde la leyenda y utilizar las herramientas de Plotly.

## Excel de resultados

Incluye Resumen general (origen, alcance, fechas y reglas), Partidas contratadas, Registro de avances, Valorizaciones, Indicadores, Resumen mensual y Avance por trabajo. Los registros y valorizaciones incluyen historia hasta el corte para reproducir los acumulados; Resumen mensual solo contiene el período. Se aplican encabezados, filtros, panel inmovilizado, fechas ISO y números con dos decimales; la unidad monetaria figura en resumen e indicadores. Las columnas de porcentajes contienen valores 0–100, no fracciones. Los textos se conservan como texto literal aunque empiecen con `=`.

## Ejemplo verificable

Con todos los proyectos/frentes y período 2026-01-31 a 2026-03-31:

| Indicador | Resultado |
|---|---:|
| Trabajos / registros de avance | 8 / 18 |
| Presupuesto | 130,000 UM |
| Programado acumulado | 66,000 UM |
| Ejecutado acumulado | 60,000 UM |
| Saldo | 70,000 UM |
| Avance programado | 50.769231% |
| Avance real | 46.153846% |
| Desviación | −4.615385 pp |
| Trabajos atrasados / pendientes | 4 / 8 |

Ejecución mensual: enero 15,500 UM, febrero 20,000 UM y marzo 24,500 UM. En Proyecto DEMO A: presupuesto 100,000 UM y ejecutado 46,000 UM. Los precios son únicamente ejemplos académicos.

## Verificación

Desde `NEXA_CONTROL`:

```powershell
& '..\.venv\Scripts\python.exe' -m compileall -q app.py modulos scripts tests
& '..\.venv\Scripts\python.exe' -m pytest -q
& '..\.venv\Scripts\python.exe' -m pip check
```

Las pruebas de interfaz emplean `streamlit.testing.v1.AppTest`, además de las pruebas unitarias de cálculos, gráficos y archivos. Para regenerar los ejemplos ficticios (sobrescribe únicamente los archivos de ejemplo del proyecto):

```powershell
& '..\.venv\Scripts\python.exe' scripts/generar_ejemplos.py
```

### Resultados ejecutados el 18/10/2026

| Comprobación | Resultado observado |
|---|---|
| Suite pytest final | **33 pruebas aprobadas**, 48.18 segundos |
| Compilación e importación | `compileall` sin errores; módulos importados por pytest y por la aplicación |
| Dependencias | `pip check`: No broken requirements found |
| Ejemplo numérico | Presupuesto 130,000; ejecución 60,000; saldo 70,000 UM; 4 atrasados |
| Importación | Excel/CSV, códigos con ceros, formatos incorrectos y transacciones rechazadas comprobados con pruebas |
| Exportación | Hojas, cifras, historia al corte, formatos y texto literal verificados con openpyxl |
| Interfaz AppTest | Navegación por cinco secciones, filtros, alta manual de trabajo/avance, duplicado rechazado sin perder datos, sesión vacía y rango inválido |
| Servidor | Streamlit inició en `http://127.0.0.1:8501`; endpoint `/_stcore/health` respondió `ok` |
| Navegador real | Playwright + Microsoft Edge: cinco secciones, formularios, cuatro gráficos y descarga real de Excel; ocho comprobaciones aprobadas |
| Consola y página | Cero errores de consola y cero excepciones de página en la prueba de navegador |
| Escritorio / móvil | 1536 × 1024 y 390 × 844; captura visual revisada y sin desbordamiento horizontal de página en móvil |

Se corrigieron dos problemas detectados: fecha de corte duplicada en la curva vacía y meses interpretados como fechas continuas en las barras de valorización. La suite final incluye ambas comprobaciones. Aparecen tres advertencias de deprecación de `importlib.metadata` durante AppTest en Python 3.14; no provocan fallos. La primera ejecución restringida tuvo problemas de permisos en cachés temporales, por lo que la suite final se ejecutó con autorización fuera del aislamiento.

El navegador integrado informó que no había navegador disponible; se utilizó Playwright con Edge instalado. El primer selector automatizado de radio no podía pulsar el input visualmente sustituido por Streamlit; se corrigió la prueba para pulsar las etiquetas visibles y la navegación pasó. No se cambió el comportamiento de navegación de la aplicación para adaptarlo a la prueba.

Las capturas y el script de comprobación se conservaron en la carpeta temporal del equipo, fuera del código publicable. Los resultados de navegador comprobaron navegación y descarga; la incorporación de archivos y las altas manuales se verificaron mediante las pruebas Python/AppTest descritas, no mediante carga de archivos en Edge. No se han probado despliegue remoto, otros navegadores, concurrencia de usuarios ni persistencia en una base de datos.

Comparación visual con `recursos/concepto_dashboard.png`: referencia y capturas inspeccionadas con `view_image`. Se revisaron fondo blanco/sidebar gris, paleta navy/azul/verde/rojo, jerarquía de títulos, ocho métricas en dos filas, cuatro gráficos en dos columnas y composición móvil. Se mantuvo la estructura del concepto con las adaptaciones nativas de Streamlit documentadas en `recursos/DISENO.md`. El texto añadido sobre origen, cortes y respaldo responde a requisitos funcionales; se sustituyeron moneda y valores ficticios de la referencia por UM y los resultados reproducibles del sistema. La infografía visual continúa pendiente.

## Publicación en Streamlit Community Cloud — pendiente

No se ha publicado ni creado un repositorio remoto. Se requiere acceso a las cuentas del usuario.

1. Suba **el contenido de `NEXA_CONTROL` como raíz de un repositorio GitHub**, incluyendo `datos/` y `.streamlit/config.toml`; no suba el entorno virtual, secretos ni datos empresariales.
2. Entre a Streamlit Community Cloud y conecte su cuenta GitHub.
3. Cree una aplicación seleccionando repositorio, rama y archivo de entrada `app.py`.
4. Seleccione Python 3.14 si está disponible, para reproducir el entorno comprobado. Si solo se ofrece otra versión, valide que todas las versiones fijadas admitan esa versión de Python antes de desplegar; no se ha comprobado otro intérprete local.
5. Mantenga `requirements.txt` en la raíz, junto a `app.py`. No use el lock Windows como archivo de instalación de nube.
6. Despliegue y verifique la URL, los ocho KPI, los cuatro gráficos, importación y descarga Excel. Complete la evidencia académica con la URL real y capturas.

Si sube la carpeta dentro de otro repositorio, el archivo de entrada será `NEXA_CONTROL/app.py`; revise también la ubicación de la configuración respecto de la raíz del repositorio. La opción de subir el contenido como raíz evita ambigüedades.

Referencias oficiales consultadas para preparar estos pasos: [dependencias](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies), [organización de archivos](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization) y [despliegue](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app).

## Evidencias para la rúbrica

| Criterio | Evidencia implementada | Estado |
|---|---|---|
| Web Streamlit (7 puntos) | Cinco secciones, formularios, botones, tablas, desplegables, cuatro gráficos y Excel | Implementado; ver pruebas ejecutadas |
| Funciones independientes (5 puntos) | Módulos puros separados de interfaz e importados desde `app.py` | Implementado |
| Parámetros editables (4 puntos) | Más de cinco entradas manuales, filtros, editores e importación Excel/CSV | Implementado |
| Publicación, estructura e infografía IA (4 puntos) | Estructura, configuración de despliegue y contenido de infografía preparados | Parcial: faltan publicación e infografía visual |

No se afirma obtener 20/20: la puntuación corresponde al evaluador y el cuarto criterio requiere completar sus entregables externos.
