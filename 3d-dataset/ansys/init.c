#include "udf.h"

DEFINE_INIT(init,d)
{
  cell_t c;
  Thread *t;
  real xc[ND_ND];

  /* loop over all cell threads in the domain  */
    thread_loop_c(t,d)
    {
        /* loop over all cells  */
        begin_c_loop_all(c,t)
        {
            C_CENTROID(xc,c,t);
            C_U(c, t) = -(exp(xc[0])*sin(xc[1]+xc[2])+exp(xc[2])*cos(xc[0]+xc[1]));
            C_V(c, t) = -(exp(xc[1])*sin(xc[0]+xc[2])+exp(xc[0])*cos(xc[2]+xc[1]));
            C_W(c, t) = -(exp(xc[2])*sin(xc[0]+xc[1])+exp(xc[1])*cos(xc[0]+xc[2]));
        }
        end_c_loop_all(c,t)
    }
}