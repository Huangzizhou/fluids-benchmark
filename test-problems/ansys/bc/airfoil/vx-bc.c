#include "udf.h"

DEFINE_PROFILE(x_velocity,thread,nv)
{
    real t = CURRENT_TIME;
    double scale = 1 - exp(-5 * t);
    face_t f;
    begin_f_loop(f, thread)
    {
        F_PROFILE(f,thread,nv) = scale;
    }
    end_f_loop(f, thread)
}