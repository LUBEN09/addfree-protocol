
# Adfree Protocol (adfree/1)

> Un protocolo abierto sobre HTTPS para negociar y aplicar políticas de publicidad regulada entre cliente y servidor.

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

## 📖 Especificación

Documento de diseño (SDD v0.1): [SDD-ADFREE-v0.1.md](./SDD-ADFREE-v0.1.md)

## 🧩 Componentes de Referencia

| Componente       | Tecnología       | Estado     |
|------------------|------------------|------------|
| Proxy            | Python 3.11+     | 🚧 En desarrollo |
| WebExtension     | Chrome/Firefox   | 🚧 En desarrollo |
| Server Module    | Nginx/Lua, Go    | 🚧 En desarrollo |
| Portal           | React/Next.js    | 🚧 En desarrollo |
| Test Harness     | Playwright       | 🚧 En desarrollo |

## 🛠️ Requisitos

- Python 3.11+ (para proxy)
- Node.js 18+ (para portal y test-harness)
- Nginx/OpenResty (para server-module)

## 🚀 Primeros pasos

```bash
# Clona el repo
git clone https://github.com/LUBEN09/adfree-protocol.git
cd adfree-protocol

# Explora cada componente
cd packages/proxy-ref
pip install -r requirements.txt
python -m adfree_proxy --help