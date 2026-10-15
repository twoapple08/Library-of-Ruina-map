"""외부 분화구의 입체 형체. 보행/충돌은 barrier, 보이는 도시는 부품으로 만든다.

먼 곳은 창 무늬 텍스처를 쓰되 기단·층 띠·모서리·옥상 난간·설비는 실제 입체.
가까운 첫 두 테라스는 유리/창틀도 별도 부품이다. 이전 블록 도시의 팔레트는 유지하지 않는다.
"""
from __future__ import annotations

import math
import numpy as np

from tools import forms as F, form_textures as T
from . import detail as D
from . import crater

UP = np.array([0., 1., 0.])
# 고리는 도착 원화의 오른쪽 화면 밖, 동쪽 테라스에 둔다.
# 예전 북동쪽 배치는 원화에 없는 바퀴가 도착 시점의 도시를 가렸다.
WHEEL_SHIFT = np.array([0., -32., 180.])


def materials():
    def mat(name, sprite, **kw):
        return F.mat('ext_city_'+name, sprite, emissive=True, flat=True, ao=False, **kw)
    palette = [((24, 36, 42), (54, 88, 98)), ((32, 30, 48), (82, 66, 98)),
               ((40, 28, 43), (96, 54, 90)), ((27, 37, 46), (65, 96, 112))]
    m = {'wall': [], 'facade': [], 'glass': []}
    for i, (dark, light) in enumerate(palette):
        m['wall'].append(mat(f'wall{i}', T.stone_slab(f'ext_city_wall{i}', dark, light, seed=410+i)))
        m['facade'].append(mat(f'facade{i}', T.neon_facade(f'ext_city_facade{i}', seed=420+i)))
    for i, color in enumerate(((246, 213, 154), (124, 224, 232), (231, 153, 207))):
        m['glass'].append(mat(f'glass{i}', T.flat(f'ext_city_glass{i}', color), glow=(3, 2, 1)[i]))
    m['trim'] = mat('trim', T.metal('ext_city_trim', (32, 32, 40), (100, 100, 116), seed=430))
    m['roof'] = mat('roof', T.stone_slab('ext_city_roof', (30, 31, 34), (65, 67, 74), seed=431))
    m['pave'] = mat('pave', T.stone_slab('ext_city_pave', (36, 37, 42), (86, 86, 94), seed=432))
    m['cloud'] = mat('cloud', T.flat('ext_city_cloud', (130, 135, 141)))
    return m


