import poussins


def test_root_package_exports_proof_author_api_only() -> None:
    assert hasattr(poussins, "Environment")
    assert hasattr(poussins, "Prop")
    assert hasattr(poussins, "Nat")
    assert hasattr(poussins, "Bool")
    assert hasattr(poussins, "Example")
    assert hasattr(poussins, "Theorem")
    assert hasattr(poussins, "Lemma")

    assert not hasattr(poussins, "EConst")
    assert not hasattr(poussins, "ELam")
    assert not hasattr(poussins, "ProofManager")
    assert not hasattr(poussins, "ProofEngine")
    assert not hasattr(poussins, "InductiveType")
    assert not hasattr(poussins, "ProofScript")
    assert not hasattr(poussins, "apply")


def test_extension_apis_are_available_from_subpackages() -> None:
    from poussins.environment import InductiveDeclaration
    from poussins.framework import InductiveType, ProofScript
    from poussins.kernel import ProofManager
    from poussins.tactics import apply

    assert InductiveDeclaration is not None
    assert InductiveType is not None
    assert ProofScript is not None
    assert ProofManager is not None
    assert apply is not None