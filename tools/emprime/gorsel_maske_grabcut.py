import cv2, numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
src=np.array(Image.open("src.png"))
S=1750/7000; f=1750/700
im=cv2.resize(src,(1750,2677),interpolation=cv2.INTER_AREA)
bgr=im[...,::-1].copy()
head=[(425,55),(500,65),(530,120),(545,200),(560,300),(575,380),(570,480),(520,520),(450,525),(375,520),(300,500),(190,505),(125,470),(95,430),(70,390),(65,345),(85,320),(150,270),(210,170),(250,110),(320,95),(380,100)]
dress=[(345,500),(405,500),(405,575),(455,590),(500,640),(520,700),(545,780),(560,860),(600,920),(640,970),(670,1071),(0,1071),(0,1010),(40,950),(95,890),(150,850),(215,800),(228,760),(245,680),(305,605),(345,560)]
def poly(p):
    m=np.zeros(im.shape[:2],np.uint8); cv2.fillPoly(m,[np.array([(x*f,y*f) for x,y in p],np.int32)],255); return m
P=cv2.bitwise_or(poly(head),poly(dress))
k=lambda r:cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*r+1,2*r+1))
mask=np.full(im.shape[:2],cv2.GC_BGD,np.uint8)
mask[cv2.dilate(P,k(40))>0]=cv2.GC_PR_BGD
mask[P>0]=cv2.GC_PR_FGD
mask[cv2.erode(P,k(35))>0]=cv2.GC_FGD
bg=np.zeros((1,65));fg=np.zeros((1,65))
cv2.grabCut(bgr,mask,None,bg,fg,6,cv2.GC_INIT_WITH_MASK)
m=((mask==cv2.GC_FGD)|(mask==cv2.GC_PR_FGD)).astype(np.uint8)*255
cv2.imwrite("mask_gc.png",m)
ov=im.copy(); ov[m==0]=(ov[m==0]*0.25+np.array([255,0,255])*0.75).astype(np.uint8)
Image.fromarray(ov).resize((700,1071)).save("ov.png")
