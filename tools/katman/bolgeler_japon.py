"""Bolge maskeleri: gunes, dag, ev, geri kalanlar (ayrik, ikili)."""
import numpy as np, cv2
from PIL import Image
from scipy import ndimage as ndi
from skimage import morphology, measure
import sys, os
SRC = sys.argv[1] if len(sys.argv) > 1 else 'cikti/japon.jfif'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'bolgeler.npz'
im=np.asarray(Image.open(SRC).convert('RGB')).astype(np.int32)
H,W=im.shape[:2]; R,G,B=im[...,0],im[...,1],im[...,2]
lum=0.299*R+0.587*G+0.114*B
red=(R>100)&(R-G>60)&(R-B>50)
yy,xx=np.mgrid[0:H,0:W]
def poly(pts):
    m=np.zeros((H,W),np.uint8); cv2.fillPoly(m,[np.round(np.array(pts)).astype(np.int32)],1); return m.astype(bool)
def fill_small_holes(m,maxa):
    h=ndi.binary_fill_holes(m)&~m
    lab=measure.label(h); sizes=np.bincount(lab.ravel())
    keep=sizes<=maxa; keep[0]=False
    return m|keep[lab]
# ---------------- EV (v2: ince el izi cati/govde + piksel tabanli torii ve fenerler) ----------------
PAGODA=[(1017,417),(1023,417),(1025,428),(1028,432),(1029,452),(1032,456),(1034,470),(1031,480),(1029,486),
  (1040,497),(1060,507),(1080,515),(1100,524),(1120,533),(1140,542),(1160,548),(1180,552),(1200,551),(1206,555),
  (1203,563),(1185,570),(1170,578),(1160,585),(1150,590),(1140,595),(1119,600),
  (1119,611),(1143,611),(1143,628),(1148,628),(1148,640),
  (1150,643),(1175,649),(1200,653),(1216,661),(1215,668),
  (1207,681),(1190,689),(1170,690),(1152,692),
  (1148,697),(1135,698),(1135,706),(1125,706),(1125,713),(1164,713),(1164,746),
  (1178,752),(1180,762),(1160,768),(1142,775),
  (1115,795),(1107,815),(1102,830),(1097,846),(1070,846),(1060,836),(1045,826),(1030,822),(1000,825),(960,835),(930,846),(905,846),
  (898,812),(897,801),(925,792),(955,780),
  (930,780),(900,780),(870,780),(850,778),(840,773),(828,765),(820,756),(822,749),(840,752),(860,753),(887,750),
  (887,746),(888,716),(925,714),(925,681),
  (940,673),(910,678),(880,682),(850,683),(838,676),(822,665),(819,659),(821,655),
  (840,657),(860,655),(880,650),(900,645),(917,639),
  (917,608),(922,600),(926,585),(928,576),
  (920,573),(900,578),(880,578),(865,572),(853,564),(851,558),
  (856,555),(880,555),(900,550),(920,543),(940,534),(960,521),(985,509),(1002,498),(1012,486),
  (1011,480),(1010,467),(1012,456),(1014,450),(1014,432),(1016,428)]
KASAGI=[(717,812),(723,806),(750,803),(800,804),(850,804),(897,802),(900,824),(730,825)]
TORII_ZONE=[(712,798),(905,790),(905,880),(895,990),(765,990),(712,880)]
LANTERNS=[(876,574,894,598),(1164,574,1182,598),(840,676,858,702),(1188,678,1206,702),(841,774,859,797)]
def ev_mask():
    pag=poly(PAGODA)
    # torii: kirmizi bilesenler + kasagi; direkler arasi zemin/cam girmez (kirmizi degil)
    tz=poly(TORII_ZONE)&~pag
    tr=(red|(((R-G)>35)&(R>B+25)&(R>40)))&tz   # golgeli koyu kirmizi direk yuzu dahil
    tr&=~((xx<732)&(yy<836))   # kasagi ucunun arkasindaki cicek yapraklari torii degil
    tr=morphology.closing(tr,morphology.disk(2))
    tr=fill_small_holes(tr,150)
    tr=tr|poly(KASAGI)
    tr=(morphology.dilation(tr,morphology.disk(1))|(morphology.dilation(tr,morphology.disk(3))&((lum<110)|((R-G)>25))))&tz  # siyah kontur ve kenar
    lab=measure.label(tr); kas=morphology.dilation(poly(KASAGI),morphology.disk(2))
    keep=np.unique(lab[kas&tr]); tr=np.isin(lab,keep[keep>0])   # yalniz kasagiye bagli parcalar (direkler, kirisler)
    # fenerler: kucuk pencerede kirmizi + ona 3 px icindeki koyu (kontur, ip)
    lan=np.zeros((H,W),bool)
    for x0,y0,x1,y1 in LANTERNS:
        win=np.zeros((H,W),bool); win[y0:y1,x0:x1]=True
        r_=((R-G)>40)&(R>60)&win
        dk=(lum<120)&win&morphology.dilation(r_,morphology.disk(4))
        l_=fill_small_holes(morphology.closing(r_|dk,morphology.disk(1)),40)
        l_|=morphology.dilation(l_,morphology.disk(1))&win&((lum<150)|((R-G)>25))
        lan|=l_
    return pag|tr|lan
