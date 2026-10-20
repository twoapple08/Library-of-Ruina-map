"""Unprojected model preview: CPU raster fallback, no WebGPU or game required."""
import base64,io,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw,ImageFont
from tools import forms as F, form_raster as R
from tools.model_import import load_bbmodel
p=ROOT / 'design/models/tiphereth_table.bbmodel'
d=json.loads(p.read_text())
img=Image.open(io.BytesIO(base64.b64decode(d['textures'][0]['source'].split(',')[1]))).convert('RGBA')
m=F.mat('table_preview',F.texture('table_preview',img),emissive=True,ao=False)
q=F.bake_light(load_bbmodel(p,{0:m}), sun=(-.4,.8,.45), sky_rgb=(.35,.32,.28))
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',19)
W,H=480,320
sheet=Image.new('RGB',(W*3, H+34),(23,21,24));draw=ImageDraw.Draw(sheet)
for i,(label,pos) in enumerate([('Front / unprojected',(0,1.3,3.7)),('Side / unprojected',(3,1.3,.1)),('Back / unprojected',(-2,1.8,-3.3))]):
 cam=F.Camera.look_at(pos,(0,.45,0),aspect=W/H)
 im,_=R.render([q],cam,W,H,bg=(38,34,31))
 sheet.paste(im,(i*W,34));draw.text((i*W+10,7),label,font=font,fill='white')
out=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT / 'previews/tiphereth_table_2026-10-20.jpg'
sheet.save(out,quality=92)
print(out)
