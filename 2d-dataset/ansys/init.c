#include "udf.h"

DEFINE_INIT(init,d)
{
  cell_t c;
  Thread *t;
  real xc[ND_ND];
  real a = 6.283185307179586;

  /* loop over all cell threads in the domain  */
  thread_loop_c(t,d)
    {

      /* loop over all cells  */
      begin_c_loop_all(c,t)
        {
          C_CENTROID(xc,c,t);
          C_U(c, t) = cos(a * xc[0]) * sin(a * xc[1]);
          C_V(c, t) = -sin(a * xc[0]) * cos(a * xc[1]);
        }
      end_c_loop_all(c,t)
    }
}