# ---------------- SILUET ----------------
cl,cr=np.load('silfit.npy')
def silhouette_y(x):
    x=np.asarray(x,float)
    # icerde olculen egriler; disarida elle okunan noktalara dogrusal
    left_pts=[(520,477),(560,467),(600,452),(650,434),(700,np.polyval(cl,700))]
    right_pts=[(1040,np.polyval(cr,1040)),(1060,411),(1080,423),(1100,433),(1118,439)]
    y=np.where(x<866,np.polyval(cl,x),np.where(x>910,np.polyval(cr,x),305.0))
    lp=np.array(left_pts); rp=np.array(right_pts)
    y=np.where(x<700,np.interp(x,lp[:,0],lp[:,1]),y)
    y=np.where(x>1040,np.interp(x,rp[:,0],rp[:,1]),y)
    return y
ZONE_BOTTOM=[(1118,439),(1116,446),(1114,468),(1104,478),(1099,492),(1099,506),(1104,520),(1112,533),(1112,548),(1100,548),(1100,700),(925,700),(925,720),(858,720),(845,705),(822,692),(793,686),(760,658),(740,640),(700,625),(660,612),(600,585),(560,585),(545,495),(520,477)]
def dag_mask(ev):
    xs=np.arange(520,1119); top=silhouette_y(xs)
    pts=[(x,y) for x,y in zip(xs,top)]+ZONE_BOTTOM[1:-1]
    zone=poly(pts)|poly([(830,775),(962,768),(955,778),(900,794),(876,800),(830,801)])   # pagoda-torii arasi dag kamasi
    light=(lum>150)&~red
    ld=ndi.gaussian_filter(light.astype(float),3)
    cloud=morphology.opening(ld>0.5,morphology.disk(2))
    cloud=morphology.remove_small_objects(cloud,max_size=150)
    cloud=morphology.dilation(cloud,morphology.disk(2))
    cloud&=(yy>=478)
    m=zone&~ev&~cloud
    m=morphology.opening(m,morphology.disk(1))
    m=morphology.remove_small_objects(m,max_size=300)
    m=fill_small_holes(m,400)&zone&~ev
    # sag sirt (gunes disi): siluet ustundeki 1-3 px krem seridi Dag'dan cikar
    sil=np.zeros((H,W)); sil[:,520:1119]=silhouette_y(np.arange(520,1119))[None,:]
    band=(yy<sil+4)&(xx>=1000)&m
    m&=~(band&(lum>150)&~red)
    # kucuk kirmizi bilesenler (dusen yaprak) -> geri kalanlar
    reddish=red|(((R-G)>35)&(R>B+25)&(R>40))
    rd=morphology.dilation(reddish&m,morphology.disk(2))&m
    m&=~rd
    return m,zone
# ---------------- GUNES ----------------
cx,cy,r=np.load('circle2.npy')
tw=poly([(663,282),(672,277),(681,286),(675,293)])&(R<120)
BUDS=(np.hypot(xx-696,yy-320)<=8)|(np.hypot(xx-679,yy-368)<=4)|poly([(678,316),(692,315),(693,328),(680,329)])\
    |poly([(655,324),(672,326),(681,340),(679,353),(662,356),(655,350)])|morphology.dilation(tw,morphology.disk(1))
