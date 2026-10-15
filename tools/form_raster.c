/* Offline verification only: perspective-correct, two-triangle quad rasterizer.
 * Returns nearest quad + four interpolation weights. No game/runtime dependency.
 */
#include <math.h>
#include <stdint.h>
#include <stddef.h>

static double edge(double ax, double ay, double bx, double by, double x, double y) {
    return (bx-ax)*(y-ay)-(by-ay)*(x-ax);
}
void raster(const double *p, const uint8_t *active, int64_t n, int w, int h,
            double *depth, int64_t *ids, double *weights,
            const double *uv, const int32_t *materials, const int64_t *meta, const uint8_t *alpha) {
    const int tris[2][3] = {{0,1,2}, {0,2,3}};
    for (int64_t q=0; q<n; ++q) {
        if (!active[q]) continue;
        const double *v = p+q*12;
        for (int t=0; t<2; ++t) {
            int a=tris[t][0], b=tris[t][1], c=tris[t][2];
            double ax=v[a*3], ay=v[a*3+1], az=v[a*3+2];
            double bx=v[b*3], by=v[b*3+1], bz=v[b*3+2];
            double cx=v[c*3], cy=v[c*3+1], cz=v[c*3+2];
            double area=edge(ax,ay,bx,by,cx,cy);
            if (fabs(area)<1e-10) continue;
            double xmin=fmax(0, floor(fmin(ax,fmin(bx,cx))));
            double xmax=fmin(w-1, ceil(fmax(ax,fmax(bx,cx))));
            double ymin=fmax(0, floor(fmin(ay,fmin(by,cy))));
            double ymax=fmin(h-1, ceil(fmax(ay,fmax(by,cy))));
            if(xmin>xmax || ymin>ymax) continue;
            for(int y=(int)ymin; y<=(int)ymax; ++y) {
                for(int x=(int)xmin; x<=(int)xmax; ++x) {
                    double u=edge(bx,by,cx,cy,x+.5,y+.5)/area;
                    double v1=edge(cx,cy,ax,ay,x+.5,y+.5)/area;
                    double v2=1-u-v1;
                    if(u < -1e-9 || v1 < -1e-9 || v2 < -1e-9) continue;
                    double inv=u/az+v1/bz+v2/cz;
                    if(inv <= 0) continue;
                    double z=1/inv;
                    size_t k=(size_t)y*w+x;
                    if(z>=depth[k]) continue;
                    double wa=u/az*z, wb=v1/bz*z, wc=v2/cz*z;
                    const int64_t *tx=meta+materials[q]*3;
                    if(tx[0]>=0) {
                        const double *qt=uv+q*8;
                        double tu=qt[a*2]*wa+qt[b*2]*wb+qt[c*2]*wc;
                        double tv=qt[a*2+1]*wa+qt[b*2+1]*wb+qt[c*2+1]*wc;
                        int ix=(int)fmin(tx[1]-1,fmax(0,floor(tu*tx[1])));
                        int iy=(int)fmin(tx[2]-1,fmax(0,floor(tv*tx[2])));
                        if(alpha[tx[0]+(size_t)iy*tx[1]+ix]<128) continue;
                    }
                    depth[k]=z; ids[k]=q;
                    double *out=weights+k*4;
                    out[0]=out[1]=out[2]=out[3]=0;
                    out[a]=wa; out[b]=wb; out[c]=wc;
                }
            }
        }
    }
}
