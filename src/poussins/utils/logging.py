"""Utility functions for logging within the Poussins project."""
from __future__ import annotations

import logging
import os
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from typing import Any

from ..ast import (
    EApp,
    EBVar,
    EConst,
    EFVar,
    ELam,
    ELet,
    EMetaVar,
    EPi,
    ESort,
    Expr,
    decompose_app,
)

_APP_ARITY_UNARY = 1
_APP_ARITY_BINARY = 2
_APP_ARITY_TERNARY = 3


@dataclass(frozen=True)
class _ExprRenderOptions:
    nat_literals: bool = False
    nat_ops_infix: bool = False
    and_infix: bool = False
    eq_infix: bool = False
    pi_bound_names: bool = False
    compact_lambdas: bool = False


def _try_read_nat_literal(expr: Expr) -> int | None:
    count = 0
    current = expr
    while isinstance(current, EApp):
        head, args = decompose_app(current)
        if not (
            isinstance(head, EConst)
            and head.name == "Nat.succ"
            and len(args) == _APP_ARITY_UNARY
        ):
            return None
        count += 1
        current = args[0]

    if isinstance(current, EConst) and current.name == "Nat.zero":
        return count
    return None


def _render_expr(
    expr: Expr,
    options: _ExprRenderOptions,
    binders: tuple[str, ...] = (),
) -> str:
    match expr:
        case ESort():
            return str(expr)
        case EFVar(name):
            return name
        case EBVar(index):
            if options.pi_bound_names and index < len(binders):
                return binders[-1 - index]
            return f"#{index}"
        case EConst(name, levels):
            if options.nat_literals and name == "Nat.zero":
                return "0"
            if levels:
                return f"{name}.{{{', '.join(str(level) for level in levels)}}}"
            return name
        case EPi(var, domain, body):
            domain_str = _render_expr(domain, options, binders)
            body_str = _render_expr(body, options, (*binders, var))
            return f"(Π {var} : {domain_str}, {body_str})"
        case ELam(var, domain, body):
            if options.compact_lambdas:
                vars_and_domains: list[tuple[str, Expr]] = [(var, domain)]
                current_body = body
                while isinstance(current_body, ELam):
                    vars_and_domains.append((current_body.var, current_body.domain))
                    current_body = current_body.body

                binders_for_body = binders
                rendered_binders: list[str] = []
                for binder_var, binder_domain in vars_and_domains:
                    domain_str = _render_expr(binder_domain, options, binders_for_body)
                    rendered_binders.append(f"{binder_var} : {domain_str}")
                    binders_for_body = (*binders_for_body, binder_var)

                body_str = _render_expr(current_body, options, binders_for_body)
                return f"(λ {', '.join(rendered_binders)}, {body_str})"

            domain_str = _render_expr(domain, options, binders)
            body_str = _render_expr(body, options, (*binders, var))
            return f"(λ {var} : {domain_str}, {body_str})"
        case ELet(var, type_expr, value, body):
            type_str = _render_expr(type_expr, options, binders)
            value_str = _render_expr(value, options, binders)
            body_str = _render_expr(body, options, (*binders, var))
            return f"(let {var} : {type_str} := {value_str} in {body_str})"
        case EMetaVar(goal_id):
            return f"?{goal_id}"
        case EApp():
            return _render_app_expr(expr, options, binders)


def _render_app_expr(
    expr: EApp,
    options: _ExprRenderOptions,
    binders: tuple[str, ...],
) -> str:
    head, args = decompose_app(expr)
    if isinstance(head, EConst):
        if (
            options.nat_literals
            and head.name == "Nat.succ"
            and len(args) == _APP_ARITY_UNARY
        ):
            nat_literal = _try_read_nat_literal(expr)
            if nat_literal is not None:
                return str(nat_literal)
        if options.nat_ops_infix and len(args) == _APP_ARITY_BINARY:
            nat_op_symbols = {
                "Nat.add": "+",
                "Nat.sub": "-",
                "Nat.mul": "*",
                "Nat.div": "/",
                "Nat.mod": "%",
            }
            symbol = nat_op_symbols.get(head.name)
            if symbol is not None:
                left = _render_expr(args[0], options, binders)
                right = _render_expr(args[1], options, binders)
                return f"({left} {symbol} {right})"
        if options.and_infix and head.name == "And" and len(args) == _APP_ARITY_BINARY:
            left = _render_expr(args[0], options, binders)
            right = _render_expr(args[1], options, binders)
            return f"({left} ∧ {right})"
        if options.eq_infix and head.name == "Eq" and len(args) == _APP_ARITY_TERNARY:
            left = _render_expr(args[1], options, binders)
            right = _render_expr(args[2], options, binders)
            return f"({left} = {right})"

    fn_str = _render_expr(expr.fn, options, binders)
    arg_str = _render_expr(expr.arg, options, binders)
    return f"({fn_str} {arg_str})"


