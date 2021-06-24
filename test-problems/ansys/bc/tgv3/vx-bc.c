#include "udf.h"

DEFINE_PROFILE(x_velocity, thread, nv)
{
    double pos[3];
    face_t f;
    double nu = 1e-2;
    begin_f_loop(f, thread)
    {
        F_CENTROID(pos,f,thread);
        F_PROFILE(f, thread, nv)
            = -(exp(pos[0])*sin(pos[1]+pos[2])+exp(pos[2])*cos(pos[0]+pos[1]))*exp(-CURRENT_TIME * nu);
    }
    end_f_loop(f, thread)
}