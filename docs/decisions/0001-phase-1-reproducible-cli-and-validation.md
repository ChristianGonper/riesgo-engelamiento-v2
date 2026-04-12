# ADR-0001: Fase 1 con CLI reproducible, validación explícita y resumen generado

## Status
Accepted

## Date
2026-04-12

## Context
El repositorio parte de una salida WRF grande y de un objetivo incremental. La primera entrega debe ser útil por sí misma, repetible y fácil de validar sin depender de notebooks ni de inspección manual.

## Decision
Implementar la fase 1 como un pipeline reproducible en Python con:
- un CLI principal basado en script,
- lectura y validación de NetCDF con `xarray`,
- reporte explícito de variables y dimensiones requeridas,
- resumen generado en `outputs/` en formato Markdown y JSON,
- documentación central de supuestos y limitaciones, incluyendo `T0 = 300 K`.

## Consequences
- La validación del dataset queda separada de las fases físicas posteriores.
- El proyecto mantiene un punto de entrada estable para futuras fases.
- El resumen generado sirve como artefacto de trazabilidad para usuarios y revisores.
- Si el dataset cambia, la validación fallará con mensajes concretos en vez de producir diagnósticos silenciosamente incorrectos.

