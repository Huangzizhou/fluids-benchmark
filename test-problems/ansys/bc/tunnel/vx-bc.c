#include "udf.h"

DEFINE_PROFILE(x_velocity,thread,nv)
{
    double x[3];
    double y;
    double scale = 1 - exp(-5 * CURRENT_TIME);
    face_t f;
    begin_f_loop(f, thread)
    {
        F_CENTROID(x,f,thread);
        y = x[1];
        F_PROFILE(f,thread,nv) = scale*1.5*4*y*(0.41-y)/(0.41*0.41);
    }
    end_f_loop(f, thread)
}