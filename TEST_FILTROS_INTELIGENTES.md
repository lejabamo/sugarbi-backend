# 🧪 Guía de Pruebas - Filtros Inteligentes

## 📋 Resumen de Problemas Solucionados

### ❌ Problemas Identificados:
1. **Error de columna inexistente**: `area_hectareas` no existe en la base de datos
2. **Estado no actualizado**: `loadFilterOptions` no actualizaba `setFilterOptions`
3. **Filtros no reactivos**: Los filtros no se actualizaban dinámicamente

### ✅ Soluciones Implementadas:
1. **Removida columna inexistente** del agrupamiento en `filter_intersections.py`
2. **Agregada actualización de estado** en `loadFilterOptions`
3. **Mejorados logs de debug** para diagnosticar problemas

## 🔍 Pruebas de Verificación

### 1. Prueba de Backend (API)

#### 1.1 Verificar que el backend responde:
```bash
# Probar endpoint básico
curl -X GET "http://localhost:5001/api/filter-options"

# Debería retornar:
# - Status 200
# - Datos de años, meses, zonas, variedades, fincas
# - Sin errores de columna
```

#### 1.2 Probar datos filtrados:
```bash
# Probar sin filtros
curl -X GET "http://localhost:5001/api/cosecha-filtered?limit=5"

# Probar con filtro de año
curl -X GET "http://localhost:5001/api/cosecha-filtered?año=2025&limit=3"

# Probar con múltiples filtros
curl -X GET "http://localhost:5001/api/cosecha-filtered?año=2025&mes=1&limit=3"
```

#### 1.3 Verificar logs del backend:
```bash
# En la consola del backend deberías ver:
# 🔍 DEBUG - Filtros recibidos: {'año': 2025}
# 📊 DEBUG - Datos devueltos: X registros
```

### 2. Prueba de Frontend (Interfaz)

#### 2.1 Verificar carga inicial:
1. Abrir `http://localhost:5193` (o el puerto actual)
2. Ir a Dashboard
3. Verificar que aparecen datos por defecto
4. Verificar que la barra superior muestra "Mostrando X registros de producción"

#### 2.2 Probar filtros paso a paso:

**Paso 1: Seleccionar Año**
1. Hacer clic en dropdown "Año"
2. Seleccionar "2025"
3. **Verificar**: 
   - Dropdown de "Mes" se habilita
   - Aparecen opciones de meses para 2025
   - Barra superior cambia a "Mostrando X registros filtrados"

**Paso 2: Seleccionar Mes**
1. Hacer clic en dropdown "Mes"
2. Seleccionar "Enero" (o cualquier mes)
3. **Verificar**:
   - Dropdown de "Zona" se habilita
   - Aparecen opciones de zonas para 2025/Enero
   - Los datos del dashboard se actualizan

**Paso 3: Seleccionar Zona**
1. Hacer clic en dropdown "Zona"
2. Seleccionar cualquier zona (ej: "Zona 2")
3. **Verificar**:
   - Dropdown de "Variedad" se habilita
   - Aparecen variedades disponibles para la combinación
   - Los datos se filtran correctamente

**Paso 4: Seleccionar Variedad**
1. Hacer clic en dropdown "Variedad"
2. Seleccionar cualquier variedad
3. **Verificar**:
   - Dropdown de "Top Fincas" se habilita
   - Aparecen fincas disponibles
   - Los datos se filtran aún más

#### 2.3 Verificar consola del navegador:
1. Abrir DevTools (F12)
2. Ir a la pestaña "Console"
3. **Buscar logs**:
   ```
   🧠 Cargando filtros inteligentes para: {año: 2025}
   ✅ Filtros inteligentes recibidos: {...}
   🔍 Enviando filtros a API: {año: 2025}
   📊 Respuesta de API: {...}
   ✅ Opciones de filtros actualizadas: {...}
   ```

### 3. Pruebas de Casos Específicos

