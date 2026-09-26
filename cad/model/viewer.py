#!/usr/bin/env python3
"""Writes cad/out/viewer.html: a rotatable 3D view of cad/out/concept_v0.glb (embedded)."""
import base64
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "out")
glb = base64.b64encode(open(os.path.join(OUT, "concept_v0.glb"), "rb").read()).decode()

HTML = r"""<title>Dweilrobo 3D</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;600&family=JetBrains+Mono:wght@400&display=swap">
<style>
:root{--bg:#eef1f3;--panel:#ffffffe6;--ink:#1b2328;--muted:#5d6b73;--line:#cfd7dc;--accent:#0f7c8c;--grid:#c3ccd1;
  --sans:"Barlow",system-ui,sans-serif;--mono:"JetBrains Mono",ui-monospace,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#12181b;--panel:#1b2327e6;--ink:#e3eaee;--muted:#93a3ab;--line:#2d393f;--accent:#4cc1d0;--grid:#2a353a;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#12181b;--panel:#1b2327e6;--ink:#e3eaee;--muted:#93a3ab;--line:#2d393f;--accent:#4cc1d0;--grid:#2a353a;color-scheme:dark}
html,body{height:100%}
body{background:var(--bg);color:var(--ink);font-family:var(--sans);overflow:hidden}
#view{position:fixed;inset:0}
.panel{position:fixed;left:16px;top:calc(16px + env(safe-area-inset-top,0px));max-width:min(320px,calc(100% - 32px));
  background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 16px;display:grid;gap:10px;backdrop-filter:blur(6px)}
h1{margin:0;font-size:18px;font-weight:600;text-wrap:balance}
.note{margin:0;color:var(--muted);font-size:13px;line-height:1.4}
.groups{display:flex;flex-wrap:wrap;gap:6px}
.groups button{font:600 12px var(--sans);letter-spacing:.03em;border:1px solid var(--line);background:transparent;color:var(--ink);
  border-radius:999px;padding:5px 10px;cursor:pointer;display:flex;gap:6px;align-items:center}
.groups button[aria-pressed="false"]{opacity:.45;text-decoration:line-through}
.groups button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.dot{width:9px;height:9px;border-radius:50%}
.dims{font:12px var(--mono);color:var(--muted);font-variant-numeric:tabular-nums}
.hint{position:fixed;right:16px;bottom:calc(16px + env(safe-area-inset-bottom,0px));font-size:12px;color:var(--muted)}
</style>
<div id="view"></div>
<section class="panel">
  <h1>Dweilrobo, concept v0</h1>
  <p class="note">Grove blokken om te zien of alles past. Bijna alle maten zijn nog geschat. Tik een groep aan om hem te verbergen.</p>
  <div class="groups" id="groups"></div>
  <div class="dims">Ø350 mm · hoogte ≈170 mm · pads Ø130</div>
</section>
<div class="hint">Slepen = draaien · scrollen/knijpen = zoomen</div>
<script src="https://cdn.jsdelivr.net/npm/three@0.147.0/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.147.0/examples/js/controls/OrbitControls.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.147.0/examples/js/loaders/GLTFLoader.js"></script>
<script>
const GLB="__GLB__";
const GROUPS=[
 ["Frame",["base_plate"],"#d2a86e"],["Bovendek",["top_deck"],"#e8d6b0"],["Lidar",["lidar"],"#b22222"],
 ["Wielen + motoren",["wheel","drive_motor","caster"],"#555"],["Mop-pads",["pad_","mop_motor"],"#6cb4ee"],
 ["Watertank",["tank"],"#9fd0e8"],["Batterij",["battery"],"#e6c229"],["Elektronica",["electronics"],"#8fd18f"]];
const el=document.getElementById("view");
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));el.appendChild(renderer.domElement);
const scene=new THREE.Scene();
const cam=new THREE.PerspectiveCamera(35,1,5,5000);cam.position.set(420,380,-520);
const ctl=new THREE.OrbitControls(cam,renderer.domElement);ctl.target.set(0,60,0);ctl.enableDamping=true;
scene.add(new THREE.HemisphereLight(0xffffff,0x8899aa,1.1));
const sun=new THREE.DirectionalLight(0xffffff,0.8);sun.position.set(300,600,-200);scene.add(sun);
const gridCol=getComputedStyle(document.documentElement).getPropertyValue("--grid").trim()||"#ccc";
const grid=new THREE.GridHelper(600,12,gridCol,gridCol);scene.add(grid);
function resize(){const w=el.clientWidth,h=el.clientHeight;renderer.setSize(w,h);cam.aspect=w/h;cam.updateProjectionMatrix()}
addEventListener("resize",resize);resize();
const bytes=Uint8Array.from(atob(GLB),c=>c.charCodeAt(0)).buffer;
new THREE.GLTFLoader().parse(bytes,"",g=>{
  const root=g.scene;scene.add(root);
  const meshes=[];root.traverse(o=>{if(o.isMesh){o.material.side=THREE.DoubleSide;o.material.metalness=0;o.material.roughness=0.75;meshes.push(o)}});
  const nameOf=o=>{let n="";for(let p=o;p;p=p.parent)n+=" "+(p.name||"");return n};
  const box=document.getElementById("groups");
  GROUPS.forEach(([label,keys,col])=>{
    const ms=meshes.filter(m=>keys.some(k=>nameOf(m).includes(k)));if(!ms.length)return;
    const b=document.createElement("button");b.type="button";b.setAttribute("aria-pressed","true");
    b.innerHTML=`<span class="dot" style="background:${col}"></span>${label}`;
    b.onclick=()=>{const on=b.getAttribute("aria-pressed")!=="true";b.setAttribute("aria-pressed",on);ms.forEach(m=>m.visible=on)};
    box.appendChild(b);
  });
},e=>{document.querySelector(".note").textContent="Model laden mislukt: "+e});
(function loop(){requestAnimationFrame(loop);ctl.update();renderer.render(scene,cam)})();
</script>
"""
open(os.path.join(OUT, "viewer.html"), "w").write(HTML.replace("__GLB__", glb))
print("wrote cad/out/viewer.html")
