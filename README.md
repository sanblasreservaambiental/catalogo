# Catálogo de especies · San Blas Reserva Ambiental

Web con las plantas y aves de San Blas Reserva Ambiental (San Miguel de Abona, Tenerife):
foto, descripción y usos tradicionales en **español de Canarias, inglés y alemán**.

Pensada para publicarse en https://sanblasreservaambiental.org/catalogo/ (GitHub Pages).

## Archivos

| Archivo | Qué contiene |
|---|---|
| `index.html`, `estilo.css`, `catalogo.js` | La web (mismo estilo que *Materiales*). Sin dependencias. |
| `datos.js` | Las fichas de cada especie, en los tres idiomas. Aquí se corrigen textos o se añaden especies. |
| `datos-inat.js` | Especies observadas en iNaturalist alrededor de la reserva (se genera con el script). |
| `taxonomia.js` | Reino, clase, orden y familia de cada especie, para el selector de nivel (se genera con el script). |
| `img/` | Imágenes de las guías de plantas y aves de San Blas. |
| `img/inat/` | Fotos de iNaturalist con licencia Creative Commons (las descarga el script). |
| `herramientas/actualizar_inat.py` | Actualiza `datos-inat.js` desde el proyecto de iNaturalist. |

## Actualizar las especies de iNaturalist

```
python herramientas/actualizar_inat.py            # consulta iNaturalist
python herramientas/actualizar_inat.py --sin-red  # regenera desde la copia guardada
```

El script recoge **todas las observaciones de iNaturalist en un radio de 750 m alrededor de la reserva**
(no solo las del proyecto [San Blas Reserva Ambiental](https://www.inaturalist.org/projects/san-blas-reserva-ambiental),
que todavía tiene pocas), las agrupa por especie y guarda el resultado en `herramientas/inat-cache.tsv`.
Después genera `datos-inat.js` y descarga la foto representativa de cada especie nueva **solo si tiene licencia
Creative Commons**, guardando autor y licencia (la web los muestra en la ficha). Si las fotos pesan mucho,
conviene reducirlas a unos 700 px antes de subirlas.

Las correcciones a mano van en `herramientas/ajustes-inat.json`:

- `nombres_es`: nombre canario cuando el de iNaturalist no sirve (p. ej. *Cenchrus setaceus* → «Rabo de gato»).
- `estatus`: endémica, nativa, introducida, **invasora**… (claves de `ESTATUS` en `datos.js`).
- `excluir`: especies que aparecen por observaciones con ubicación oculta pero no viven aquí.
- `alias`: cuando iNaturalist usa otro nombre científico que nuestras fichas.

Las especies que ya tienen ficha en `datos.js` reciben el número de observaciones y el enlace a iNaturalist;
las nuevas aparecen como «ficha en preparación» hasta que se redacte su texto en `datos.js`. Las observaciones
con ubicación oculta (especies protegidas o autores que la esconden) llevan la etiqueta «Ubicación aproximada».

## Nivel del alumnado

Encima de los filtros hay un deslizador con cuatro niveles, los mismos de los cuadernos:

1. **Primaria 3.º–4.º · Reinos**: plantas, animales u hongos; solo nombres comunes.
2. **Primaria 5.º–6.º · Grupos**: aves, reptiles, peces, insectos, arácnidos, moluscos…
3. **ESO · Clases y órdenes**: filtros por clase y tarjetas agrupadas por orden.
4. **Bachillerato y FP · Familias**: tarjetas agrupadas por familia y clasificación completa en la ficha.

Los nombres en español de clases, órdenes y familias están en `herramientas/ajustes-inat.json` → `nombres_rangos`.
El nivel se puede fijar en el enlace con `?nivel=1` … `?nivel=4`.

## Enlaces directos

Cada ficha tiene su propia dirección, p. ej. `…/catalogo/#cardon`, y el idioma se puede fijar con `?lang=en` o `?lang=de`.
