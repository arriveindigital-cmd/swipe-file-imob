# -*- coding: utf-8 -*-
"""Gera formats.json + formats-data.js (estrutura formato -> exemplos) a partir de:
   - data-catalogo.js (metadados)   - analise-formato.md (análise do formato)
   - exemplo-XX/02-analise/analise-estrutura.md (análise profunda do vídeo)
   - exemplo-XX/02-analise/transcricao-bruta.txt   - drive-map.csv (driveId)
"""
import re, json, os, glob, csv, shutil

BASE = r"G:\Meu Drive\arrive-in-digital\mentoria-imob-in-digital\entregaveis\swipe-files"
OUTDIR = os.path.join(BASE, "site-v2")

# driveId por nome de arquivo (sem .mp4)
drive = {}
csvp = os.path.join(OUTDIR, "drive-map.csv")
if os.path.exists(csvp):
    for row in csv.DictReader(open(csvp, encoding="utf-8")):
        drive[row["arquivo"].strip()] = row["fileId"].strip()

# nomes curtos + descrições (formatos-meta.json)
nomes = {}
metap = os.path.join(OUTDIR, "formatos-meta.json")
if os.path.exists(metap):
    nomes = json.load(open(metap, encoding="utf-8"))

# metadados do catálogo
cat_js = open(os.path.join(BASE, "site", "data-catalogo.js"), encoding="utf-8").read()
meta = {}
for m in re.finditer(r'\{id:"([^"]+)"(.*?)\}', cat_js, re.S):
    pid, body = m.group(1), m.group(2)
    def field(name):
        mm = re.search(name + r':"((?:[^"\\]|\\.)*)"', body)
        return mm.group(1).replace('\\"', '"') if mm else ""
    objs = re.search(r'objetivos:\[([^\]]*)\]', body)
    meta[pid] = dict(
        id=pid, tipo=field("tipo"), nome=field("nome"), exemplo=field("exemplo"),
        link=field("link"), metrica=field("metrica"), plataforma=field("plataforma"),
        status=field("status"), objetivos=re.findall(r'"([^"]+)"', objs.group(1)) if objs else [],
        en=("en:true" in body.replace(" ", "")), ads=("ads:true" in body.replace(" ", "")))

def parse_sections(md):
    """Retorna lista [(titulo, corpo)] das seções ## do markdown (ignora H1)."""
    out, cur, buf = [], None, []
    for line in md.splitlines():
        h = re.match(r'##\s+(.*)', line)
        if h:
            if cur is not None: out.append((cur, "\n".join(buf).strip()))
            cur, buf = h.group(1).strip(), []
        elif cur is not None:
            buf.append(line)
    if cur is not None: out.append((cur, "\n".join(buf).strip()))
    return out

def fmt_key(title):
    t = title.lower()
    for k, needle in [("estrutura","esqueleto"),("hook","hook"),("blocos","estrutura em blocos"),
                      ("porque","por que"),("aplicar","como aplicar"),("guia","guia"),("prompt","prompt")]:
        if needle in t: return k
    return None

def find_dir(pid):
    for tipo in ("organico", "anuncios"):
        for f in glob.glob(os.path.join(BASE, tipo, "*", "analise-formato.md")):
            if re.match(rf'#\s*{pid}\b', open(f, encoding="utf-8").readline()):
                return os.path.dirname(f)
    return None