#### 3.1 Caso: Filtro sin datos
1. Seleccionar año 2020
2. Seleccionar mes "Diciembre"
3. **Verificar**: 
   - Aparece mensaje "No hay datos disponibles"
   - KPI cards muestran 0
   - Gráfico muestra mensaje de "Ajusta los filtros"

#### 3.2 Caso: Reset de filtros
1. Aplicar varios filtros
2. Hacer clic en "Limpiar"
3. **Verificar**:
   - Todos los filtros se resetean
   - Dashboard vuelve a mostrar datos por defecto
   - Barra superior vuelve a "Mostrando X registros de producción"

#### 3.3 Caso: Filtros dependientes
1. Seleccionar año 2025
2. Seleccionar mes "Enero"
3. Cambiar año a 2024
4. **Verificar**:
   - El mes se resetea automáticamente
   - Aparecen meses disponibles para 2024
   - Los datos se actualizan

### 4. Pruebas de Rendimiento

#### 4.1 Tiempo de respuesta:
- **Filtros básicos**: < 500ms
- **Filtros complejos**: < 1s
- **Carga inicial**: < 2s

#### 4.2 Verificar logs de rendimiento:
```javascript
// En la consola del navegador:
console.time('filter-load');
// ... aplicar filtro ...
console.timeEnd('filter-load');
```

## 🐛 Diagnóstico de Problemas

### Si los filtros no se actualizan:

1. **Verificar consola del navegador**:
   - Buscar errores en rojo
   - Verificar que aparecen los logs de debug

2. **Verificar consola del backend**:
   - Buscar logs de debug
   - Verificar que no hay errores de SQL

3. **Verificar red**:
   - Ir a DevTools > Network
   - Verificar que las peticiones a `/api/filter-options` y `/api/cosecha-filtered` retornan 200

### Si aparecen errores de columna:

1. **Verificar base de datos**:
   ```sql
   DESCRIBE hechos_cosecha;
   ```

2. **Verificar consulta SQL**:
   - Revisar logs del backend
   - Verificar que todas las columnas existen

### Si los datos no se filtran:

1. **Verificar parámetros de URL**:
   - Los filtros se envían correctamente
   - Los nombres de parámetros coinciden

2. **Verificar respuesta de API**:
   - Los datos retornados corresponden a los filtros
   - El conteo de registros es correcto

## 📊 Métricas de Éxito

### ✅ Pruebas Exitosas:
- [ ] Backend responde sin errores
- [ ] Filtros se actualizan dinámicamente
- [ ] Datos se filtran correctamente
- [ ] Dashboard se actualiza en tiempo real
- [ ] Logs de debug aparecen correctamente
- [ ] Rendimiento es aceptable (< 1s)

### 📈 KPIs de Rendimiento:
- **Tiempo de respuesta API**: < 500ms
- **Tiempo de actualización UI**: < 200ms
- **Precisión de filtros**: 100%
- **Disponibilidad**: 99.9%

## 🔧 Comandos de Debug

### Backend:
```bash
# Ver logs en tiempo real
tail -f logs/sugarBI.log

# Probar API directamente
curl -X GET "http://localhost:5001/api/filter-options?año=2025" | jq
```

### Frontend:
```javascript
// En la consola del navegador:
// Ver estado actual de filtros
console.log('Filtros actuales:', window.sugarBI?.filters);

// Ver opciones de filtros
console.log('Opciones de filtros:', window.sugarBI?.filterOptions);

// Forzar recarga de filtros
window.sugarBI?.loadFilterOptions();
```

---

## 📝 Notas Adicionales

- **Versión**: 1.0.0
- **Última actualización**: Enero 2025
- **Mantenido por**: Equipo SugarBI

Para reportar problemas, incluir:
1. Pasos para reproducir
2. Logs de consola (frontend y backend)
3. Screenshots del problema
4. Información del navegador y sistema

