# Favicon Package — Pickaxe + Magnifier (Design #1)
Date: 2025-08-10 15:30:56
Author: Auto-generated

## Files
- favicon.svg
- favicon.ico (16, 32, 48, 64, 128, 256)
- favicon-16.png
- favicon-32.png
- favicon-48.png
- favicon-64.png
- favicon-128.png
- favicon-192.png
- favicon-256.png
- favicon-512.png

## Colors
- Theme (graphite): #2E2E2E (RGBA 46,46,46,255)
- Accent (amber):   #FFC107 (RGBA 255,193,7,255)

## HTML (drop in <head>)
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/favicon-192.png">
<link rel="manifest" href="/site.webmanifest">

## Express (Node) static example
app.use(express.static("public"));
// Put files in: public/favicon.ico, public/favicon.svg, public/favicon-192.png, etc.

## Notes
- Raster PNGs are derived from a 1024×1024 master for sharp downscaling.
- Shapes are simplified for readability at 16×16.
- Background is transparent.