def gunes_mask(dag,ev):
    rr=np.hypot(xx-cx,yy-cy)
    disk=rr<=r+2.5
    sunred=red&disk
    a=morphology.opening(sunred,morphology.disk(3))
    lab=measure.label(a); comp=lab==lab[int(cy),int(cx)]
    # dal: disk icinde, dag disinda, ham pikselde kirmizi olmayan (krem dalcik + siyah kontur)
    nonred=disk&~((R-G)>60)&~dag&(rr<=r-1.5)&(xx<790)   # gunes icindeki tek dal sol tarafta
    branch=morphology.remove_small_objects(nonred,max_size=3)
    branch=morphology.closing(branch,morphology.disk(4))      # tomurcuklari dalla birlestir
    branch=fill_small_holes(branch,1500)                       # konturla cevrili tomurcuk ici
    branch=morphology.dilation(branch,morphology.disk(1))
    comp=fill_small_holes(comp,250)&~branch
    # kenar: krem halka almadan kirmizimsi kenar piksellerini ekle
    edge=morphology.dilation(comp,morphology.disk(4))&((R-G)>40)&(rr<=r+5)&~branch
    m=(comp|edge)&~dag&~ev
    # dal bolgesi: tomurcuklar koyu konturla ana diskten ayrilir -> yalniz ana bilesen kalir
    BZ=poly([(650,290),(760,320),(760,385),(650,385)])
    core=m&~(BZ&~(((R-G)>90)&(R>=115)))
    core=morphology.opening(core,morphology.disk(1))|(m&~morphology.dilation(BZ,morphology.disk(2)))
    lab=measure.label(core,connectivity=1); main=lab==lab[int(cy),int(cx)]
    m=m&(main|~BZ)
    m=m&~(BZ&~morphology.dilation(main,morphology.disk(1)))
    # elle isaretlenen tomurcuk/dalcik parcalari (7x buyutmede okundu) -> Geri Kalanlar
    m&=~BUDS
    lab=measure.label(m,connectivity=1); m=lab==lab[int(cy),int(cx)]
    return m
def kucuk_parcalari_dagit(masks,maxa=60,koru=None):
    """Bir grubun kucuk kopuk parcalarini en cok komsu oldugu gruba verir (ayrik bolum korunur)."""
    keys=list(masks); L=np.zeros((H,W),np.int8)
    for i,k in enumerate(keys): L[masks[k]]=i
    moved=0
    for i,k in enumerate(keys):
        lab=measure.label(L==i,connectivity=1); sizes=np.bincount(lab.ravel())
        for c in np.where((sizes<=maxa)&(np.arange(len(sizes))>0))[0]:
            comp=lab==c
            if koru is not None and (comp&koru).any(): continue
            ring=morphology.dilation(comp,morphology.disk(1))&~comp
            nb=L[ring]; nb=nb[nb!=i]
            if len(nb)==0: continue
            L[comp]=np.bincount(nb,minlength=len(keys)).argmax(); moved+=int(comp.sum())
    return {k:(L==i) for i,k in enumerate(keys)},moved
if __name__=='__main__':
    ev=ev_mask(); dag,zone=dag_mask(ev); gun=gunes_mask(dag,ev)
    gk=~(ev|dag|gun)
    # gunes ile dag arasinda kalan 1-2 px kontur hatti (tek kaynak) -> Dag (kontur dagin cizgisi)
    ara=gk&morphology.dilation(gun,morphology.disk(2))&morphology.dilation(dag,morphology.disk(2))&~BUDS
    dag=dag|ara; gk=gk&~ara; print('gunes-dag arasi -> Dag px',int(ara.sum()))
    # pagoda kenarinda disarida kalan kirmizi suslemeler -> Ev
    reddish=red|(((R-G)>35)&(R>B+25)&(R>40))
    kenar=(reddish|(((R-G)>18)&(R>B+10)&(R>30)&(lum<110)))&(gk|dag)&morphology.dilation(ev,morphology.disk(12))&morphology.dilation(poly(PAGODA),morphology.disk(10))
    kenar=morphology.dilation(kenar,morphology.disk(1))&(gk|dag)&((lum<110)|reddish)&morphology.dilation(poly(PAGODA),morphology.disk(10))
    # torii ust kenarindaki beyaz cizgi (kama bolgesinde, Ev'e 4 px icinde) -> Ev
    kama=poly([(868,799),(962,766),(972,776),(880,808)])   # yalniz kasagi ust beyaz cizgisi seridi
    kenar|=kama&(gk|dag)&(lum>140)&morphology.dilation(ev,morphology.disk(7))&(yy>=yy*0+0)
    ev=ev|kenar; gk&=~kenar; dag&=~kenar; print('pagoda kenari kirmizi -> Ev px',int(kenar.sum()))
    fen=np.zeros((H,W),bool)
    for x0,y0,x1,y1 in LANTERNS: fen[y0:y1,x0:x1]=True
    out,moved=kucuk_parcalari_dagit({'gunes':gun,'dag':dag,'ev':ev,'gk':gk},koru=(fen&ev)|(BUDS&~gun))
    gun,dag,ev,gk=out['gunes'],out['dag'],out['ev'],out['gk']
    print('tasinan kucuk parca px',moved)
    np.savez_compressed(OUT,gunes=gun,dag=dag,ev=ev,gk=gk)
    for n,m in (('gunes',gun),('dag',dag),('ev',ev),('gk',gk)): print(n,m.sum(),round(100*m.mean(),2))
    print('toplam',int(gun.sum()+dag.sum()+ev.sum()+gk.sum()),H*W,'cakisma',int((gun&dag).sum()+(gun&ev).sum()+(dag&ev).sum()))
