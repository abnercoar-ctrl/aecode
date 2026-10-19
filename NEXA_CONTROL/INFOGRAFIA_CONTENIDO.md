# Guion para infografía con IA — NEXA CONTROL

Este archivo es **contenido preparatorio**, no una infografía visual terminada.

## Título y propósito

**NEXA CONTROL**
Sistema de Seguimiento de Trabajos y Valorizaciones

Del metrado registrado a una decisión informada: avance, valorización y desviaciones en una sola aplicación.

## Flujo funcional

1. **Definir trabajos:** proyecto + código, frente, descripción, unidad, metrado, precio y fechas.
2. **Cargar datos:** formularios o Excel/CSV → vista previa → validación → incorporación.
3. **Registrar avances:** cantidades incrementales programadas y ejecutadas por fecha.
4. **Calcular:** presupuesto → valorización del período y acumulada → saldo → avance ponderado → desviación.
5. **Explorar:** filtros por proyecto, frente y período → ocho indicadores y cuatro gráficos interactivos.
6. **Compartir y conservar:** reporte Excel del alcance y respaldo completo de sesión.

## Tecnologías

Python: lógica modular. Streamlit: aplicación y estado de sesión. Pandas + NumPy: tablas y cálculos. Plotly: gráficos. openpyxl: lectura Excel. XlsxWriter: reportes. pytest + AppTest: verificación. Streamlit Community Cloud: destino de publicación pendiente.

## Fórmulas destacadas

- Presupuesto = Σ(metrado contratado × precio unitario).
- Valorización = Σ(metrado ejecutado del período × precio unitario).
- Avance físico ponderado por presupuesto = valorización acumulada / presupuesto × 100.
- Desviación = avance real − avance programado, en **puntos porcentuales**.

No es promedio simple de porcentajes. El corte Hasta incluye toda la historia previa. Desde delimita únicamente los montos del período.

## Ejemplo reproducible

**Datos ficticios de demostración — todos los proyectos y frentes, al 31/03/2026**

- 8 trabajos y 18 registros.
- Presupuesto 130,000 UM.
- Programado acumulado 66,000 UM → 50.77%.
- Ejecutado acumulado 60,000 UM → 46.15%.
- Saldo 70,000 UM.
- Desviación −4.62 pp.
- 4 trabajos atrasados y 8 pendientes.
- Ejecución mensual: enero 15,500; febrero 20,000; marzo 24,500 UM.

Comprobación: 15,500 + 20,000 + 24,500 = 60,000; 130,000 − 60,000 = 70,000.

## Dirección visual propuesta

Formato vertical A4 o 1080 × 1920 px; fondo blanco, texto azul marino #162D46, acento verde #008577, programación azul #377CF5, retrasos rojo #D94D5B. Jerarquía clara, seis pasos conectados y un bloque de ejemplo. Etiquetar datos ficticios de forma visible. Mostrar los cuatro gráficos en miniatura sin alterar sus fórmulas.

## Prompt sugerido para la infografía visual posterior

“Diseña una infografía profesional en español titulada NEXA CONTROL, Sistema de Seguimiento de Trabajos y Valorizaciones. Explica el flujo en seis pasos: definir trabajos, cargar y validar, registrar avances, calcular, explorar dashboard y exportar. Usa Python, Streamlit, Pandas, NumPy, Plotly, openpyxl, XlsxWriter y pytest como tecnologías. Destaca el avance físico ponderado por presupuesto y la desviación en puntos porcentuales. Incluye el ejemplo académico: presupuesto 130,000 UM, programado 66,000 UM (50.77%), ejecutado 60,000 UM (46.15%), saldo 70,000 UM, desviación −4.62 pp, 8 trabajos y 4 atrasados, corte 31/03/2026. Indica claramente DATOS FICTICIOS DE DEMOSTRACIÓN. Fondo blanco, texto azul marino, verde y azul para avances y rojo para retrasos. Mantén texto legible, fórmulas exactas y flujo claro. No incluyas una URL de publicación hasta disponer de una verificada.”

## Pendientes para entregar la imagen final

Generar o diseñar la infografía visual con IA, revisar texto/números, exportar PNG o PDF y añadir únicamente la URL real de la aplicación cuando se publique.
