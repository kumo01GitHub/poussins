use std::collections::HashMap;

use super::declaration::Declaration;

#[derive(Clone, Default)]
pub struct Environment {
    declarations: HashMap<String, Declaration>,
}

impl Environment {
    /// Create a new empty environment.
    pub fn new() -> Self {
        Self::default()
    }

    pub fn has(&self, name: &str) -> bool {
        self.declarations.contains_key(name)
    }

    pub fn get(&self, name: &str) -> Option<&Declaration> {
        self.declarations.get(name)
    }

    pub fn iter(&self) -> impl Iterator<Item = (&String, &Declaration)> {
        self.declarations.iter()
    }

    /// Insert a declaration into the environment.
    pub fn insert(&mut self, name: String, declaration: Declaration) {
        self.declarations.insert(name, declaration);
    }
}
