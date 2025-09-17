# Especificación de Diseño de Software (SDD) - ADFREE Protocol v0.1

Resumen
-------
Este documento describe el diseño de referencia para el protocolo ADFREE: un conjunto de componentes (proxy, servidor, extensiones y portal) destinados a facilitar el bloqueo/filtrado de publicidad respetando la privacidad y la extensibilidad.

Arquitectura de alto nivel
-------------------------
- Proxy (proxy-ref): componente en Python encargada de inspección y modificación de tráfico.
- Extensión de navegador (webext-ref): intercepta y enriquece solicitudes desde el cliente.
- Módulo servidor (server-module): integración con Nginx/OpenResty o middleware para despliegue en el borde.
- Portal (portal): dashboard para administración de políticas y métricas.
- Test-harness: pruebas automáticas de integración usando Playwright.

Requisitos clave
----------------
- Privacidad: minimizar la exposición de datos del usuario.
- Extensibilidad: plugins o reglas que pueden añadirse sin rehacer el core.
- Desempeño: latencias añadidas mínimas en rutas críticas.

Detalles de diseño
------------------
Se describen interfaces, formatos de reglas y flujos de datos en las siguientes secciones (omitidas en este resumen inicial).

Seguridad
--------
Se recomiendan canales TLS, validación de entradas y pruebas de fuzzing para reglas.
