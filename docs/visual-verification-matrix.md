# AEGIS visual verification matrix

This capture set documents the principal product surfaces in the four supported presentation combinations. The matrix is deliberately limited to the authenticated/public product routes a user actively uses; it excludes reset-password and registration variants because they reuse the same public authentication shell.

| Surface | Route or state | English light | English dark | Persian light | Persian dark |
|---|---|---:|---:|---:|---:|
| Public entry | `/` | Yes | Yes | Yes | Yes |
| Digital-trust dashboard | `/dashboard` | Yes | Yes | Yes | Yes |
| Scanner workspace | `/scan` | Yes | Yes | Yes | Yes |
| Completed scanner assessment | Guided email demo on `/scan` | Yes | Yes | Yes | Yes |
| Verified threat map | `/map` | Yes | Yes | Yes | Yes |
| Learning center | `/learn` | Yes | Yes | Yes | Yes |
| Profile and preferences | `/profile` | Yes | Yes | Yes | Yes |
| Operator console | `/admin` | Yes | Yes | Yes | Yes |
| Assessment casefile | Guided assessment casefile (`/report/<id>`) | Yes | Yes | Yes | Yes |

The result is **36 requested visual states**. All screenshots use the same demo administrator and fixed fictional assessment sample so hierarchy, theme contrast, RTL structure, bidirectional text, and component variants can be compared directly. The accompanying [`visual-capture-index.tsv`](visual-capture-index.tsv) records the source path, locale-theme label, and route purpose for every image.
