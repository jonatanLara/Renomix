<p align="center">
  <img 
    src="https://github.com/jonatanLara/jonatanLara/blob/main/src/header_3_t.png?raw=true" 
    alt="Hoja Calendario"
    width="73%"
  />
</p>

<p align="center">
  <a href="https://github.com/jonatanLara">🐙 GitHub</a> |
  <a href="https://www.youtube.com/@jonatanlara">📺 YouTube</a> |
  <a href="https://www.instagram.com/jonatanlaraortiz/">📸 Instagram</a>
</p>
<br>




<p align="center">
  <img 
    src="https://github.com/jonatanLara/jonatanLara/blob/main/src/autor_1.png?raw=true" 
    alt="Hoja Calendario"
    width="100%"
  />
</p>
<br>

# Renomix

**Renomix** es una aplicación de escritorio desarrollada en **Python + Tkinter + SQLite** para el **renombrado masivo de archivos** con historial, reportes y opción de deshacer cambios.  

---

## ✨ Características principales
- Renombrado masivo con **prefijo, sufijo, separador y patrones dinámicos**.
- Modos:
  - **Renombrar en la misma carpeta**.
  - **Copiar a carpeta destino** (manteniendo originales).
- Políticas de conflicto configurables:
  - `increment` → agrega `(1)`, `(2)`…  
  - `overwrite` → reemplaza  
  - `skip` → omite el archivo
- **Previsualización** antes de aplicar.
- **Historial** guardado en SQLite (`renomix.db`).
- **Deshacer último lote** (undo por batch).
- Menú bar con opciones de **reportes y estadísticas**.

---

## 📦 Instalación

### Requisitos
- Python 3.9 o superior.
- No necesita dependencias externas (usa solo librerías estándar).

### Ejecución
```bash
git clone https://github.com/tuusuario/renomix.git
cd renomix
python main.py
```

---

## 🖥️ Uso

### Parámetros principales
- **Carpeta origen**: directorio donde están los archivos.
- **Extensiones**: lista separada por comas (`jpg,png,tif`).
- **Prefijo / Sufijo / Separador**: personaliza el nombre.
- **Patrón**: `{prefix}{name}{suffix}{ext}`.
- **Destino**:
  - `overwrite` → renombra en la misma carpeta.
  - `copy` → copia a carpeta destino.

### Acciones
- **Previsualizar** → muestra los cambios sin aplicarlos.
- **Aplicar cambios** → ejecuta el renombrado/copiado.
- **Deshacer último lote** → revierte el último renombrado.

---

## 📂 Menú Bar

### Archivo
- Exportar historial a CSV  
- Abrir carpeta de la BD  
- Salir

### Ver *(solo si hay datos en la BD)*
- Actividad reciente  
- Lotes (batches)  
- Top extensiones  

### Reportes
- Resumen de operaciones  

### Herramientas
- Compactar BD (VACUUM)  

### Ayuda
- Documentación  
- Acerca de  

---

## 📊 Historial y Reportes
- Cada lote se guarda con un `batch_id`.
- Consultable desde el menú **Ver/Reportes**.
- Exportable a CSV.

---

## 🔄 Deshacer (Undo)
- Si fue **copy** → elimina las copias.  
- Si fue **rename** → devuelve el nombre original (si existe, añade `(revert)`).  

---

## 📸 Capturas de pantalla (opcional)
> *(Puedes añadir imágenes de la interfaz aquí con Markdown)*  
Ejemplo:
```markdown
![Pantalla principal](docs/img/main.png)
```

---

## 📌 Futuras mejoras
- Preferencias guardadas (tema, política por defecto).
- Numeración automática con ceros (`001, 002…`).
- Detección de duplicados con hash MD5.
- Interfaz con tema oscuro/claro.

---

<p align="center">
  <img 
    src="https://github.com/jonatanLara/jonatanLara/blob/main/src/autor_1.png?raw=true" 
    alt="Hoja Calendario"
    width="100%"
  />
</p>
<br>

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas!  
Si tienes mejoras, errores que reportar o ideas para funciones nuevas, no dudes en abrir un issue o pull request.

---
## 📄 Licencia

Este proyecto está bajo la licencia [MIT](LICENSE).

---
