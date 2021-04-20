"""Numerical approximation methods"""

def interp(
    x: ulab.array,
    xp: ulab.array,
    fp: ulab.array,
    *,
    left: Optional[float] = None,
    right: Optional[float] = None
) -> ulab.array:
    """
    :param ulab.array x: The x-coordinates at which to evaluate the interpolated values.
    :param ulab.array xp: The x-coordinates of the data points, must be increasing
    :param ulab.array fp: The y-coordinates of the data points, same length as xp
    :param left: Value to return for ``x < xp[0]``, default is ``fp[0]``.
    :param right: Value to return for ``x > xp[-1]``, default is ``fp[-1]``.

    Returns the one-dimensional piecewise linear interpolant to a function with given discrete data points (xp, fp), evaluated at x."""
    ...

def trapz(y: ulab.array, x: Optional[ulab.array] = None, dx: float = 1.0) -> float:
    """
    :param 1D ulab.array y: the values of the dependent variable
    :param 1D ulab.array x: optional, the coordinates of the independent variable. Defaults to uniformly spaced values.
    :param float dx: the spacing between sample points, if x=None

    Returns the integral of y(x) using the trapezoidal rule.
    """
    ...

