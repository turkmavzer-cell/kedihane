// Floyd-Steinberg (serpantin) hata yayilimi, dogrusal RGB, sabit palet. derle: gcc -O2 -shared -fPIC -o fs_dither.so fs_dither.c
#include <stdlib.h>
#include <math.h>
void fs_dither(float *img, int h, int w, const float *pal, int m, unsigned char *out, int gam) {
  for (int y = 0; y < h; y++) {
    int ltr = (y % 2 == 0);
    for (int k = 0; k < w; k++) {
      int x = ltr ? k : w - 1 - k;
      float *p = img + ((long)y * w + x) * 3;
      int best = 0; float bd = 1e30f;
      for (int i = 0; i < m; i++) {
        float d0, d1, d2;
        if (gam) { d0 = sqrtf(fmaxf(p[0],0))-sqrtf(pal[i*3]); d1 = sqrtf(fmaxf(p[1],0))-sqrtf(pal[i*3+1]); d2 = sqrtf(fmaxf(p[2],0))-sqrtf(pal[i*3+2]); }
        else { d0 = p[0]-pal[i*3]; d1 = p[1]-pal[i*3+1]; d2 = p[2]-pal[i*3+2]; }
        float d = d0*d0 + d1*d1 + d2*d2;
        if (d < bd) { bd = d; best = i; }
      }
      out[(long)y*w + x] = (unsigned char)best;
      float e[3] = { p[0]-pal[best*3], p[1]-pal[best*3+1], p[2]-pal[best*3+2] };
      int dx = ltr ? 1 : -1;
      for (int c = 0; c < 3; c++) {
        if (x+dx >= 0 && x+dx < w) img[((long)y*w + x+dx)*3 + c] += e[c]*0.4375f;
        if (y+1 < h) {
          if (x-dx >= 0 && x-dx < w) img[((long)(y+1)*w + x-dx)*3 + c] += e[c]*0.1875f;
          img[((long)(y+1)*w + x)*3 + c] += e[c]*0.3125f;
          if (x+dx >= 0 && x+dx < w) img[((long)(y+1)*w + x+dx)*3 + c] += e[c]*0.0625f;
        }
      }
    }
  }
}
