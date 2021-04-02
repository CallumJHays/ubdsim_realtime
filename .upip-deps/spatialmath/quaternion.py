"""
Classes to abstract quaternions and unit-quaternions.

To use::

    from spatialmath.quaternion import *
    T = UnitQuaternion.Rx(0.3)

    import spatialmath as sm
    T = sm.UnitQuaternion.Rx(0.3)

 .. inheritance-diagram:: spatialmath.quaternion
    :top-classes: collections.UserList
    :parts: 1
"""
# pylint: disable=invalid-name

import math
import numpy as np
from typing import Any, Type
from spatialmath import base
from spatialmath.pose3d import SO3, SE3
from spatialmath.baseposelist import BasePoseList

_eps = np.finfo(np.float64).eps

class Quaternion(BasePoseList):
    r"""
    Quaternion class

    A quaternion can be considered an ordered pair :math:`(s, \vec{v})`
    where :math:`s \in \mathbb{R}` is the *scalar* part and :math:`\vec{v} = (v_x, v_y, v_z) \in \mathbb{R}^3`
    is the *vector* part and is often written as

    .. math:: \q = s \langle v_x, v_y, v_z \rangle

    .. inheritance-diagram:: spatialmath.quaternion.Quaternion
       :top-classes: collections.UserList
       :parts: 1
    """

    def __init__(self, s: Any = None, v=None, check=True):
        r"""
        Construct a new quaternion

        :param s: scalar
        :type s: float
        :param v: vector
        :type v: 3-element array_like

        - ``Quaternion()`` constructs a zero quaternion
        - ``Quaternion(s, v)`` construct a new quaternion from the scalar ``s``
          and the vector ``v``
        - ``Quaternion(q)`` construct a new quaternion from the 4-vector
          ``q = [s, v]``
        - ``Quaternion([q1, q2 .. qN])`` construct a new quaternion with ``N``
          values where each element is a 4-vector
        - ``Quaternion([Q1, Q2 .. QN])`` construct a new quaternion with ``N``
          values where each element is a Quaternion instance
        - ``Quaternion(M)`` construct a new quaternion with ``N`` values where
          ``Q`` is a 4xN NumPy array.

        Example:

        .. runblock:: pycon

            >>> from spatialmath import Quaternion
            >>> Quaternion()
            >>> Quaternion(1, [2,3,4])
            >>> Quaternion([1,2,3,4])
            >>> q=Quaternion([np.r_[1,2,3,4], np.r_[5,6,7,8]])
            >>> len(q)
            >>> print(q)

        """
        super().__init__()

        if v is None:
            # single argument
            if super().arghandler(s, check=False):
                return

            elif base.isvector(s, 4):
                self.data = [base.getvector(s)]

        elif base.isscalar(s) and base.isvector(v, 3):
            # Quaternion(s, v)
            self.data = [np.r_[s, base.getvector(v)]]

        else:
            raise ValueError('bad argument to Quaternion constructor')


    @classmethod
    def Pure(cls, v):
        r"""
        Construct a pure quaternion from a vector

        :param v: vector
        :type v: 3-element array_like

        ``Quaternion.Pure(v)`` is a Quaternion with a zero scalar part and the
        vector part set to ``v``,
        ie. :math:`q = 0 \langle v_x, v_y, v_z \rangle`

        Example:

        .. runblock:: pycon

            >>> from spatialmath import Quaternion
            >>> print(Quaternion.Pure([1,2,3]))
        """
        return cls(s=0, v=base.getvector(v, 3))

    @staticmethod
    def _identity():
        return np.zeros((4,))

    @property
    def shape(self):
        """
        Shape of the object's interal matrix representation

        :return: (4,)
        :rtype: tuple
        """
        return (4,)

    @staticmethod
    def isvalid(x):
        """
        Test if vector is valid quaternion

        :param x: vector to test
        :type x: numpy.ndarray
        :arg check: explicitly check vector is unit length [default True]
        :type check: bool
        :return: True if the matrix has shape (4,).
        :rtype: bool

        Example:

        .. runblock:: pycon

            >>> from spatialmath import Quaternion
            >>> import numpy as np
            >>> Quaternion.isvalid(np.r_[1, 0, 0, 0])
            >>> Quaternion.isvalid(np.r_[1, 2, 3, 4])
        """
        return x.shape == (4,)

    @property
    def s(self):
        """
        Scalar part of quaternion

        :return: scalar part of quaternion
        :rtype: float or numpy.ndarray

        ``q.s`` is the scalar part.  If `len(q)` is:

            - 1, return a scalar float
            - N>1, return a NumPy array shape=(N,) is returned.

        Example:

        .. runblock:: pycon

            >>> from spatialmath import Quaternion
            >>> Quaternion([1,2,3,4]).s
            >>> Quaternion([np.r_[1,2,3,4], np.r_[5,6,7,8]]).s

        """
        if len(self) == 1:
            return self._A[0]
        else:
            return np.array([q.s for q in self])

    @property
    def v(self):
        """
        Vector part of quaternion

        :return: vector part of quaternion
        :rtype: NumPy ndarray

        ``q.v`` is the vector part.  If `len(q)` is:

            - 1, return a NumPy array shape=(3,)
            - N>1, return a NumPy array shape=(N,3).

        Example:

        .. runblock:: pycon

            >>> from spatialmath import Quaternion
            >>> Quaternion([1,2,3,4]).v
            >>> Quaternion([np.r_[1,2,3,4], np.r_[5,6,7,8]]).v

        """
        if len(self) == 1:
            return self._A[1:4]
        else:
            return np.array([q.v for q in self])

    @property
    def vec(self):
        """
        Quaternion as a vector

        :return: quaternion expressed as a 4-vector
        :rtype: numpy ndarray, shape=(4,)

        ``q.vec`` is the quaternion as a vector.  If `len(q)` is:

            - 1, return a NumPy array shape=(4,)
            - N>1, return a NumPy array shape=(N,4).

        Example:

        .. runblock:: pycon

            >>> from spatialmath import Quaternion
            >>> Quaternion([1,2,3,4]).vec
            >>> Quaternion([np.r_[1,2,3,4], np.r_[5,6,7,8]]).vec
        """
        if len(self) == 1:
            return self._A
        else:
            return np.array([q._A for q in self])

    @property
    def matrix(self):
        """
        Matrix equivalent of quaternion

        :rtype: Numpy array, shape=(4,4)

        ``q.matrix`` is a 4x4 matrix which encodes the arithmetic rules of Hamilton multiplication.
        This matrix, multiplied by the 4-vector equivalent of a second quaternion, results in the 4-vector
        equivalent of the Hamilton product.

        Example:

        .. runblock:: pycon

            >>> from spatialmath import Quaternion
            >>> Quaternion([1,2,3,4]).matrix
            >>> Quaternion([1,2,3,4]) * Quaternion([5,6,7,8])   # Hamilton product
            >>> Quaternion([1,2,3,4]).matrix @ Quaternion([5,6,7,8]).vec  # matrix-vector product

        :seealso: :func:`~spatialmath.base.quaternions.matrix`
        """

        return base.matrix(self._A)


    def conj(self):
        r"""
        Conjugate of quaternion

        :rtype: Quaternion instance

        ``q.conj()`` is the quaternion ``q`` with the vector part negated, ie.
        :math:`q = s \langle -v_x, -v_y, -v_z \rangle`

        Example:

        .. runblock:: pycon

            >>> from spatialmath import Quaternion
            >>> print(Quaternion.Pure([1,2,3]).conj())

        :seealso: :func:`~spatialmath.base.quaternions.conj`
        """

        return self.__class__([base.conj(q._A) for q in self])

    def norm(self):
        r"""
        Norm of quaternion

        :rtype: float

        ``q.norm()`` is the norm or length of the quaternion 
        :math:`\sqrt{s^2 + v_x^2 + v_y^2 + v_z^2}`


        Example:

        .. runblock:: pycon

            >>> from spatialmath import Quaternion
            >>> Quaternion([1,2,3,4]).norm()
            >>> Quaternion([np.r_[1,2,3,4], np.r_[5,6,7,8]]).norm()

        :seealso: :func:`~spatialmath.base.quaternions.qnorm`
        """
        if len(self) == 1:
            return base.qnorm(self._A)
        else:
            return np.array([base.qnorm(q._A) for q in self])

    def unit(self):
        r"""
        Unit quaternion

        :rtype: UnitQuaternion instance

        ``q.unit()`` is the quaternion ``q`` normalized to have a unit length.

        Example:

        .. runblock:: pycon

            >>> from spatialmath import Quaternion
            >>> q = Quaternion([1,2,3,4])
            >>> print(q)
            >>> print(q.unit())
            >>> print(Quaternion([np.r_[1,2,3,4], np.r_[5,6,7,8]]).unit())

        Note that the return type is different, a ``UnitQuaternion``, which is
        distinguished by the use of double angle brackets to delimit the 
        vector part.

        :seealso: :func:`~spatialmath.base.quaternions.qnorm`
        """
        return UnitQuaternion([base.unit(q._A) for q in self], norm=False)

    def log(self):
        r"""
        Logarithm of quaternion

        :rtype: Quaternion instance

        ``q.log()`` is the logarithm of the quaternion ``q``, ie.
        
        .. math::
        
             \ln \| q \|,  \langle \frac{\vec{v}}{\| \vec{v} \|} \cos^{-1} \frac{s}{\| q \|} \rangle

        For a ``UnitQuaternion`` the logarithm is a pure quaternion whose vector
        part :math:`\vec{v}` and :math:`\vec{v}/2` is a Euler vector: parallel
        to the axis of rotation and whose norm is the magnitude of rotation.

        Example:

        .. runblock:: pycon

            >>> from spatialmath import Quaternion, UnitQuaternion
            >>> from math import pi
            >>> q = Quaternion([1, 2, 3, 4])
            >>> print(q.log())
            >>> q = UnitQuaternion.Rx(pi / 2)
            >>> print(q.log())

        :reference: `Wikipedia <https://en.wikipedia.org/wiki/Quaternion#Exponential,_logarithm,_and_power_functions>`_

        :seealso: :func:`~spatialmath.quaternion.Quaternion.exp`, :func:`~spatialmath.quaternion.Quaternion.log`, :func:`~spatialmath.quaternion.UnitQuaternion.angvec`, 
        """
        norm = self.norm()
        s = math.log(norm)
        v = math.acos(self.s / norm) * base.unitvec(self.v)
        return Quaternion(s=s, v=v)

    def exp(self):
        r"""
        Exponential of quaternion

        :rtype: Quaternion instance

        ``q.exp()`` is the exponential of the quaternion ``q``, ie.
        
        .. math::
        
             e^s \cos \| v \|,  \langle e^s \frac{\vec{v}}{\| \vec{v} \|} \sin \| \vec{v} \| \rangle

        For a pure quaternion with vector value :math:`\vec{v}` the the result
        is a unit quaternion equivalent to a rotation defined by
        :math:`2\vec{v}` intepretted as an Euler vector, that is, parallel to
        the axis of rotation and whose norm is the magnitude of rotation.

        Example:

        .. runblock:: pycon

            >>> from spatialmath import Quaternion
            >>> from math import pi
            >>> q = Quaternion([1, 2, 3, 4])
            >>> print(q.exp())
            >>> q = Quaternion.Pure([pi / 4, 0, 0])
            >>> print(q.exp())  # result is a UnitQuaternion
            >>> print(q.exp().angvec())

        :reference: `Wikipedia <https://en.wikipedia.org/wiki/Quaternion#Exponential,_logarithm,_and_power_functions>`_

        :seealso: :func:`~spatialmath.quaternion.Quaternion.log`, :func:`~spatialmath.quaternion.UnitQuaternion.log`, :func:`~spatialmath.quaternion.UnitQuaternion.AngVec`, :func:`~spatialmath.quaternion.UnitQuaternion.EulerVec`
        """
        exp_s = math.exp(self.s)
        norm_v = base.norm(self.v)
        s = exp_s * math.cos(norm_v)
        v = exp_s * self.v / norm_v * math.sin(norm_v)
        if abs(self.s) < 100 * _eps:
            # result will be a unit quaternion
            return UnitQuaternion(s=s, v=v)
        else:
            return Quaternion(s=s, v=v)


    def inner(self, other):
        """
        Inner product of quaternions

        :rtype: float

        ``q1.inner(q2)`` is the dot product of the equivalent vectors, 
        ie. ``numpy.dot(q1.vec, q2.vec)``.
        The value of ``q.inner(q)`` is the same as ``q.norm ** 2``.

        Example:

        .. runblock:: pycon

            >>> from spatialmath import Quaternion
            >>> Quaternion([1,2,3,4]).inner(Quaternion([5,6,7,8]))
            >>> numpy.dot([1,2,3,4], [5,6,7,8])

        :seealso: :func:`~spatialmath.base.quaternions.inner`
        """

        assert isinstance(other, Quaternion), \
            'operands to inner must be Quaternion subclass'
        return self.binop(other, base.inner, list1=False)

    #-------------------------------------------- operators

    def __eq__(left, right): # lgtm[py/not-named-self] pylint: disable=no-self-argument
        """
        Overloaded ``==`` operator

        :return: Equality of two operands
        :rtype: bool or list of bool
        ``q1 == q2`` is True if ``q1` is elementwise equal to ``q2``.

        Example:

        .. runblock:: pycon

            >>> from spatialmath import Quaternion
            >>> q1 = Quaternion([1,2,3,4])
            >>> q2 = Quaternion([5,6,7,8])
            >>> q1 == q1
            >>> q1 == q2
            >>> Quaternion([np.r_[1,2,3,4], np.r_[5,6,7,8]]) == q1
            >>> Quaternion([np.r_[1,2,3,4], np.r_[5,6,7,8]]) == q2
            >>> Quaternion([np.r_[1,2,3,4], np.r_[5,6,7,8]]) == Quaternion([np.r_[1,2,3,4], np.r_[5,6,7,8]])

        :seealso: :func:`__ne__`, :func:`~spatialmath.base.quaternions.isequal`
        """
        assert isinstance(left, type(right)), \
            'operands to == are of different types'
        return left.binop(right, base.isequal, list1=False)

    def __ne__(left, right):  # lgtm[py/not-named-self] pylint: disable=no-self-argument
        """
        Overloaded ``!=`` operator

        :rtype: bool

        ``q1 != q2`` is True if ``q` is elementwise not equal to ``q2``.

        Example:

        .. runblock:: pycon

            >>> from spatialmath import Quaternion

            >>> q1 = Quaternion([1,2,3,4])
            >>> q2 = Quaternion([5,6,7,8])
            >>> q1 != q1
            False
            >>> q1 != q2
            True
            >>> Quaternion([np.r_[1,2,3,4], np.r_[5,6,7,8]]) != q1
            [False, True]
            >>> Quaternion([np.r_[1,2,3,4], np.r_[5,6,7,8]]) != q2
            [True, False]

        :seealso: :func:`__ne__`, :func:`~spatialmath.base.quaternions.isequal`
        """
        assert isinstance(left, type(right)), 'operands to == are of different types'
        return left.binop(right, lambda x, y: not base.isequal(x, y), list1=False)

    def __mul__(left, right):  # lgtm[py/not-named-self] pylint: disable=no-self-argument
        """
        Overloaded ``*`` operator

        :return: product
        :rtype: Quaternion
        :raises: ValueError

        - ``q1 * q2`` is the Hamilton product of two quaternions
        - ``q * s`` is the scalar product, where ``s`` is a scalar

        ==============   ==============   ==============  ================
                   Multiplicands                   Product
        -------------------------------   --------------------------------
            left             right            type           result
        ==============   ==============   ==============  ================
        Quaternion       Quaternion       Quaternion      Hamilton product
        Quaternion       UnitQuaternion   Quaternion      Hamilton product
        Quaternion       scalar           Quaternion      scalar product
        ==============   ==============   ==============  ================

        Any other input combinations result in a ValueError.

        Note that left and right can have a length greater than 1 in which case:

        ====   =====   ====  ================================
        left   right   len     operation
        ====   =====   ====  ================================
         1      1       1    ``prod = left * right``
         1      N       N    ``prod[i] = left * right[i]``
         N      1       N    ``prod[i] = left[i] * right``
         N      N       N    ``prod[i] = left[i] * right[i]``
         N      M       -    ``ValueError``
        ====   =====   ====  ================================

        Example:

        .. runblock:: pycon

            >>> from spatialmath import Quaternion

            >>> Quaternion([1,2,3,4]) * Quaternion([5,6,7,8])
            -60.000000 < 12.000000, 30.000000, 24.000000 >

            >>> Quaternion([1,2,3,4]) * 2
            2.000000 < 4.000000, 6.000000, 8.000000 >
            >>> Quaternion([np.r_[1,2,3,4], np.r_[5,6,7,8]]) * 2
            2.000000 < 4.000000, 6.000000, 8.000000 >
            10.000000 < 12.000000, 14.000000, 16.000000 >

            >>> Quaternion([np.r_[1,2,3,4], np.r_[5,6,7,8]]) * Quaternion([1,2,3,4])
            -28.000000 < 4.000000, 6.000000, 8.000000 >
            -60.000000 < 20.000000, 14.000000, 32.000000 >
            >>> Quaternion([1,2,3,4]) * Quaternion([np.r_[1,2,3,4], np.r_[5,6,7,8]])
            -28.000000 < 4.000000, 6.000000, 8.000000 >
            -60.000000 < 12.000000, 30.000000, 24.000000 >
            >>> Quaternion([np.r_[1,2,3,4], np.r_[5,6,7,8]]) * Quaternion([np.r_[1,2,3,4], np.r_[5,6,7,8]])
            -28.000000 < 4.000000, 6.000000, 8.000000 >
            -124.000000 < 60.000000, 70.000000, 80.000000 >

        :seealso: :func:`__rmul__`, :func:`__imul__`, :func:`~spatialmath.base.quaternions.qqmul`
        """
        if isinstance(right, left.__class__):
            # quaternion * [unit]quaternion case
            return Quaternion(left.binop(right, base.qqmul))

        elif base.isscalar(right):
            # quaternion * scalar case
            #print('scalar * quat')
            return Quaternion([right * q._A for q in left])

        else:
            raise ValueError('operands to * are of different types')

    def __rmul__(right, left):  # lgtm[py/not-named-self] pylint: disable=no-self-argument
        """
        Overloaded ``*`` operator

        :return: product
        :rtype: Quaternion
        :raises: ValueError

        ``s * q`` is the scalar product, where ``s`` is a scalar.

        Example:

        .. runblock:: pycon

            >>> from spatialmath import Quaternion
            >>> 2 * Quaternion([1,2,3,4])
            >>> 2 * Quaternion([np.r_[1,2,3,4], np.r_[5,6,7,8]])

        :seealso: :func:`__mul__`
        """
        # scalar * quaternion case
        return Quaternion([left * q._A for q in right])

    def __imul__(left, right):  # lgtm[py/not-named-self] pylint: disable=no-self-argument
        """
        Overloaded ``*=`` operator

        :return: product
        :rtype: Quaternion
        :raises: ValueError

        ``q1 *= q2`` sets ``q1 := q1 * q2``
        ``q1 *= s`` sets ``q1 := q1 * s`` where ``s`` is a scalar

        Example:

        .. runblock:: pycon

            >>> from spatialmath import Quaternion
            >>> q = Quaternion([1,2,3,4])
            >>> q *= Quaternion([5,6,7,8])
            >>> print(q)
            >>> q *= 2
            >>> print(q)

        :seealso: :func:`__mul__`
        """
        return left.__mul__(right)

    def __pow__(self, n):
        """
        Overloaded ``**`` operator

        :rtype: Quaternion instance

        ``q ** N`` computes the product of ``q`` with itself ``N-1`` times, where ``N`` must be
        an integer.  If ``N``<0 the result is conjugated.

        Example:

        .. runblock:: pycon

            >>> from spatialmath import Quaternion
            >>> print(Quaternion([1,2,3,4]) ** 2)
            >>> print(Quaternion([1,2,3,4]) ** -1)
            >>> print(Quaternion([np.r_[1,2,3,4], np.r_[5,6,7,8]]) ** 2)

        :seealso: :func:`spatialmath.base.quaternions.qpow`
        """
        return self.__class__([base.qpow(q._A, n) for q in self])

    def __ipow__(self, n):
        """
        Overloaded ``=**`` operator

        :rtype: Quaternion instance

        ``q **= N`` computes the product of ``q`` with itself ``N-1`` times, where ``N`` must be
        an integer.  If ``N``<0 the result is conjugated.

        Example:

        .. runblock:: pycon

            >>> from spatialmath import Quaternion

            >>> q = Quaternion([1,2,3,4])
            >>> q **= 2
            >>> q
            -28.000000 < 4.000000, 6.000000, 8.000000 >

            >>> q = Quaternion([np.r_[1,2,3,4], np.r_[5,6,7,8]])
            >>> q **= 2
            >>> q
            -28.000000 < 4.000000, 6.000000, 8.000000 >
            -124.000000 < 60.000000, 70.000000, 80.000000 >

        :seealso: :func:`__pow__`
        """

        return self.__pow__(n)

    def __truediv__(self, other):
        return NotImplemented  # Quaternion division not supported

    def __add__(left, right):  # lgtm[py/not-named-self] pylint: disable=no-self-argument
        """
        Overloaded ``+`` operator

        :return: sum
        :rtype: Quaternion, UnitQuaternion
        :raises: ValueError

        ==============   ==============   ==============  ===================
                   Operands                            Sum
        -------------------------------   -----------------------------------
            left             right            type           result
        ==============   ==============   ==============  ===================
        Quaternion       Quaternion       Quaternion      elementwise sum
        Quaternion       UnitQuaternion   Quaternion      elementwise sum
        Quaternion       scalar           Quaternion      add to each element
        UnitQuaternion   Quaternion       Quaternion      elementwise sum
        UnitQuaternion   UnitQuaternion   Quaternion      elementwise sum
        UnitQuaternion   scalar           Quaternion      add to each element
        ==============   ==============   ==============  ===================

        Any other input combinations result in a ValueError.

        Note that left and right can have a length greater than 1 in which case:

        ====   =====   ====  ================================
        left   right   len     operation
        ====   =====   ====  ================================
         1      1       1    ``sum = left + right``
         1      N       N    ``sum[i] = left + right[i]``
         N      1       N    ``sum[i] = left[i] + right``
         N      N       N    ``sum[i] = left[i] + right[i]``
         N      M       -    ``ValueError``
        ====   =====   ====  ================================

        A scalar of length N is a list, tuple or numpy array.
        A 3-vector of length N is a 3xN numpy array, where each column is a 3-vector.

        Example:

        .. runblock:: pycon

            >>> from spatialmath import Quaternion

            >>> Quaternion([1,2,3,4]) + Quaternion([5,6,7,8])
            6.000000 < 8.000000, 10.000000, 12.000000 >
            >>> Quaternion([np.r_[1,2,3,4], np.r_[5,6,7,8]]) + Quaternion([1,2,3,4])
            2.000000 < 4.000000, 6.000000, 8.000000 >
            6.000000 < 8.000000, 10.000000, 12.000000 >
            >>> Quaternion([np.r_[1,2,3,4], np.r_[5,6,7,8]]) + Quaternion([np.r_[1,2,3,4], np.r_[5,6,7,8]])
            2.000000 < 4.000000, 6.000000, 8.000000 >
            10.000000 < 12.000000, 14.000000, 16.000000 >
        """
        # results is not in the group, return an array, not a class
        assert isinstance(left, type(right)), 'operands to + are of different types'
        return Quaternion(left.binop(right, lambda x, y: x + y))

    def __sub__(left, right):  # lgtm[py/not-named-self] pylint: disable=no-self-argument
        """
        Overloaded ``-`` operator

        :return: difference
        :rtype: Quaternion, UnitQuaternion
        :raises: ValueError

        ==============   ==============   ==============  ==========================
                   Operands                          Difference
        -------------------------------   ------------------------------------------
            left             right            type           result
        ==============   ==============   ==============  ==========================
        Quaternion       Quaternion       Quaternion      elementwise sum
        Quaternion       UnitQuaternion   Quaternion      elementwise sum
        Quaternion       scalar           Quaternion      subtract from each element
        UnitQuaternion   Quaternion       Quaternion      elementwise sum
        UnitQuaternion   UnitQuaternion   Quaternion      elementwise sum
        UnitQuaternion   scalar           Quaternion      subtract from each element
        ==============   ==============   ==============  ==========================

        Any other input combinations result in a ValueError.

        Note that left and right can have a length greater than 1 in which case:

        ====   =====   ====  ================================
        left   right   len     operation
        ====   =====   ====  ================================
         1      1       1    ``diff = left - right``
         1      N       N    ``diff[i] = left - right[i]``
         N      1       N    ``diff[i] = left[i] - right``
         N      N       N    ``diff[i] = left[i] - right[i]``
         N      M       -    ``ValueError``
        ====   =====   ====  ================================

        A scalar of length N is a list, tuple or numpy array.
        A 3-vector of length N is a 3xN numpy array, where each column is a 3-vector.

        Example:

        .. runblock:: pycon

            >>> from spatialmath import Quaternion

            >>> Quaternion([1,2,3,4]) - Quaternion([5,6,7,8])
            -4.000000 < -4.000000, -4.000000, -4.000000 >

            >>> Quaternion([np.r_[1,2,3,4], np.r_[5,6,7,8]]) - Quaternion([1,2,3,4])
            0.000000 < 0.000000, 0.000000, 0.000000 >
            4.000000 < 4.000000, 4.000000, 4.000000 >

            >>> Quaternion([np.r_[1,2,3,4], np.r_[5,6,7,8]]) - Quaternion([np.r_[1,2,3,4], np.r_[5,6,7,8]])
            0.000000 < 0.000000, 0.000000, 0.000000 >
            0.000000 < 0.000000, 0.000000, 0.000000 >

        """
        # results is not in the group, return an array, not a class
        # TODO allow class +/- a conformant array
        assert isinstance(left, type(right)), 'operands to - are of different types'
        return Quaternion(left.binop(right, lambda x, y: x - y))

    def __neg__(self):
        r"""
        Overloaded unary ``-`` operator

        :rtype: Quaternion or UnitQuaternion

        ``-q`` is a quaternion with all its components negated.

        Example:

        .. runblock:: pycon

            >>> from spatialmath import Quaternion

            >>> -Quaternion([1,2,3,4])
            -0.182574 << -0.365148, -0.547723, -0.730297 >>

            >>> -Quaternion([np.r_[1,2,3,4], np.r_[5,6,7,8]])
            -0.182574 << -0.365148, -0.547723, -0.730297 >>
            -0.379049 << -0.454859, -0.530669, -0.606478 >>
        """

        return UnitQuaternion([-x for x in self.data])  # pylint: disable=invalid-unary-operand-type

    def __repr__(self):
        """
        Readable representation of pose (superclass method)

        :return: readable representation of the pose as a list of arrays
        :rtype: str

        Example:

        .. runblock:: pycon

            >>> from spatialmath import Quaternion

            >>> q = Quaternion([1,2,3,4])
            >>> q
            Quaternion(array([[ 1.        ,  0.        ,  0.        ,  0.        ],
                       [ 0.        ,  0.95533649, -0.29552021,  0.        ],
                       [ 0.        ,  0.29552021,  0.95533649,  0.        ],
                       [ 0.        ,  0.        ,  0.        ,  1.        ]]))

        """
        name = type(self).__name__
        if len(self) == 0:
            return name + '([])'
        elif len(self) == 1:
            # need to indent subsequent lines of the native repr string by 4 spaces
            return name + '(' + self._A.__repr__() + ')'
        else:
            # format this as a list of ndarrays
            return name + '([\n  ' + ',\n  '.join([v.__repr__() for v in self.data]) + ' ])'

    def _repr_pretty_(self, p, cycle):
        """
        Pretty string for IPython (superclass method)

        :param p: pretty printer handle (ignored)
        :param cycle: pretty printer flag (ignored)

        Print colorized output when variable is displayed in IPython, ie. on a line by
        itself.

        Example::

            In [1]: x

        """
        print(self.__str__())

    def __str__(self):
        """
        Pretty string representation of quaternion

        :return: readable representation of quaternion
        :rtype: str

        Format the quaternion elements into a single line format.  For example::

        Example:

        .. runblock:: pycon

            >>> from spatialmath import Quaternion
            >>> q = Quaternion([1,2,3,4])
            >>> print(x)
            1.000000 < 2.000000, 3.000000, 4.000000 >
            >> q = UnitQuaternion.Rx(0.3)
            0.988771 << 0.149438, 0.000000, 0.000000 >>

            Note that unit quaternions are denoted by different delimiters for
            the vector part.

                    :seealso: :func:`~spatialmath.base.quaternions.qnorm`
        """
        if isinstance(self, UnitQuaternion):
            delim = ('<<', '>>')
        else:
            delim = ('<', '>')
        return '\n'.join([base.qprint(q, file=None, delim=delim) for q in self.data])