def annulus(inner, outer, bottom, top, mat, segs):
    """밑면과 안팎 벽까지 닫힌 고리 단면."""
    return F.revolve([(inner, bottom), (outer, bottom), (outer, top-.18),
                      (outer-.18, top), (inner+.18, top), (inner, top-.18), (inner, bottom)],
                     mat, segs=segs, tiles_around=max(4, segs//8), tile_up=64)


def terrain(lay, d, m, collision=True):
    # 광장 가장자리(134)와 첫 옹벽(135) 사이에 낙하 틈이 생기지 않게 한다.
    lay.add(annulus(134,135,-2,0,m['pave'],128),max_edge=4)
    if collision:
        for x0,z0,mask,_,_ in crater._ring_cells(134,135):
            d.place_mask(x0,-1,z0,mask[:,None,:],'minecraft:barrier')
    for i, level in enumerate(crater.TOPS):
        a, b = crater.RINGS[i]*crater.K, crater.RINGS[i+1]*crater.K
        previous = -1 if i == 0 else crater.TOPS[i-1]*crater.K
        top = level*crater.K+1
        q = annulus(a, b, previous-1, top, m['pave'], max(96, int(2*math.pi*a/7)))
        lay.add(F.bake_light(q, sun=(-.45,.65,.4), sky_rgb=(.6,.65,.8)), max_edge=8)
        # 테라스 끝의 돌출 띠 (안팎 두께).
        for radius in (a+.5, b-.5):
            lip = annulus(radius-.5, radius+.5, top-.2, top+.3, m['trim'], max(96, int(2*math.pi*radius/7)))
            lay.add(F.bake_light(lip), max_edge=8)
        if collision:
            for x0, z0, mask, _, _ in crater._ring_cells(a, b):
                d.place_mask(x0, int(top)-1, z0, mask[:, None, :], 'minecraft:barrier')
            for x0, z0, mask, _, _ in crater._ring_cells(a, a+1):
                height = int(top-previous+1)
                d.place_mask(x0, int(previous)-1, z0, np.repeat(mask[:, None, :], height, axis=1), 'minecraft:barrier')


def _box(lo, hi, mat, near):
    return D.beveled_box(lo, hi, mat, .08) if near else F.box(lo, hi, mat, tile=max(np.asarray(hi)-lo))


def building(m, width, depth, height, seed, near=False):
    """직접 쌓은 건물 부품: 기단·네 벽·층 띠·창/살·옥상 난간·기계실·환기기·안테나."""
    rng = np.random.default_rng(seed)
    w, d, h = width/2, depth/2, height
    k = seed % len(m['wall'])
    wall, trim = m['wall'][k], m['trim']
    out = [_box((-w-.5, 0, -d-.5), (w+.5, 1, d+.5), wall, near),
           _box((-w, 1, -d), (w, h, d), wall, near)]
    # 동일한 치수로 네 면을 부품화. 로컬 면은 +Z.
    for length, radius, yaw in ((width, d, 0), (width, d, 180), (depth, w, 90), (depth, w, 270)):
        face = []
        for x in (-length/2, length/2-.24):
            face.append(_box((x, 1, radius), (x+.24, h+.15, radius+.24), trim, near))
        if near:
            # 실제 깊이가 있는 발광 유리와 그 사이의 독립된 수직 창살/수평 인방.
            for y in np.arange(2.2, h-2, 3.2):
                face.append(_box((-length/2, y-.25, radius+.03), (length/2, y, radius+.35), trim, True))
                n = max(1, int((length-1)/2))
                pitch = (length-1)/n
                for j in range(n):
                    x = -length/2+.5+j*pitch
                    mat = m['glass'][(seed+j)%3] if rng.random() < .38 else m['roof']
                    face.append(_box((x+.12, y, radius+.05), (x+pitch-.12, min(y+1.8,h-.5), radius+.11), mat, False))
                    face.append(_box((x, y, radius), (x+.10, min(y+1.9,h-.4), radius+.26), trim, True))
        else:
            face.append(F.plane((-length/2+.25, 1.2, radius+.04), (length-.5,0,0), (0,h-1.6,0),
                                m['facade'][k], tile=(max(length-.5,1),max(h-1.6,1))))
            for y in np.arange(2, h, 7):
                face.append(_box((-length/2, y, radius), (length/2, y+.22, radius+.25), trim, False))
        out.append(F.concat(face).rotate('y', yaw))
    # 지붕을 뚫어 놓지 않으며 난간은 네 개의 따로 떨어진 벽체다.
    for x in (-w, w-.3):
        out.append(_box((x, h, -d), (x+.3, h+1.1, d), trim, near))
    for z in (-d, d-.3):
        out.append(_box((-w, h, z), (w, h+1.1, z+.3), trim, near))
    out.append(_box((-w*.45,h,-d*.4), (w*.45,h+3.5,d*.4), wall, near))
    out.append(_box((-w*.5,h+3.5,-d*.45), (w*.5,h+3.8,d*.45), trim, near))
    for x in (-w*.6, w*.55):
        out.append(_box((x-.5,h+.1,-.6), (x+.5,h+1,.6), trim, near))
        for z in np.linspace(-.4,.4,3):
            out.append(_box((x-.45,h+1,z-.035), (x+.45,h+1.08,z+.035), m['roof'], False))
    if seed % 3 == 0:
        out.append(_box((-.09,h+3.8,-.09), (.09,h+9,.09), trim, False))
        out.append(_box((-.8,h+7,-.06), (.8,h+7.12,.06), trim, False))
    return F.concat(out)


def city(lay, d, m, collision=True):
    rng = np.random.default_rng(401)
    count = 0
    for i, level in enumerate(crater.TOPS):
        a, b = crater.RINGS[i]*crater.K, crater.RINGS[i+1]*crater.K
        rows = 2 if b-a > 80 else 1
        for radius in np.linspace(a+22, b-22, rows):
            n = max(12, int(2*math.pi*radius/(42+i*4)))
            offset = rng.uniform(0, 2*math.pi)
            for j in range(n):
                theta = offset+j*2*math.pi/n
                x, z = radius*math.cos(theta), radius*math.sin(theta)
                # 고리와 검은 기둥의 받침은 비워 겹친 덩어리가 생기지 않게 한다.
                if math.hypot(x-324-WHEEL_SHIFT[0], z+157-WHEEL_SHIFT[2]) < 105:
                    continue
                width, depth = rng.uniform(10,21), rng.uniform(10,20)
                h = rng.uniform(18+i*3,32+i*6)
                base = level*crater.K+1
                q = building(m, width, depth, h, 500+count, near=i<2).translate((x,base,z))
                lay.add(F.bake_light(q, sky_rgb=(.65,.66,.83), ground_rgb=(.5,.42,.45)), max_edge=4 if i<2 else 8)
                if collision:
                    x0,x1 = math.floor(x-width/2),math.ceil(x+width/2)-1
                    z0,z1 = math.floor(z-depth/2),math.ceil(z+depth/2)-1
                    y0,y1 = int(base),int(base+h)
                    for zz in (z0,z1):
                        d.fill(x0,y0,zz,x1,y1,zz,'minecraft:barrier')
                    for xx in (x0,x1):
                        d.fill(xx,y0,z0,xx,y1,z1,'minecraft:barrier')
                    d.fill(x0,y1,z0,x1,y1,z1,'minecraft:barrier')
                count += 1
    return count


def wheel(lay, d, m, collision=True):
    """이중 고리·독립된 기울어진 바퀴살·두꺼운 허브·받침·검은 기둥."""
    angle=-.45
    radial=np.array([math.cos(angle),0,math.sin(angle)])
    tangent=np.array([-math.sin(angle),0,math.cos(angle)])
    center=radial*360+UP*(crater.TOPS[3]+78)
    out=[]
    for radius,thick in ((72,5.5),(58,2.2)):
        points=np.array([center+radius*(math.cos(t)*tangent+math.sin(t)*UP) for t in np.linspace(0,2*math.pi,97)])
        out.append(F.sweep(points,thick,m['trim'],sides=8,step=4,tile_along=8))
    for i in range(10):
        t=i*2*math.pi/10
        p0=center+10*(math.cos(t+.55)*tangent+math.sin(t+.55)*UP)
        p1=center+70*(math.cos(t)*tangent+math.sin(t)*UP)
        # 각재 두께를 가진 바퀴살.
        out.append(F.sweep([p0,p1],2.2,m['trim'],sides=4,step=8,tile_along=8))
    hub=F.revolve([(0,-5),(11,-5),(12,-3),(12,3),(11,5),(0,5)],m['trim'],segs=24,tile_up=12)
    # 회전 단면의 y축을 고리 법선 방향으로 돌린다.
    hub=hub.rotate('x',90).rotate('y',90-math.degrees(angle)).translate(center)
    out.append(hub)
    base=center-UP*78
    out.append(D.beveled_box(base+[-13,0,-9],base+[13,10,9],m['roof'],.5))
    pillar=base+70*tangent+20*radial
    out.append(D.beveled_box(pillar+[-10,0,-10],pillar+[10,3,10],m['trim'],.4))
    out.append(D.beveled_box(pillar+[-8,3,-8],pillar+[8,230,8],m['roof'],.6))
    out.append(D.beveled_box(pillar+[-9,230,-9],pillar+[9,232,9],m['trim'],.4))
    for x in (-6,6):
        out.append(F.box(pillar+[x-.22,4,8],pillar+[x+.22,228,8.4],m['trim'],tile=8))
    lay.add(F.bake_light(F.concat(out).translate(WHEEL_SHIFT),sky_rgb=(.68,.7,.77)),max_edge=6)
    if collision:
        # 형체와 충돌을 같은 만큼 옮겨 옛 위치에 보이지 않는 벽을 남기지 않는다.
        from tools import shapes as S
        class Shifted(S.Part):
            def __init__(self, part):
                self.part = part
                self.lo, self.hi = part.lo+WHEEL_SHIFT, part.hi+WHEEL_SHIFT
                self.lip = part.lip

            def d(self, P, lo=None, hi=None):
                return self.part.d(P-WHEEL_SHIFT, None if lo is None else lo-WHEEL_SHIFT,
                                   None if hi is None else hi-WHEEL_SHIFT)
        parts=[Shifted(p).with_(paint='minecraft:barrier') for p in crater.ring_landmark()]
        S.carve(d,S.Union(*parts),shell=1,smooth=False,only_air=True)


def clouds(lay,m):
    """세 나선 팔의 닫힌 구름 부피. 먼 형체를 굵게, 겹친 반투명 면 남발 없이 굽는다."""
    for arm in range(3):
        t=np.linspace(0,1,95)
        r=400+360*t
        a=arm*2*math.pi/3+1.9*np.log(r/400)+.08*np.sin(t*19+arm)
        points=np.stack([r*np.cos(a),318+18*t+5*np.sin(t*13+arm),r*np.sin(a)],1)
        radius=2+12*np.sin(np.pi*t)**.7
        q=F.sweep(points,lambda s:.45*np.interp(s,t,radius),m['cloud'],sides=8,step=8,
                  tile_along=16,squash=2.2,profile=lambda theta:1+.13*np.cos(theta*3))
        q=F.bake_light(q,sun=(-.6,.8,.2),sky_rgb=(.62,.67,.75),ground_rgb=(.24,.27,.34))
        lay.add(q,max_edge=8)
        # 위쪽 윤곽을 깨는 닫힌 낮은 부피 (단순한 매끈한 관 실루엣을 피한다).
        for i in range(5,len(points)-5,3):
            p=points[i]+np.array([math.sin(i*7)*7,2,math.cos(i*5)*7])
            puff=F.ellipsoid(p,(radius[i]*1.2,radius[i]*.45,radius[i]),m['cloud'],12,5)
            lay.add(F.bake_light(puff,sky_rgb=(.64,.68,.76)),max_edge=8)
        for i in (0,-1):
            cap=F.ellipsoid(points[i],(radius[i]*1.1,radius[i]*.6,radius[i]*1.1),m['cloud'],12,5)
            lay.add(F.bake_light(cap),max_edge=8)


def build(lay,d,city_enabled=True,clouds_enabled=True,collision=True,projection=None):
    m=materials()
    stats={}
    first=len(lay.parts)
    if city_enabled:
        print('  외부 주변: 테라스',flush=True)
        terrain(lay,d,m,collision)
        print('  외부 주변: 도시',flush=True)
        stats['buildings']=city(lay,d,m,collision)
        print(f'  외부 주변: 건물 {stats["buildings"]}개, 고리',flush=True)
        wheel(lay,d,m,collision)
    if clouds_enabled:
        print('  외부 주변: 구름',flush=True)
        clouds(lay,m)
    if projection is not None and len(lay.parts)>first:
        # 도착 색칠은 실제 부품을 완성한 뒤에만 적용한다. 안 보이는 옆/뒤 면은
        # 창·석재·금속의 원본 재질을 유지하고, 형체/충돌/부품 두께는 변하지 않는다.
        cam,art=projection
        # 실제 월드의 칸 분할과 같은 크기로 먼저 나눈다. 큰 벽 하나의 네 모서리가
        # 창틀 뒤에 가렸다는 이유로 벽 전체의 색칠이 누락되지 않게 한다.
        targets=[(F.subdivide(q,e),e) for q,e in lay.parts[first:]]
        print('  외부 주변: 도착 시점 색칠',flush=True)
        painted=F.project_scene([q for q,e in targets],cam,art,
                                occluders=[q for q,e in lay.parts[:first]],
                                min_facing=.5,min_seen=2,zres=(1000,562))
        lay.parts[first:]=[(q,e) for q,(_,e) in zip(painted,targets)]
    return stats