out = []
for pid, md in meta.items():
    d = find_dir(pid)
    e = dict(md)
    e["nomeLongo"] = md["nome"]
    e["nome"] = nomes.get(pid, {}).get("nome", md["nome"])
    e["desc"] = nomes.get(pid, {}).get("desc", "")
    e["slug"] = os.path.basename(d) if d else ""
    e["formato"] = {}
    e["exemplos"] = []
    if d:
        for t, c in parse_sections(open(os.path.join(d, "analise-formato.md"), encoding="utf-8").read()):
            k = fmt_key(t)
            if k: e["formato"][k] = c
        exdirs = sorted(glob.glob(os.path.join(d, "exemplo-*")))
        for exdir in exdirs:
            cr = re.sub(r'^exemplo-\d+-', '', os.path.basename(exdir))
            ex = dict(criador=cr, driveId="", metrica=md["metrica"], link=md["link"],
                      en=md["en"], temTranscricao=False, analise=[])
            vids = glob.glob(os.path.join(exdir, "01-video", "*.mp4"))
            if vids:
                did = drive.get(os.path.splitext(os.path.basename(vids[0]))[0], "")
                if did:
                    ex["driveId"] = did
                else:
                    # não está no Drive → auto-hospeda no próprio repo
                    vid_out = os.path.join(OUTDIR, "videos")
                    os.makedirs(vid_out, exist_ok=True)
                    shutil.copy(vids[0], os.path.join(vid_out, e["slug"] + ".mp4"))
                    ex["localVid"] = f"videos/{e['slug']}.mp4"
            ana = os.path.join(exdir, "02-analise", "analise-estrutura.md")
            if os.path.exists(ana):
                ex["analise"] = [{"titulo": t, "corpo": c} for t, c in parse_sections(open(ana, encoding="utf-8").read()) if t.lower() != "metadados"]
            tr = os.path.join(exdir, "02-analise", "transcricao-bruta.txt")
            if os.path.exists(tr):
                txt = open(tr, encoding="utf-8").read().strip()
                if txt and not txt.startswith("[SEM"):
                    ex["temTranscricao"] = True; ex["transcricao"] = txt
            # slides de carrossel (formatos de foto): exemplo-XX/slides/1.jpg, 2.jpg...
            sl = sorted(glob.glob(os.path.join(exdir, "slides", "*.jpg")),
                        key=lambda p: int(os.path.splitext(os.path.basename(p))[0]) if os.path.splitext(os.path.basename(p))[0].isdigit() else 999)
            if sl:
                sl_out = os.path.join(OUTDIR, "slides", e["slug"])
                os.makedirs(sl_out, exist_ok=True)
                rel = []
                for i, s in enumerate(sl, 1):
                    shutil.copy(s, os.path.join(sl_out, f"{i}.jpg"))
                    rel.append(f"slides/{e['slug']}/{i}.jpg")
                ex["slides"] = rel
            e["exemplos"].append(ex)
        # prompt profundo APROVADO (do primeiro exemplo que tiver prompt.md)
        for exdir in exdirs:
            pp = os.path.join(exdir, "03-prompt-replicacao", "prompt.md")
            if os.path.exists(pp):
                raw = open(pp, encoding="utf-8").read().splitlines()
                idx = next((i for i, l in enumerate(raw) if l.strip() == "---"), None)
                body = "\n".join(raw[idx+1:]).strip() if idx is not None else "\n".join(raw).strip()
                if body:
                    e["formato"]["prompt"] = body
                break
        # guia de uso (do primeiro exemplo que tiver guia-de-uso.md) — independente do prompt.md
        for exdir in exdirs:
            gp = os.path.join(exdir, "03-prompt-replicacao", "guia-de-uso.md")
            if os.path.exists(gp):
                e["formato"]["guiaPrompt"] = [{"titulo": t, "corpo": c}
                                              for t, c in parse_sections(open(gp, encoding="utf-8").read())]
                break
    out.append(e)

out.sort(key=lambda x: (x["tipo"] != "organico", x["id"]))
for i, e in enumerate(out, 1):
    e["num"] = i   # número sequencial estável do formato (1..82)
json.dump(out, open(os.path.join(OUTDIR, "formats.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open(os.path.join(OUTDIR, "formats-data.js"), "w", encoding="utf-8").write(
    "window.FORMATS = " + json.dumps(out, ensure_ascii=False) + ";\n")

nex = sum(len(e["exemplos"]) for e in out)
print(f"formatos={len(out)} | exemplos={nex} | com driveId={sum(1 for e in out for x in e['exemplos'] if x['driveId'])}")
print(f"formato c/ análise={sum(1 for e in out if e['formato'])} | exemplos c/ análise-vídeo={sum(1 for e in out for x in e['exemplos'] if x['analise'])}")
