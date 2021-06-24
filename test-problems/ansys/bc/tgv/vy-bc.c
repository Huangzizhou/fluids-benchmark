#include "udf.h"

DEFINE_PROFILE(y_velocity,thread,nv)
{
    double pos[3];
    double x, y;
    double T = 6.283185307179586;
    double visc = 1e-2;
    real t = CURRENT_TIME;
    double scale = exp(-2 * visc * T * T * t);
    face_t f;
    begin_f_loop(f, thread)
    {
        F_CENTROID(pos,f,thread);
        x = pos[0];
        y = pos[1];
        F_PROFILE(f,thread,nv) = -sin(T * x) * cos(T * y) * scale;
    }
    end_f_loop(f, thread)
}