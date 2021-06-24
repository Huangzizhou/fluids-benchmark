#include "udf.h"

DEFINE_PROFILE(x_velocity,thread,nv)
{
    double x[3];
    double scale = sin(3.14159265358979323846264338 * CURRENT_TIME / 2);
    if (CURRENT_TIME >= 1)
        scale = 1;
    face_t f;
    begin_f_loop(f, thread)
    {
        F_CENTROID(x,f,thread);
        if (x[0] > 0.02 && x[0] < 1 - 0.02)
            F_PROFILE(f,thread,nv) = 50 * exp(1. / (x[0]*x[0] - x[0])) * x[1] * scale;
        else
            F_PROFILE(f,thread,nv) = 0;
    }
    end_f_loop(f, thread)
}