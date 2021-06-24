#include "udf.h"

DEFINE_PROFILE(z_velocity, thread, nv)
{
    double pos[3];
    face_t f;
    double nu = 1e-2;
    begin_f_loop(f, thread)
    {
        F_CENTROID(pos,f,thread);
        F_PROFILE(f, thread, nv)
            = -(exp(pos[2])*sin(pos[0]+pos[1])+exp(pos[1])*cos(pos[0]+pos[2]))*exp(-CURRENT_TIME * nu);
    }
    end_f_loop(f, thread)
}