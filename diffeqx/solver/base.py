import abc
import functools as ft
import jax
from typing import Tuple, TypeVar

from ..custom_types import Array, PyTree, Scalar
from ..interpolation import AbstractInterpolation


# Abusing slightly to represent PyTrees with the same structure
T = TypeVar('T', bound=PyTree)
T2 = TypeVar('T2', bound=PyTree)


class AbstractSolver(metaclass=abc.ABCMeta):
    recommended_interpolation: AbstractInterpolation

    @abc.abstractmethod
    def init(self, t0: Scalar, y0: Array["state": ...]) -> T:
        pass

    @abc.abstractmethod
    def step(self, t0: Scalar, t1: Scalar, y0: Array["state": ...], solver_state: T) -> Tuple[Array["state": ...], T]:
        pass


@ft.partial(jax.jit, static_argnums=0)
def _splitting_method_step(solvers: list[list[AbstractSolver]], t0: Scalar, t1: Scalar, y0: Array["state": ...], solver_state: list[list[T2]]) -> Tuple[Array["state": ...], list[list[T2]]]:
    y = y0
    new_solver_state = []
    for solver_group in solvers:
        new_group_state = []
        new_solver_state.append(new_group_state)
        y_group = 0
        for solver, solver_state_i in zip(solver_group, solver_state):
            yi, solver_state_i = solver.step(t0, t1, y, solver_state_i)
            y_group = y_group + yi
            new_group_state.append(solver_state_i)
        y = y_group
    return y, new_solver_state



class SplittingMethod(AbstractSolver):
    def __init__(self, *, solvers: list[list[AbstractSolver]], **kwargs):
        assert len(solvers) > 0
        super().__init__(**kwargs)
        self.solvers = solvers
        self.recommended_interpolation = self.solvers[0].recommended_interpolation

    def init(self, t0: Scalar, y0: Array["state": ...]) -> list[list[T2]]:
        return [[solver.init(t0, y0) for solver in solver_group] for solver_group in self.solvers]

    def step(self, t0: Scalar, t1: Scalar, y0: Array["state": ...], solver_state: list[list[T2]]) -> Tuple[Array["state": ...], list[list[T2]]]:
        return _splitting_method_step(self.solvers, t0, t1, solver_state)

