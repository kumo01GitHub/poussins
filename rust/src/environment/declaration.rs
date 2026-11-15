use crate::ast::expr::Expr;

/// A definition declaration in the environment.
#[derive(Clone)]
pub struct DefinitionDecl {
    pub name: String,
    pub ty: Expr,
    pub value: Expr,
    pub level_params: Vec<String>,
    pub mutual_decls: Vec<String>,
    pub is_opaque: bool,
}

/// An axiom declaration in the environment.
#[derive(Clone)]
pub struct AxiomDecl {
    pub name: String,
    pub ty: Expr,
    pub level_params: Vec<String>,
}

/// An inductive type declaration in the environment.
#[derive(Clone)]
pub struct InductiveDecl {
    pub name: String,
    pub ty: Expr,
    pub level_params: Vec<String>,
    pub mutual_decls: Vec<String>,
    pub constructor_names: Vec<String>,
    pub recursor_names: Vec<String>,
}

/// A constructor declaration in the environment.
#[derive(Clone)]
pub struct ConstructorDecl {
    pub name: String,
    pub ty: Expr,
    pub level_params: Vec<String>,
    pub inductive_name: String,
}

/// A computation rule for a recursor applied to a specific constructor.
#[derive(Clone)]
pub struct RecursorRule {
    pub constructor_name: String,
    pub num_fields: usize,
    pub rhs: Expr,
}

/// A recursor declaration in the environment.
#[derive(Clone)]
pub struct RecursorDecl {
    pub name: String,
    pub ty: Expr,
    pub level_params: Vec<String>,
    pub mutual_decls: Vec<String>,
    pub num_params: usize,
    pub num_indices: usize,
    pub num_motives: usize,
    pub num_minors: usize,
    pub rules: Vec<RecursorRule>,
}

/// Represents a declaration in the environment.
#[derive(Clone)]
pub enum Declaration {
    Definition(DefinitionDecl),
    Axiom(AxiomDecl),
    Inductive(InductiveDecl),
    Constructor(ConstructorDecl),
    Recursor(RecursorDecl),
}
