#include "udf.h"

DEFINE_PROFILE(y_velocity, thread, nv)
{
    double x[3];
    face_t f;
    double scale = 1 - exp(-5 * CURRENT_TIME);
    begin_f_loop(f, thread)
    {
        F_CENTROID(x,f,thread);
        F_PROFILE(f, thread, nv)
            = 1.5*4*x[0]*(0.5-x[0])/(0.5*0.5)*scale;
    }
    end_f_loop(f, thread)
}