# ========================================================================= #

class UnitQuaternion(Quaternion):
    r"""
    Unit quaternion class

    A unit quaternion can be considered an ordered pair :math:`(s, \vec{v})`
    where :math:`s \in \mathbb{R}` is the *scalar* part and :math:`\vec{v} = (v_x, v_y, v_z) \in \mathbb{R}^3`
    is the *vector* part and is often written as

    .. math:: \q = s \langle v_x, v_y, v_z \rangle

    and subject to a unit-length constraint :math:`s^2+v_x^2+v_y^2+v_z^2 = 1`.

    A unit-quaternion can be considered as a rotation :math:`\theta` about the
    vector :math:`\vec{v}`, so the unit quaternion can also be
    written as 
    
    .. math:: \q = \cos \frac{\theta}{2} \sin \frac{\theta}{2} <v_x v_y v_z>

    The quaternion :math:`\q` and :math:`-\q` represent the equivalent rotation, and this is referred to
    as a double mapping.

    .. inheritance-diagram:: spatialmath.quaternion.UnitQuaternion
        :top-classes: collections.UserList
        :parts: 1

    The ``UnitQuaternion`` class inherits many methods from the ``Quaternion`` class

    """

    def __init__(self, s: Any = None, v=None, norm=True, check=True):
        """
        Construct a UnitQuaternion instance

        :arg norm: explicitly normalize the quaternion [default True]
        :type norm: bool
        :arg check: explicitly check validity of argument [default True]
        :type check: bool
        :return: unit-quaternion
        :rtype: UnitQuaternion instance
        :raises: ValueError

        - ``UnitQuaternion()`` constructs the identity quaternion 1<0,0,0>
        - ``UnitQuaternion(s, v)`` constructs a unit quaternion with specified
          real ``s`` and ``v`` vector parts. ``v`` is a 3-vector given as a
          list, tuple, or ndarray(3). If ``norm`` is True the resulting 
          quaternion is normalized.
        - ``UnitQuaternion(v)`` constructs a unit quaternion with specified
          elements from ``v`` which is a 4-vector given as a list, tuple, or ndarray(4). Also known
          as the Euler parameters.
        - ``UnitQuaternion(M)`` construct a new unit quaternion with ``N`` values where ``Q`` is a Nx4 NumPy array
          whose rows are the quaternion in vector form
        - ``UnitQuaternion(R)`` constructs a unit quaternion from an SO(3)
          rotation matrix given as a ndarray(3,3). If ``check`` is True
          test the rotation submatrix for orthogonality.
        - ``UnitQuaternion(X)`` constructs a unit quaternion from the rotational
          part of ``X`` which is an SO3 or SE3 instance.  If len(X) > 1 then
          the resulting unit quaternion is of the same length.
        - ``UnitQuaternion([q1, q2 .. qN])`` construct a new unit quaternion with ``N`` values where each element is a 4-vector
        - ``UnitQuaternion([Q1, Q2 .. QN])`` construct a new unit quaternion with ``N`` values where each element is a UnitQuaternion instance
        - ``UnitQuaternion([X1, X2 .. XN])`` construct a new unit quaternion with ``N`` values where each element is an SO3 or SE3 instance

        Example:

        .. runblock:: pycon

            >>> from spatialmath import UnitQuaternion as UQ
            >>> q = UQ()
            >>> q         # repr()
            >>> print(q)  # str()

        """
        super().__init__()

        if v is None:
            # single argument
            if super().arghandler(s, check=check):
                # create unit quaternion
                self.data = [base.unit(q) for q in self.data]

            elif isinstance(s, np.ndarray):
                # passed a NumPy array, it could be:
                #  an SO(3) or SE(3) matrix
                #  a quaternion as a 1D array
                #  an array of quaternions as an nx4 array

                if base.isrot(s, check=check):
                    # UnitQuaternion(R) R is 3x3 rotation matrix
                    self.data = [base.r2q(s)]
                elif s.shape == (4,):
                    # passed a 4-vector
                    if norm:
                        self.data = [base.unit(s)]
                    else:
                        self.data = [s]
                elif s.ndim == 2 and s.shape[1] == 4:
                    if norm:
                        self.data = [base.unit(x) for x in s]
                    else:
                        # self.data = [base.qpositive(x) for x in s]
                        self.data = [x for x in s]

            elif isinstance(s, SO3):
                # UnitQuaternion(x) x is SO3 or SE3 (since SE3 is subclass of SO3)
                self.data = [base.r2q(x.R) for x in s]

            elif isinstance(s[0], SO3):
                # list of SO3 or SE3
                self.data = [base.r2q(x.R) for x in s]

            else:
                raise ValueError('bad argument to UnitQuaternion constructor')

        elif base.isscalar(s) and base.isvector(v, 3):
            # UnitQuaternion(s, v)   s is scalar, v is 3-vector
            q = np.r_[s, base.getvector(v)]
            if norm:
                q = base.unit(q)
            self.data = [q]
        
        else:
            raise ValueError('bad argument to UnitQuaternion constructor')


    @staticmethod
    def _identity():
        return base.eye()

    @staticmethod
    def isvalid(x, check=True):
        """
        Test if vector is valid unit quaternion

        :param x: vector to test
        :type x: numpy.ndarray
        :arg check: explicitly check vector is unit length [default True]
        :type check: bool
        :return: True if the matrix has shape (4,).
        :rtype: bool

        Example:

        .. runblock:: pycon

            >>> from spatialmath import UnitQuaternion 
            >>> import numpy as np
            >>> UnitQuaternion.isvalid(np.r_[1, 0, 0, 0])
            >>> UnitQuaternion.isvalid(np.r_[1, 2, 3, 4])
        """
        return x.shape == (4,) and (not check or base.isunitvec(x))

    @property
    def R(self):
        """
        Unit quaternion as a rotation matrix

        :return: equivalent rotational matrix
        :rtype: ndarray(3,3)

        ``q.R`` returns the rotation matrix which describes the equivalent rotation. If ``len(x)`` is:

            - 1, return an ndarray with shape=(3,3)
            - N>1, return ndarray with shape=(N,3,3)

        Example:

        .. runblock:: pycon

            >>> from spatialmath import UnitQuaternion as UQ
            >>> q = UQ.Rx(0.3)
            >>> q.R
            >>> q = UQ.Rx([0.3, 0.4])
            >>> q.R
            
        .. warning:: The i'th rotation matrix is ``x[i,:,:]`` or simply 
            ``x[i]``. This is different to the MATLAB version where the i'th
            rotation matrix is ``x(:,:,i)``.        
        """
        if len(self) > 1:
            return np.array([base.q2r(q) for q in self.data])
        else:
            return base.q2r(self._A)

    @property
    def vec3(self):
        r"""
        Unit quaternion unique vector part

        :return: vector part of unit quaternion
        :rtype: numpy array, shape=(3,)

        ``q.vec3`` is the vector part of a unit quaternion.  If ``q`` has a negative scalar
        part we take the vector part of ``-q``, since  ``q`` and ``-q`` represent the
        same rotation.

        This vector part is a minimal unique representation of the unit quaternion and can be used in
        optimization procedures such as bundle adjustment.

        Example:

        .. runblock:: pycon

            >>> from spatialmath import UnitQuaternion as UQ
            >>> q = UQ.Rz(-4)
            >>> print(q)
            >>> q.vec3
            >>> q2 = UQ.Vec3(q.vec3)
            >>> print(q2)
            >>> q == q2

        :seealso: :func:`~spatialmath.quaternion.UnitQuaternion.Vec3`
        """
        return base.q2v(self._A)

    # -------------------------------------------- constructor variants
    @classmethod
    def Rx(cls, angle, unit='rad'):
        """
        Construct a UnitQuaternion object representing rotation about the X-axis

        :arg θ: rotation angle
        :type θ: float or array_like
        :arg unit: rotation unit 'rad' [default] or 'deg'
        :type unit: str
        :return: unit-quaternion
        :rtype: UnitQuaternion instance

        - ``UnitQuaternion(θ)`` constructs a unit quaternion representing a
          rotation of ``θ`` radians about the X-axis.
        - ``UnitQuaternion(θ, 'deg')`` constructs a unit quaternion representing a
          rotation of ``θ`` degrees about the X-axis.

        Example:

        .. runblock:: pycon
        
            >>> from spatialmath import UnitQuaternion as UQ
            >>> print(UQ.Rx(0.3))
            >>> print(UQ.Rx([0, 0.3, 0.6]))
        """
        angles = base.getunit(base.getvector(angle), unit)
        return cls([np.r_[math.cos(a / 2), math.sin(a / 2), 0, 0] for a in angles], check=False)

    @classmethod
    def Ry(cls, angle, unit='rad'):
        """
        Construct a UnitQuaternion object representing rotation about the Y-axis

        :arg θ: rotation angle
        :type θ: float or array_like
        :arg unit: rotation unit 'rad' [default] or 'deg'
        :type unit: str
        :return: unit-quaternion
        :rtype: UnitQuaternion instance

        - ``UnitQuaternion(θ)`` constructs a unit quaternion representing a
          rotation of ``θ`` radians about the Y-axis.
        - ``UnitQuaternion(θ, 'deg')`` constructs a unit quaternion representing a
          rotation of ``θ`` degrees about the Y-axis.

        Example:

        .. runblock:: pycon
        
            >>> from spatialmath import UnitQuaternion as UQ
            >>> print(UQ.Ry(0.3))
            >>> print(UQ.Ry([0, 0.3, 0.6]))
        """
        angles = base.getunit(base.getvector(angle), unit)
        return cls([np.r_[math.cos(a / 2), 0, math.sin(a / 2), 0] for a in angles], check=False)

    @classmethod
    def Rz(cls, angle, unit='rad'):
        """
        Construct a UnitQuaternion object representing rotation about the Z-axis

        :arg θ: rotation angle
        :type θ: float or array_like
        :arg unit: rotation unit 'rad' [default] or 'deg'
        :type unit: str
        :return: unit-quaternion
        :rtype: UnitQuaternion instance

        - ``UnitQuaternion(θ)`` constructs a unit quaternion representing a
          rotation of ``θ`` radians about the Z-axis.
        - ``UnitQuaternion(θ, 'deg')`` constructs a unit quaternion representing a
          rotation of ``θ`` degrees about the Z-axis.

        Example:

        .. runblock:: pycon
        
            >>> from spatialmath import UnitQuaternion as UQ
            >>> print(UQ.Rz(0.3))
            >>> print(UQ.Rz([0, 0.3, 0.6]))
        """
        angles = base.getunit(base.getvector(angle), unit)
        return cls([np.r_[math.cos(a / 2), 0, 0, math.sin(a / 2)] for a in angles], check=False)

    @classmethod
    def Rand(cls, N=1):
        """
        Construct a new random unit quaternion

        :param N: number of random rotations
        :type N: int
        :return: random unit-quaternion
        :rtype: UnitQuaternion instance

        - ``UnitQuaternion.Rand()`` is a uniformly distributed random unit quaternion value.
        - ``SO3.Rand(N)`` is a unit quaternion instance containing a sequence of N random unit quaternion
          values.

        Example:

        .. runblock:: pycon
        
            >>> from spatialmath import UnitQuaternion as UQ
            >>> print(UQ.Rand())
            >>> print(UQ.Rand(3))

        :seealso: :func:`~spatialmath.quaternion.UnitQuaternion.Rand`
        """
        return cls([base.rand() for i in range(0, N)], check=False)

    @classmethod
    def Eul(cls, *angles, unit='rad'):
        r"""
        Construct a new unit quaternion from Euler angles

        :param 𝚪: 3-vector of Euler angles
        :type 𝚪: array_like
        :param unit: angular units: 'rad' [default], or 'deg'
        :type unit: str
        :return: unit-quaternion
        :rtype: UnitQuaternion instance

        - ``UnitQuaternion.Eul(𝚪)`` is a unit quaternion that describes the 3D
          rotation defined by a 3-vector of Euler angles :math:`\Gamma = (\phi,
          \theta, \psi)` which correspond to consecutive rotations about the Z,
          Y, Z axes respectively.

        - ``UnitQuaternion.Eul(φ, θ, ψ)`` as above but the angles are provided
          as three scalars.

        Example:

        .. runblock:: pycon
        
            >>> from spatialmath import UnitQuaternion as UQ
            >>> print(UQ.Eul([0.1, 0.2, 0.3]))

        :seealso: :func:`~spatialmath.quaternion.UnitQuaternion.RPY`, :func:`~spatialmath.pose3d.SE3.eul`, :func:`~spatialmath.pose3d.SE3.Eul`, :func:`~spatialmath.base.transforms3d.eul2r`
        """
        if len(angles) == 1:
            angles = angles[0]

        return cls(base.r2q(base.eul2r(angles, unit=unit)), check=False)

    @classmethod
    def RPY(cls, *angles, order='zyx', unit='rad'):
        """
        Construct a new unit quaternion from roll-pitch-yaw angles

        :param 𝚪: 3-vector of roll-pitch-yaw angles
        :type 𝚪: array_like
        :param unit: angular units: 'rad' [default], or 'deg'
        :type unit: str
        :param unit: rotation order: 'zyx' [default], 'xyz', or 'yxz'
        :type unit: str
        :return: unit-quaternion
        :rtype: UnitQuaternion instance

        - ``UnitQuaternion.RPY(𝚪)`` is a unit quaternion that describes the 3D
          rotation defined by a  3-vector of roll, pitch, yaw angles
          :math:`\Gamma = (r, p, y)` which correspond to successive rotations
          about the axes specified by ``order``:

            - ``'zyx'`` [default], rotate by yaw about the z-axis, then by pitch
              about the new y-axis, then by roll about the new x-axis.
              Convention for a mobile robot with x-axis forward and y-axis
              sideways.
            - ``'xyz'``, rotate by yaw about the x-axis, then by pitch about the
              new y-axis, then by roll about the new z-axis. Convention for a
              robot gripper with z-axis forward and y-axis between the gripper
              fingers.
            - ``'yxz'``, rotate by yaw about the y-axis, then by pitch about the
              new x-axis, then by roll about the new z-axis. Convention for a
              camera with z-axis parallel to the optic axis and x-axis parallel
              to the pixel rows.


        - ``UnitQuaternion.RPY(⍺, β, 𝛾)`` as above but the angles are provided
          as three scalars.

        Example:

        .. runblock:: pycon
        
            >>> from spatialmath import UnitQuaternion as UQ
            >>> print(UQ.RPY([0.1, 0.2, 0.3]))

        :seealso: :func:`~spatialmath.quaternion.UnitQuaternion.Eul`, :func:`~spatialmath.pose3d.SE3.rpy`, :func:`~spatialmath.pose3d.SE3.RPY`, :func:`~spatialmath.base.transforms3d.rpy2r`
        """
        if len(angles) == 1:
            angles = angles[0]

        return cls(base.r2q(base.rpy2r(angles, unit=unit, order=order)), check=False)

    @classmethod
    def OA(cls, o, a):
        """
        Construct a new unit quaternion from two vectors

        :param o: 3-vector parallel to Y- axis
        :type o: array_like
        :param a: 3-vector parallel to the Z-axis
        :type a: array_like
        :return: unit-quaternion
        :rtype: UnitQuaternion instance

        ``UnitQuaternion.OA(O, A)`` is a unit quaternion that describes the 3D rotation defined in terms of
        vectors parallel to the Y- and Z-axes of its reference frame.  In robotics these axes are
        respectively called the orientation and approach vectors defined such that
        R = [N O A] and N = O x A.

        Example:

        .. runblock:: pycon
        
            >>> from spatialmath import UnitQuaternion as UQ
            >>> print(UQ.OA([0,0,-1], [0,1,0]))

        .. notes::

            - Only the ``A`` vector is guaranteed to have the same direction in the resulting
            rotation matrix
            - ``O`` and ``A`` do not have to be unit-length, they are normalized
            - ``O`` and ``A` do not have to be orthogonal, so long as they are not parallel

        :seealso: :func:`~spatialmath.base.transforms3d.oa2r`
        """
        return cls(base.r2q(base.oa2r(o, a)), check=False)

    @classmethod
    def AngVec(cls, theta, v, *, unit='rad'):
        r"""
        Construct a new unit quaternion from rotation angle and axis

        :param theta: rotation
        :type theta: float
        :param unit: angular units: 'rad' [default], or 'deg'
        :type unit: str
        :param v: rotation axis, 3-vector
        :type v: array_like
        :return: unit-quaternion
        :rtype: UnitQuaternion instance

        ``UnitQuaternion.AngVec(θ, v)`` is a unit quaternion that describes the 3D rotation
        defined by a rotation of ``θ`` about the 3-vector ``v``.

        Example:

        .. runblock:: pycon
        
            >>> from spatialmath import UnitQuaternion as UQ
            >>> print(UQ.AngVec(0, [1,0,0]))
            >>> print(UQ.AngVec(90, [1,0,0], unit='deg'))

        .. note:: :math:`\theta = 0` the result in an identity quaternion, otherwise
            ``V`` must have a finite length, ie. :math:`|V| > 0`.

        :seealso: :func:`~spatialmath.UnitQuaternion.angvec`, :func:`~spatialmath.quaternion.UnitQuaternion.exp`, :func:`~spatialmath.base.transforms3d.angvec2r`
        """
        v = base.getvector(v, 3)
        base.isscalar(theta)
        theta = base.getunit(theta, unit)
        return cls(s=math.cos(theta / 2), v=math.sin(theta / 2) * v, norm=False, check=False)

    @classmethod
    def EulerVec(cls, w):
        r"""
        Construct a new unit quaternion from an Euler rotation vector

        :param ω: rotation axis
        :type ω: 3-element array_like
        :return: unit-quaternion
        :rtype: UnitQuaternion instance

        ``UnitQuaternion.EulerVec(ω)`` is a unit quaternion that describes the 3D rotation
        defined by a rotation of :math:`\theta = \lVert \omega \rVert` about the
        unit 3-vector :math:`\omega / \lVert \omega \rVert`.

        Example:

        .. runblock:: pycon
        
            >>> from spatialmath import UnitQuaternion as UQ
            >>> print(UQ.EulerVec([0.5,0,0]))

        .. note:: :math:`\theta \eq 0` the result in an identity matrix, otherwise
            ``V`` must have a finite length, ie. :math:`|V| > 0`.

        :seealso: :func:`~spatialmath.pose3d.SE3.angvec`, :func:`~spatialmath.base.transforms3d.angvec2r`
        """
        assert base.isvector(w, 3), 'w must be a 3-vector'
        w = base.getvector(w)
        theta = base.norm(w)
        s = math.cos(theta / 2)
        v = math.sin(theta / 2) * base.unitvec(w)
        return cls(s=s, v=v, check=False)

    @classmethod
    def Vec3(cls, vec):
        r"""
        Construct a new unit quaternion from its vector part

        :param vec: vector part of unit quaternion
        :type vec: 3-element array_like

        ``UnitQuaternion.Vec(v)`` is a new unit quaternion with the specified vector part
        and the scalar part is
        
        .. math:: s = \sqrt{1 - v_x^2 - v_y^2 - v_z^2}
        
        The unit quaternion will always have a positive scalar part.

        Example:

        .. runblock:: pycon
        
            >>> from spatialmath import UnitQuaternion as UQ
            >>> q = UQ.Rz(-4)
            >>> print(q)
            >>> q.vec3
            >>> q2 = UQ.Vec3(q.vec3)
            >>> print(q2)
            >>> q == q2

        :seealso: :func:`~spatialmath.quaternion.UnitQuaternion.vec3`
        """
        return cls(base.v2q(vec))

    def inv(self):
        """
        Inverse of unit quaternion

        :return: unit-quaternion
        :rtype: UnitQuaternion instance

        ``q.inv()`` is the inverse of the unit-quaternion.  This is a group operation
        and the product of the unit-quaternion and its inverse is the identity quaternion.

        Example:

        .. runblock:: pycon
        
            >>> from spatialmath import UnitQuaternio
            >>> print(UQ.Rx(0.3).inv())
            >>> print(UQ.Rx(0.3).inv() * UQ.Rx(0.3))
            >>> print(UQ.Rx([0.3, 0.6]).inv())

        """
        return UnitQuaternion([base.conj(q._A) for q in self])

    @staticmethod
    def qvmul(qv1, qv2):
        """
        Multiply unit quaternions defined by unique vector parts

        :param qv1: vector representation of first multiplicand
        :type qv1: ndarray(3)
        :param qv1: vector representation of second multiplicand
        :type qv1: ndarray(3)

        ``UnitQuaternion(qv1, qv2)`` is the Hamilton product of two unit quaternions
        represented in minimal vector form.

        Example:

        .. runblock:: pycon
        
            >>> from spatialmath import UnitQuaternion as UQ
            >>> q1 = UQ.Rx(0.3)
            >>> q2 = UQ.Ry(-0.3)
            >>> qv1 = q1.vec3
            >>> qv1
            >>> qv2 = q2.vec3
            >>> qv = UQ.qvmul(qv1, qv2)
            >>> qv
            >>> print(UQ.Vec3(qv))
            >>> print(UQ.Rx(0.3) * UQ.Ry(-0.3))

        :seealso: :func:`~spatialmath.quaternion.UnitQuaternion.vec3`, :func:`~spatialmath.quaternion.UnitQuaternion.Vec3`
        """
        return base.vvmul(qv1, qv2)

    def dot(self, omega):
        """
        Rate of change of a unit quaternion in world frame

        :param ω: angular velocity in world frame
        :type ω: 3-element array_like
        :return: rate of change of unit quaternion
        :rtype: ndarray(4)

        ``q.dot(ω)`` is the rate of change of the elements of the unit quaternion ``q``
        which represents the orientation of a body frame with angular velocity ``ω`` in
        the world frame.
        """
        return base.dot(self._A, omega)

    def dotb(self, omega):
        """
        Rate of change of a unit quaternion in body frame

        :param ω: angular velocity in body frame
        :type ω: 3-element array_like
        :return: rate of change of unit quaternion
        :rtype: ndarray(4)

        ``q.dotb(ω)`` is the rate of change of the elements of the unit quaternion ``q``
        which represents the orientation of a body frame with angular velocity ``ω`` in
        the body frame.
        """
        return base.dotb(self._A, omega)

    def __mul__(left, right):  # lgtm[py/not-named-self] pylint: disable=no-self-argument
        """
        Multiply unit quaternion

        :return: product
        :rtype: Quaternion, UnitQuaternion
        :raises: ValueError

        ==============   ==============   ==============  ================
                   Multiplicands                   Product
        -------------------------------   --------------------------------
            left             right            type           result
        ==============   ==============   ==============  ================
        UnitQuaternion   Quaternion       Quaternion      Hamilton product
        UnitQuaternion   UnitQuaternion   UnitQuaternion  Hamilton product
        UnitQuaternion   scalar           Quaternion      scalar product
        UnitQuaternion   3-vector         3-vector        vector rotation
        UnitQuaternion   3xN array        3xN array       vector rotations
        ==============   ==============   ==============  ================

        Any other input combinations result in a ValueError.

        Example:

        .. runblock:: pycon

            >>> from spatialmath import UnitQuaternion as UQ
            >>> print(UQ.Rx(0.3) * UQ.Rx(0.4))
            >>> print(UQ.Rx(0.3) * 2)
            >>> print(UQ.Rx(0.3) * [1, 2, 3])

        Note that left and right can have a length greater than 1 in which case:

        ====   =====   ====  ================================
        left   right   len     operation
        ====   =====   ====  ================================
         1      1       1    ``prod = left * right``
         1      N       N    ``prod[i] = left * right[i]``
         N      1       N    ``prod[i] = left[i] * right``
         N      N       N    ``prod[i] = left[i] * right[i]``
         N      M       n/a    ``ValueError``
        ====   =====   ====  ================================

        A scalar of length N is a list, tuple or numpy array.
        A 3-vector of length N is a 3xN numpy array, where each column is 
        a 3-vector.

        Example:

        .. runblock:: pycon
        
            >>> from spatialmath import UnitQuaternion as UQ
            >>> print(UQ.Rx(0.3) * UQ.Rx(0.4))
            >>> q = UQ.Rx(0.3)
            >>> q *= UQ.Rx(0.4))
            >>> print(q)
            >>> print(UQ.Rx(0.3) * UQ.Rx([0.4, 0.6])
            >>> print(UQ.Rx([0.3, 0.6]) * UQ.Rx(0.3))
            >>> print(UQ.Rx([0.3, 0.6]) * UQ.Rx([0.3, 0.6]))

        :seealso: :func:`~spatialmath.Quaternion.__mul__`
        """
        if isinstance(left, right.__class__):
            # quaternion * quaternion case (same class)
            return right.__class__(left.binop(right, base.qqmul))

        elif base.isscalar(right):
            # quaternion * scalar case
            #print('scalar * quat')
            return Quaternion([right * q._A for q in left])

        elif isinstance(right, (list, tuple, np.ndarray)):
            # unit quaternion * vector
            #print('*: pose x array')
            if base.isvector(right, 3):
                v = base.getvector(right)
                if len(left) == 1:
                    # pose x vector
                    #print('*: pose x vector')
                    return base.qvmul(left._A, base.getvector(right, 3))

                elif len(left) > 1 and base.isvector(right, 3):
                    # pose array x vector
                    #print('*: pose array x vector')
                    return np.array([base.qvmul(x, v) for x in left._A]).T

            elif len(left) == 1 and isinstance(right, np.ndarray) and right.shape[0] == 3:
                # pose x stack of vectors
                return np.array([base.qvmul(left._A, x) for x in right.T]).T
            else:
                raise ValueError('bad operands')
        else:
            raise ValueError('UnitQuaternion: operands to * are of different types')

    def __imul__(left, right):  # lgtm[py/not-named-self] pylint: disable=no-self-argument
        """
        Multiply unit quaternion in place

        :return: product
        :rtype: UnitQuaternion, Quaternion
        :raises: ValueError

        Multiplies a quaternion in place. If the right operand is a list,
        the result will be a list.

        Example::

            >>> q = UQ.Rx(0.3)
            >>> q *= UQ.Rx(0.3)
            >>> q
            0.955336 << 0.295520, 0.000000, 0.000000 >>

        :seealso: :func:`__mul__`

        """
        return left.__mul__(right)

    def __truediv__(left, right):  # lgtm[py/not-named-self] pylint: disable=no-self-argument
        """
        Overloaded ``/`` operator

        :rtype: Quaternion or UnitQuaternion

        - ``q1 / q2`` is equivalent to ``q1 * q1.inv()``.
        - ``q / s`` performs elementwise division of the elements of ``q`` by 
          ``s``. This is not a group operation so the result will be a 
          Quaternion.

        ==============   ==============   ==============  ===========================
                   Multiplicands                   Quotient
        -------------------------------   -------------------------------------------
            left             right            type           result
        ==============   ==============   ==============  ===========================
        UnitQuaternion   UnitQuaternion   UnitQuaternion  Hamilton product by inverse
        UnitQuaternion   scalar           Quaternion      element-wise division
        ==============   ==============   ==============  ===========================

        Any other input combinations result in a ValueError.

        Example:

        .. runblock:: pycon

            >>> from spatialmath import UnitQuaternion as UQ
            >>> print(UQ.Rx(0.3) / UQ.Rx(0.3))
            >>> print(UQ.Rx(0.3) / 2)

        For pose composition either or both operands may hold more than one value which
        results in the composition holding more than one value according to:

        =========   ==========   ====  =====================================
        len(left)   len(right)   len     operation
        =========   ==========   ====  =====================================
         1          1             1    ``quo = left * right.inv()``
         1          M             M    ``quo[i] = left * right[i].inv()``
         N          1             M    ``quo[i] = left[i] * right.inv()``
         M          M             M    ``quo[i] = left[i] * right[i].inv()``
        =========   ==========   ====  =====================================

        Example:

        .. runblock:: pycon

            >>> from spatialmath import UnitQuaternion as UQ
            >>> print(UQ.Rx(0.3) / UQ.Rx(0.3))
            >>> print(UQ.Rx([0.3, 0.6]) / UQ.Rx(0.3))
            >>> print(UQ.Rx(0.3) / UQ.Rx([0.3, 0.6]))
            >>> print(UQ.Rx([0.3, 0.6]) / UQ.Rx([0.3, 0.6]))

        """
        if isinstance(left, right.__class__):
            return UnitQuaternion(left.binop(right, lambda x, y: base.qqmul(x, base.conj(y))))
        elif base.isscalar(right):
            return Quaternion(left.binop(right, lambda x, y: x / y))
        else:
            raise ValueError('bad operands')

    def __eq__(left, right):  # lgtm[py/not-named-self] pylint: disable=no-self-argument
        """
        Overloaded ``==`` operator

        :rtype: bool

        ``q1 == q2`` is True if ``q1`` is elementwise equal to ``q2`` and accounts for the
        double mapping. Supports broadcasting.

        Example:

        .. runblock:: pycon

            >>> from spatialmath import UnitQuaternion as UQ
            >>> q1 = UQ.Rx(0.3)
            >>> q2 = UQ.Ry(0.3)
            >>> q1 == q1
            >>> q1 == (-q1)
            >>> q1 == q2
            >>> UQ([q1, q2]) == q1
            >>> UQ([q1, q2]) == q2
            >>> UQ([q1, q2]) == UQ([q1, q2])

        :seealso: :func:`__ne__`, :func:`~spatialmath.base.quaternions.isequal`
        """
        return left.binop(right, lambda x, y: base.isequal(x, y, unitq=True), list1=False)

    def __ne__(left, right):  # lgtm[py/not-named-self] pylint: disable=no-self-argument
        """
        Overloaded ``!=`` operator

        :rtype: bool

        ``q1 != q2`` is True if ``q1`` is elementwise not equal to ``q2`` and accounts for the
        double mapping. Supports broadcasting.

        Example:

        .. runblock:: pycon

            >>> from spatialmath import UnitQuaternion as UQ
            >>> q1 = UQ.Rx(0.3)
            >>> q2 = UQ.Ry(0.3)
            >>> q1 != q1
            >>> q1 != (-q1)
            >>> q1 != q2
            >>> UQ([q1, q2]) == q1
            >>> UQ([q1, q2]) == q2
            >>> UQ([q1, q2]) == UQ([q1, q2])

        :seealso: :func:`__eq__`, :func:`~spatialmath.base.quaternions.isequal`
        """
        return left.binop(right, lambda x, y: not base.isequal(x, y, unitq=True), list1=False)

    def __matmul__(left, right):  # lgtm[py/not-named-self] pylint: disable=no-self-argument
        """
        Overloaded @ operator

        :return: product :rtype: UnitQuaternion

        - ``q1 @ q2`` is the Hamilton product of ``q1`` and ``q2``, both unit
          quaternions, followed by explicit normalization.

        - `` q1 @= q2`` as above.

        .. note:: This operator is functionally equivalent to ``*`` but is more
            costly.  It is useful for cases where a pose is incrementally update
            over many cycles.
        """
        return left.__class__(left.binop(right, lambda x, y: base.unit(base.qqmul(x, y))))

    def interp(self, end, s=0, shortest=False):
        """
        Interpolate between two unit quaternions

        :param end: final unit quaternion
        :type end: UnitQuaternion
        :param shortest: Take the shortest path along the great circle
        :param s: interpolation coefficient, range 0 to 1, or number of steps
        :type s: array_like or int
        :return: interpolated unit quaternion
        :rtype: UnitQuaternion instance

        - ``q0.interp(q1, s)`` is a unit quaternion that is interpolated between
          ``q0`` when s=0 and ``q1`` when s=1. Spherical linear interpolation
          (slerp) is used.  If ``s`` is an ndarray(n) then the result will be
          a UnitQuaternion with n values.

        - ``q0.interp(q1, N)`` interpolate between ``q0`` and ``q1`` in ``N``
          steps.

        Example:

        .. runblock:: pycon

            >>> from spatialmath import UnitQuaternion as UQ
            >>> q1 = UQ.Rx(0.3); q2 = UQ.Rz(-0.4)
            >>> print(q1)
            >>> print(q2)
            >>> q1.interp(q2, 0)    # this is q1
            >>> q1.interp(q2, 1,)   # this is q2
            >>> q1.interp(q2, 0.5)  # this is in between
            >>> q = q1.interp(q2, 11)  # in 11 steps
            >>> len(q)
            >>> q[0]                # this is q1
            >>> q[5]                # this is in between

        .. note:: values of ``s`` are silently clipped to the range [0, 1]

        :seealso: :func:`~spatialmath.base.quaternions.slerp`
        """
        # TODO allow self to have len() > 1

        if isinstance(s, int) and s > 1:
            s = np.linspace(0, 1, s)
        else:
            s = base.getvector(s)
            s = np.clip(s, 0, 1)  # enforce valid values

        # 2 quaternion form
        if not isinstance(end, UnitQuaternion):
            raise TypeError('end argument must be a UnitQuaternion')
        q1 = self.vec
        q2 = end.vec
        dot = base.inner(q1, q2)

        # If the dot product is negative, the quaternions
        # have opposite handed-ness and slerp won't take
        # the shorter path. Fix by reversing one quaternion.
        if shortest:
            if dot < 0:
                q1 = - q1
                dot = -dot

        # shouldn't be needed by handle numerical errors: -eps, 1+eps cases
        dot = np.clip(dot, -1, 1)  # Clip within domain of acos()

        theta_0 = math.acos(dot)  # theta_0 = angle between input vectors

        qi = []
        for sk in s:
            theta = theta_0 * sk  # theta = angle between v0 and result

            s1 = float(math.cos(theta) - dot * math.sin(theta) / math.sin(theta_0))
            s2 = math.sin(theta) / math.sin(theta_0)
            out = (q1 * s1) + (q2 * s2)
            qi.append(out)

        return UnitQuaternion(qi)

    def interp1(self, s=0, shortest=False):
        """
        Interpolate a unit quaternions

        :param shortest: Take the shortest path along the great circle
        :param s: interpolation coefficient, range 0 to 1, or number of steps
        :type s: array_like or int
        :return: interpolated unit quaternion
        :rtype: UnitQuaternion instance

        - ``q.interp1(s)`` is a unit quaternion that is interpolated between
          identity when s=0 and ``q`` when s=1. Spherical linear interpolation
          (slerp) is used.  If ``s`` is an ndarray(n) then the result will be
          a UnitQuaternion with n values.

        - ``q.interp1(N)`` interpolate between identity and ``q1`` in ``N``
          steps.

        Example:

        .. runblock:: pycon

            >>> from spatialmath import UnitQuaternion as UQ
            >>> q = UQ.Rx(0.3)
            >>> print(q)
            >>> q.interp1(0)    # this is identity
            >>> q.interp1(1)    # this is q
            >>> q.interp1(0.5)  # this is in between
            >>> qi = q.interp1(q2, 11)  # in 11 steps
            >>> len(qi)
            >>> qi[0]                # this is q1
            >>> qi[5]                # this is in between

        .. note:: values of ``s`` are silently clipped to the range [0, 1]

        :seealso: :func:`~spatialmath.base.quaternions.slerp`
        """
        # TODO allow self to have len() > 1

        if isinstance(s, int) and s > 1:
            s = np.linspace(0, 1, s)
        else:
            s = base.getvector(s)
            s = np.clip(s, 0, 1)  # enforce valid values

        q = self.vec
        dot = q[0]   # s

        # If the dot product is negative, the quaternions
        # have opposite handed-ness and slerp won't take
        # the shorter path. Fix by reversing one quaternion.
        if shortest:
            if dot < 0:
                q = - q
                dot = -dot

        # shouldn't be needed by handle numerical errors: -eps, 1+eps cases
        dot = np.clip(dot, -1, 1)  # Clip within domain of acos()

        theta_0 = math.acos(dot)  # theta_0 = angle between input vectors

        qi = []
        for sk in s:
            theta = theta_0 * sk  # theta = angle between v0 and result

            s1 = float(math.cos(theta) - dot * math.sin(theta) / math.sin(theta_0))
            s2 = math.sin(theta) / math.sin(theta_0)
            out = np.r_[s1, 0, 0, 0] + (q * s2)
            qi.append(out)

        return UnitQuaternion(qi)

    def increment(self, w, normalize=False):
        """
        Quaternion incremental update

        :param w: angular displacement, Euler vector
        :type w: array_like(3)
        :param normalize: normalize the result, defaults to False
        :type normalize: bool, optional

        .. note:: The object state is updated
        """

        # is (v, theta) or None
        vt = base.unitvec_norm(w)

        if vt is None:
            # zero update
            return
    
        ds = math.cos(vt[1] / 2)
        dv = math.sin(vt[1] / 2) * vt[0]

        updated = base.qqmul(self.A, np.r_[ds, dv])
        if normalize:
            updated = base.unit(updated)
        self.data = [updated]

    def rpy(self, unit='rad', order='zyx'):
        """
        Unit quaternion as roll-pitch-yaw angles

        :param order: angle sequence order, default to 'zyx'
        :type order: str
        :param unit: angular units: 'rad' [default], or 'deg'
        :type unit: str
        :return: 3-vector of roll-pitch-yaw angles
        :rtype: ndarray(3)

        ``q.rpy`` is the roll-pitch-yaw angle representation of the 3D rotation.  The angles are
        a 3-vector :math:`(r, p, y)` which correspond to successive rotations about the axes
        specified by ``order``:

            - 'zyx' [default], rotate by yaw about the z-axis, then by pitch about the new y-axis,
              then by roll about the new x-axis.  Convention for a mobile robot with x-axis forward
              and y-axis sideways.
            - 'xyz', rotate by yaw about the x-axis, then by pitch about the new y-axis,
              then by roll about the new z-axis. Convention for a robot gripper with z-axis forward
              and y-axis between the gripper fingers.
            - 'yxz', rotate by yaw about the y-axis, then by pitch about the new x-axis,
              then by roll about the new z-axis. Convention for a camera with z-axis parallel
              to the optic axis and x-axis parallel to the pixel rows.

        If ``len(x)`` is:

        - 1, return an ndarray with shape=(3,)
        - N>1, return ndarray with shape=(N,3)

        Example:

        .. runblock:: pycon
        
            >>> from spatialmath import UnitQuaternion as UQ

            >>> UQ.Rx(0.3).rpy()
            array([ 0.3, -0. ,  0. ])
            >>> UQ.Rz([0.2, 0.3]).rpy()
            array([[ 0. , -0. ,  0.2],
                [ 0. , -0. ,  0.3]])

        :seealso: :func:`~spatialmath.pose3d.SE3.RPY`, ::func:`spatialmath.base.transforms3d.tr2rpy`
        """
        if len(self) == 1:
            return base.tr2rpy(self.R, unit=unit, order=order)
        else:
            return np.array([base.tr2rpy(q.R, unit=unit, order=order) for q in self])

    def eul(self, unit='rad'):
        r"""
        Unit quaternion as Euler angles

        :param unit: angular units: 'rad' [default], or 'deg'
        :type unit: str
        :return: 3-vector of Euler angles
        :rtype: ndarray(3)

        ``q.eul`` is the Euler angle representation of the rotation.  Euler angles are
        a 3-vector :math:`(\phi, \theta, \psi)` which correspond to consecutive
        rotations about the Z, Y, Z axes respectively.

        If ``len(x)`` is:

        - 1, return an ndarray with shape=(3,)
        - N>1, return ndarray with shape=(N,3)

        - ndarray with shape=(3,), if len(R) == 1
        - ndarray with shape=(N,3), if len(R) = N > 1

        Example:

        .. runblock:: pycon
        
            >>> from spatialmath import UnitQuaternion as UQ

            >>> UQ.Rz(0.3).eul()
            array([0. , 0. , 0.3])
            >>> UQ.Ry([0.3, 0.4]).eul()
            array([[0. , 0.3, 0. ],
                [0. , 0.4, 0. ]])

        :seealso: :func:`~spatialmath.pose3d.SE3.Eul`, ::func:`spatialmath.base.transforms3d.tr2eul`
        """
        if len(self) == 1:
            return base.tr2eul(self.R, unit=unit)
        else:
            return np.array([base.tr2eul(q.R, unit=unit) for q in self])

    def angvec(self, unit='rad'):
        r"""
        Unit quaternion as angle and rotation vector

        :param unit: angular units: 'rad' [default], or 'deg'
        :type unit: str
        :param check: check that rotation matrix is valid
        :type check: bool
        :return: :math:`(\theta, {\bf v})`
        :rtype: float, ndarray(3)

        ``q.angvec()`` is a tuple :math:`(\theta, v)` containing the rotation 
        angle and a rotation axis which is equivalent to the rotation of
        the unit quaternion ``q``.

        Example:

        .. runblock:: pycon
        
            >>> from spatialmath import UnitQuaternion as UQ

        >>> UQ.Rz(0.3).angvec()
            (0.3, array([0., 0., 1.]))

        :seealso: :func:`~spatialmath.quaternion.AngVec`, :func:`~spatialmath.quaternion.UnitQuaternion.log`, :func:`~angvec2r`
        """
        return base.tr2angvec(self.R, unit=unit)

    # def log(self):
    #     r"""
    #     Logarithm of unit quaternion

    #     :rtype: Quaternion instance

    #     ``q.log()`` is the logarithm of the unit quaternion ``q``, ie.
        
    #     .. math::
        
    #          0  \langle \frac{\mathb{v}}{\| \mathbf{v} \|} \acos s \rangle

    #     Example:

    #     .. runblock:: pycon

    #         >>> from spatialmath import UnitQuaternion
    #         >>> q = UnitQuaternion.Rx(0.3)
    #         >>> print(q.log())

    #     :reference: `Wikipedia <https://en.wikipedia.org/wiki/Quaternion#Exponential,_logarithm,_and_power_functions>`_

    #     :seealso: :func:`~spatialmath.quaternion.Quaternion.log`, `~spatialmath.quaternion.Quaternion.exp`
    #     """
    #     return Quaternion(s=0, v=math.acos(self.s) * base.unitvec(self.v))

    def angdist(self, other, metric=3):
        r"""
        Angular distance metric between unit quaternions

        :param other: second unit quaternion
        :type other: UnitQuaternion instance
        :param metric: metric, default is 3
        :type metric: int
        :raises TypeError: if other is not a UnitQuaternion
        :return: angle in radians
        :rtype: float

        ``q1.angdist(q2)`` is the geodesic norm, or geodesic distance between two
        unit quaternions.  We can consider it as the angle between two quaternions.

        Several metrics are supported:

        ======   ===============================================================
        Metric   Details
        ======   ===============================================================
        0        :math:`1 - | \q_1 \bullet \q_2 | \in [0, 1]`
        1        :math:`\cos^{-1} | \q_1 \bullet \q_2 | \in [0, \pi/2]`
        2        :math:`\cos^{-1} | \q_1 \bullet \q_2 | \in [0, \pi/2]`
        3        :math:`2 \tan^{-1} \| \q_1 \pm \q_2\| / \|\q_1 \mp \q_2\| \in [0, \pi/2]`
        4        :math:`\cos^{-1} \left( 2 (\q_1 \bullet \q_2)^2 - 1\right) \in [0, 1]`
        ======   ===============================================================

        Metric 3 computes the sum and difference of the quaternions and uses
        the largest value in the denominator.

        Example:

        .. runblock:: pycon

            >>> from spatialmath import UnitQuaternion
            >>> q1 = UnitQuaternion.Rx(0.3)
            >>> q2 = UnitQuaternion.Ry(0.3)
            >>> print(q1.angdist(q1))
            >>> print(q1.angdist(q2))

        .. note::
            - metrics 1, 2, 4 can throw ValueError "math domain error" due to
              numeric errors which push the argument of ``acos()`` marginally
              outside its domain [0, 1].
            - metrics 2 and 3 are equivalent, but 3 is more robust
            - SMTB-MATLAB uses metric 3 for UnitQuaternion.angle()
            - MATLAB's quaternion.dist() uses metric 4
        """
        if not isinstance(other, UnitQuaternion):
            raise TypeError('bad operand')

        def metric3(p, q):
            x =  base.norm(p - q)
            y =  base.norm(p + q)
            if x >= y:
                return 2 * math.atan(y / x)
            else:
                return 2 * math.atan(x / y)

        if metric == 0:
            measure = lambda p, q: 1 - abs(np.dot(p, q))
        elif metric == 1:
            measure =  lambda p, q: math.acos(abs(np.dot(p, q)))
        elif metric == 2:
            measure =  lambda p, q: math.acos(abs(np.dot(p, q)))
        elif metric == 3:
            measure =  metric3
        elif metric == 4:
            measure = lambda p, q: math.acos(2 * np.dot(p, q) ** 2 - 1)

        ad = self.binop(other, measure)
        if len(ad) == 1:
            return ad[0]
        else:
            return ad

    def SO3(self):
        """
        Unit quaternion as SO3 instance

        :return: an SO(3) representation
        :rtype: SO3 instance

        ``q.SO3()`` is an ``SO3`` instance representing the same rotation 
        as the unit quaternion ``q``.

        Example:

        .. runblock:: pycon
        
            >>> from spatialmath import UnitQuaternion as UQ

            >>> UQ.Rz(0.3).SO3()
            SO3(array([[ 0.95533649, -0.29552021,  0.        ],
                    [ 0.29552021,  0.95533649,  0.        ],
                    [ 0.        ,  0.        ,  1.        ]]))
        """
        return SO3(self.R, check=False)

    def SE3(self):
        """
        Unit quaternion as SE3 instance

        :return: an SE(3) representation
        :rtype: SE3 instance

        ``q.SE3()`` is an ``SE3`` instance representing the same rotation 
        as the unit quaternion ``q`` and with zero translation.

        Example:

        .. runblock:: pycon
        
            >>> from spatialmath import UnitQuaternion as UQ

            >>> UQ.Rz(0.3).SE3()
            SE3(array([[ 0.95533649, -0.29552021,  0.        ,  0.        ],
                    [ 0.29552021,  0.95533649,  0.        ,  0.        ],
                    [ 0.        ,  0.        ,  1.        ,  0.        ],
                    [ 0.        ,  0.        ,  0.        ,  1.        ]]))
        """
        return SE3(base.r2t(self.R), check=False)

