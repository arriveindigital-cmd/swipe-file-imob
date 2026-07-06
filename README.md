# Swipe File Viral — Site v2 (Arrive In Digital)

Web app **format-first** do swipe file: 82 formatos do mercado imobiliário, cada um com exemplo real, **player de vídeo interno**, análise de estrutura, guia e prompt de replicação.

## Vídeos: Google Drive
Os 77 vídeos estão no Google Drive (públicos "qualquer pessoa com o link"). O site usa o **embed do Drive** — thumbnail real no card + player no modal —, então **funciona igual local e no Vercel, sem hospedar nada**. O mapa `arquivo → fileId` está em `drive-map.csv`.

## Testar local
Dê dois cliques em `index.html`. Precisa de internet (os vídeos vêm do Drive). Os cards mostram a miniatura do Drive; clicar abre o player embutido.

## Arquivos
| Arquivo | O que é |
|---|---|
| `index.html` | Interface (marca Arrive: roxo #7c3aed + laranja #f97316, tema escuro, Inter) |
| `formats-data.js` | Os 82 formatos + análises + `driveId` de cada vídeo (abre com 2 cliques, sem servidor) |
| `formats.json` | Mesmos dados em JSON limpo (para o deploy/Vercel via fetch) |
| `drive-map.csv` | Mapa `arquivo,fileId,link,status` dos 77 vídeos no Drive |

## Como regenerar os dados
Os dados saem dos 82 `analise-formato.md` + `../site/data-catalogo.js`. Depois de editar qualquer análise, rode o gerador:
```
python gen_formats.py    # (script no scratchpad da sessão; mover para cá se for versionar)
```
Ele reescreve `formats.json` e `formats-data.js`.

## Publicar no Vercel
Como os vídeos vêm do Drive, o deploy é só os arquivos leves desta pasta (nada de vídeo).

1. Suba **só o conteúdo de `site-v2/`** num repositório (ou pasta) — `index.html`, `formats-data.js`, `formats.json`, `drive-map.csv`, `README.md`.
   - **Não** inclua `_videos-upload/` (612 MB) — já está no `.gitignore`. Pode apagar essa pasta local depois de confirmar que o Drive está no ar (o `drive-map.csv` já foi copiado pra cá).
2. No Vercel: **Add New → Project** → aponte pra essa pasta. Sem build, publica direto.
3. `noindex` já está no HTML. Link público = acessível por quem tiver o link (não é proteção).

## Como regenerar (quando editar uma análise ou trocar vídeo)
```
python gen_formats.py
```
Relê os 82 `analise-formato.md` + `../site/data-catalogo.js` + `drive-map.csv` e reescreve `formats.json` e `formats-data.js`.

## Ressalva do Google Drive
Drive tem uma cota de exibição por arquivo/dia. Para tráfego baixo/médio não incomoda; se algum vídeo muito acessado der "não é possível exibir agora", é temporário. Se um dia o tráfego crescer muito, migrar pra um CDN (R2/Bunny) é trocar o `driveId` por URL — o resto do site não muda.