@dataclass(frozen=True)
class _ExprLogValue:
    expr: Expr
    options: _ExprRenderOptions = _ExprRenderOptions()

    def with_options(self, **kwargs: Any) -> _ExprLogValue:
        return _ExprLogValue(expr=self.expr, options=replace(self.options, **kwargs))

    def __str__(self) -> str:
        return _render_expr(self.expr, self.options)

    def __repr__(self) -> str:
        return str(self)


def _transform_log_value(
    value: Any,
    update: Callable[[_ExprLogValue], _ExprLogValue],
) -> Any:
    if isinstance(value, Expr):
        return update(_ExprLogValue(value))
    if isinstance(value, _ExprLogValue):
        return update(value)
    if isinstance(value, tuple):
        return tuple(_transform_log_value(v, update) for v in value)
    if isinstance(value, list):
        return [_transform_log_value(v, update) for v in value]
    if isinstance(value, dict):
        return {k: _transform_log_value(v, update) for k, v in value.items()}
    return value


class _ExprLogFilter(logging.Filter):
    def update_expr_options(self, value: _ExprLogValue) -> _ExprLogValue:
        return value

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _transform_log_value(record.msg, self.update_expr_options)
        if isinstance(record.args, tuple):
            record.args = tuple(
                _transform_log_value(arg, self.update_expr_options)
                for arg in record.args
            )
        elif isinstance(record.args, dict):
            record.args = {
                key: _transform_log_value(arg, self.update_expr_options)
                for key, arg in record.args.items()
            }
        return True


class NatExprLogFilter(_ExprLogFilter):
    """Enable Nat literal formatting for expression log values."""

    def update_expr_options(self, value: _ExprLogValue) -> _ExprLogValue:
        """Enable Nat literal rendering on target values."""
        return value.with_options(nat_literals=True, nat_ops_infix=True)


class AndExprLogFilter(_ExprLogFilter):
    """Enable `And` infix formatting for expression log values."""

    def update_expr_options(self, value: _ExprLogValue) -> _ExprLogValue:
        """Enable And infix rendering on target values."""
        return value.with_options(and_infix=True)


class EqExprLogFilter(_ExprLogFilter):
    """Enable `Eq` infix formatting for expression log values."""

    def update_expr_options(self, value: _ExprLogValue) -> _ExprLogValue:
        """Enable Eq infix rendering on target values."""
        return value.with_options(eq_infix=True)


class PiBoundNameExprLogFilter(_ExprLogFilter):
    """Enable de Bruijn-to-name formatting for binder-scoped variables."""

    def update_expr_options(self, value: _ExprLogValue) -> _ExprLogValue:
        """Enable binder-name rendering on target values."""
        return value.with_options(pi_bound_names=True, compact_lambdas=True)


DEFAULT_EXPR_LOG_FILTERS: tuple[type[logging.Filter], ...] = (
    NatExprLogFilter,
    AndExprLogFilter,
    EqExprLogFilter,
    PiBoundNameExprLogFilter,
)


def get_logger(
    name: str,
    filters: Sequence[logging.Filter] | None = None,
) -> logging.Logger:
    """Get a logger."""
    logger = logging.getLogger(name)
    level = getattr(
        logging,
        os.getenv("POUSSINS_LOG_LEVEL", "INFO").upper(),
        logging.INFO
    )

    if not logger.handlers:
        # Configure the logger only if it hasn't been configured yet
        logger.setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    else:
        logger.setLevel(level)

    effective_filters = (
        tuple(filter_class() for filter_class in DEFAULT_EXPR_LOG_FILTERS)
        if filters is None else tuple(filters)
    )
    for filter_ in effective_filters:
        if not any(type(registered) is type(filter_) for registered in logger.filters):
            logger.addFilter(filter_)

    return logger
